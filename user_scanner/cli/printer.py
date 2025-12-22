from colorama import Fore, Style
from typing import Literal
from user_scanner.core.result import Result, Status

INDENT = "  "
CSV_HEADER = "username,category,site_name,status,url,reason"


def indentate(msg: str, indent: int):
    if indent <= 0:
        return msg
    tabs = INDENT * indent
    return "\n".join([f"{tabs}{line}" for line in msg.split("\n")])


class Printer:
    def __init__(self, format: Literal["console", "csv", "json"]) -> None:
        if format not in ["console", "csv", "json"]:
            raise ValueError(f"Invalid output-format: {format}")
        self.mode: str = format
        self.indent: int = 0

    @property
    def is_console(self) -> bool:
        return self.mode == "console"

    @property
    def is_csv(self) -> bool:
        return self.mode == "csv"

    @property
    def is_json(self) -> bool:
        return self.mode == "json"

    def get_start(self, json_char: str = "[") -> str:
        if self.is_json:
            self.indent += 1
            return indentate(json_char, self.indent - 1)
        elif self.is_csv:
            return CSV_HEADER
        return ""

    def get_end(self, json_char: str = "]") -> str:
        if not self.is_json:
            return ""
        self.indent = max(self.indent - 1, 0)
        return indentate(json_char, self.indent)

    def get_result_output(self, result: Result) -> str:
        #In principle result should always have this
        site_name = result.site_name
        username = result.username

        match (result.status, self.mode):
            case (Status.AVAILABLE, "console"):
                return f"{INDENT}{Fore.GREEN}[✔] {site_name} ({username}): Available{Style.RESET_ALL}"

            case (Status.TAKEN, "console"):
                return f"{INDENT}{Fore.RED}[✘] {site_name} ({username}): Taken{Style.RESET_ALL}"

            case (Status.ERROR, "console"):
                reason = ""
                if isinstance(result, Result) and result.has_reason():
                    reason = f" ({result.get_reason()})"
                return f"{INDENT}{Fore.YELLOW}[!] {site_name} ({username}): Error{reason}{Style.RESET_ALL}"

            case (_, "json"):
                return indentate(result.to_json().replace("\t", INDENT), self.indent)

            case (_, "csv"):
                return result.to_csv()

        return ""

    def print_modules(self, category: str | None = None):
        from user_scanner.core.orchestrator import load_categories, load_modules
        categories = load_categories()
        categories_to_list = [category] if category else categories.keys()

        # Print the start
        if self.is_json:
            print(self.get_start("{"))
        elif self.is_csv:
            print("category,site_name")

        for i, cat_name in enumerate(categories_to_list):
            path = categories[cat_name]
            modules = load_modules(path)

            # Print for each category
            match self.mode:
                case "console":
                    print(Fore.MAGENTA +
                          f"\n== {cat_name.upper()} SITES =={Style.RESET_ALL}")
                case "json":
                    print(self.get_start(f"\"{cat_name}\": ["))

            for j, module in enumerate(modules):
                is_last = j == len(modules) - 1
                site_name = module.__name__.split(".")[-1].capitalize()

                # Print for each site name
                match self.mode:
                    case "console":
                        print(f"{INDENT}- {site_name}")
                    case "json":
                        msg = f"\"{site_name}\"" + ("" if is_last else ",")
                        print(indentate(msg, self.indent))
                    case "csv":
                        print(f"{cat_name},{site_name}")

            if self.is_json:
                is_last = i == len(categories_to_list) - 1
                print(self.get_end("]" if is_last else "],"))

        if self.is_json:
            print(self.get_end("}"))
