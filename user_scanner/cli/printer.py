from colorama import Fore, Style
from typing import Literal
from user_scanner.core.result import Result, Status

INDENT = "  "

JSON_TEMPLATE = """{{
\t"site_name": "{site_name}",
\t"username": "{username}",
\t"result": "{result}"
}}""".replace("\t", INDENT)

JSON_TEMPLATE_ERROR = """{{
\t"site_name": "{site_name}",
\t"username": "{username}",
\t"result": "Error",
\t"reason": "{reason}"
}}""".replace("\t", INDENT)


CSV_HEADER = "site_name,username,result,reason"
CSV_TEMPLATE = "{site_name},{username},{result},{reason}"


def indentate(msg: str, indent: int):
    if indent <= 0:
        return msg
    tabs = INDENT * indent
    return "\n".join([f"{tabs}{line}" for line in msg.split("\n")])


class Printer:
    def __init__(self, output_format: Literal["console", "csv", "json"]) -> None:
        if not output_format in ["console", "csv", "json"]:
            raise ValueError(f"Invalid output-format: {output_format}")
        self.mode: str = output_format
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

    def print_start(self, json_char: str = "[") -> None:
        if self.is_json:
            self.indent += 1
            print(indentate(json_char, self.indent - 1))
        elif self.is_csv:
            print(CSV_HEADER)

    def print_end(self, json_char: str = "]") -> None:
        if not self.is_json:
            return
        self.indent = max(self.indent - 1, 0)
        print(indentate(json_char, self.indent))

    def get_result_output(self, site_name: str, username: str, result: Result) -> str:
        if result == None:
            result = Result.error("Invalid return value: None")

        if isinstance(result, int):
            result = Result.from_number(result)

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

            case (Status.AVAILABLE, "json") | (Status.TAKEN, "json"):
                return indentate(JSON_TEMPLATE, self.indent).format(
                    site_name=site_name,
                    username=username,
                    result=str(result.status)
                )

            case (Status.ERROR, "json"):
                return indentate(JSON_TEMPLATE_ERROR, self.indent).format(
                    site_name=site_name,
                    username=username,
                    reason=result.get_reason()
                )

            case (_, "csv"):
                return CSV_TEMPLATE.format(
                    site_name=site_name,
                    username=username,
                    result=str(result.status),
                    reason=result.get_reason()
                )

        return ""

    def print_modules(self, category: str | None = None):
        from user_scanner.core.orchestrator import load_categories, load_modules
        categories = load_categories()
        categories_to_list = [category] if category else categories.keys()

        # Print the start
        if self.is_json:
            self.print_start("{")
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
                    self.print_start(f"\"{cat_name}\": [")

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
                self.print_end("]" if is_last else "],")

        if self.is_json:
            self.print_end("}")
