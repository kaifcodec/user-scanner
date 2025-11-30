import importlib
import pkgutil
from colorama import Fore, Style
import threading

import httpx
from httpx import ConnectError, TimeoutException

lock = threading.Condition()
#Basically which thread is the one to print
print_queue = 0

def load_modules(package):

    modules = []
    for _, name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(name)
            modules.append(module)
        except Exception as e:
            print(f"Failed to import {name}: {e}")
    return modules

def worker_single(module, username, i):
    global print_queue

    func = next((getattr(module, f) for f in dir(module)
                 if f.startswith("validate_") and callable(getattr(module, f))), None)
    site_name = module.__name__.split('.')[-1].capitalize().replace("_",".")
    if site_name == "X":
        site_name = "X (Twitter)"

    output = ""
    if func:
        try:
            result = func(username)
            if result == 1:
                output = f"  {Fore.GREEN}[✔] {site_name}: Available{Style.RESET_ALL}"
            elif result == 0:
                output = f"  {Fore.RED}[✘] {site_name}: Taken{Style.RESET_ALL}"
            else:
                output = f"  {Fore.YELLOW}[!] {site_name}: Error{Style.RESET_ALL}"
        except Exception as e:
            output = f"  {Fore.YELLOW}[!] {site_name}: Exception - {e}{Style.RESET_ALL}"
    else:
        output = f"  {Fore.YELLOW}[!] {site_name} has no validate_ function{Style.RESET_ALL}"

    with lock:
        #Waits for in-order printing
        while i != print_queue:
            lock.wait()

        print(output)
        print_queue += 1
        lock.notify_all()

def run_module_single(module, username):
    #Just executes as if it was a thread
    worker_single(module, username, print_queue)
    
def run_checks_category(package, username, verbose=False):
    global print_queue
    
    modules = load_modules(package)
    category_name = package.__name__.split('.')[-1].capitalize()
    print(f"{Fore.MAGENTA}== {category_name} SITES =={Style.RESET_ALL}")

    print_queue = 0

    threads = []
    for i, module in enumerate(modules):
        t = threading.Thread(target=worker_single, args=(module, username, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

def run_checks(username):
    from user_scanner import dev, social, creator, community, gaming, donation

    packages = [dev, social, creator, community, gaming, donation]

    print(f"\n{Fore.CYAN} Checking username: {username}{Style.RESET_ALL}\n")

    for package in packages:
        run_checks_category(package, username)
        print()

def make_get_request(url, **kwargs):
    """Simple wrapper to **httpx.get** that predefines headers and timeout"""
    if not "headers" in kwargs:
        kwargs["headers"] = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "en-US,en;q=0.9",
            'sec-fetch-dest': "document",
        }

    if not "timeout" in kwargs:
        kwargs["timeout"] = 5.0

    return httpx.get(url, **kwargs)

def generic_validate(url, func, **kwargs):
    """
    A generic validate function that makes a request and executes the provided function on the response.
    """
    try:
        response = make_get_request(url, **kwargs)
        return func(response)
    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2
    
def status_validate(url, available, taken, **kwargs):
    """
    Function that takes a **url** and **kwargs** for the request and 
    checks if the request status matches the availabe or taken.
    **Available** and **Taken** must either be whole numbers or lists of whole numbers.
    """
    def inner(response):
        #Checks if a number is equal or is contained inside
        contains = lambda a,b: (isinstance(a,list) and b in a) or (a == b)

        status = response.status_code
        available_value = contains(available, status)
        taken_value = contains(taken, status)

        if available_value and taken_value:
            return 2 # Can't be both available and taken
        elif available_value:
            return 1
        elif taken_value:
            return 0
        return 2

    return generic_validate(url, inner, **kwargs)
