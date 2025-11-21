import importlib
import pkgutil
from colorama import Fore, Style
import threading

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
    site_name = module.__name__.split('.')[-1].capitalize()
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
    from user_scanner import dev, social, creator, community, gaming

    categories = [
        ("DEV", dev),
        ("SOCIAL", social),
        ("CREATOR", creator),
        ("COMMUNITY", community),
        ("GAMING", gaming)
    ]

    print(f"\n{Fore.CYAN} Checking username: {username}{Style.RESET_ALL}\n")

    for _, package in categories:
        run_checks_category(package, username)
        print()
