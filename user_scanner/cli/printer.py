from colorama import Fore, Style
from typing import Literal
from user_scanner.core.result import Result, Status

JSON_TEMPLATE = """{{
\t"site_name": "{site_name}",
\t"username": "{username}",
\t"result": "{result}"
}}"""

JSON_TEMPLATE_ERROR = """{{
\t"site_name": "{site_name}",
\t"username": "{username}",
\t"result": "Error",
\t"reason": "{reason}"
}}"""


def identate(msg: str, ident: int):
    tabs = "\t" * ident
    return "\n".join([f"{tabs}{line}" for line in msg.split("\n")])


class Printer:
    def __init__(self, output_format: Literal["console", "csv", "json"]) -> None:
        if not output_format in ["console", "csv", "json"]:
            raise ValueError(f"Invalid output-format: {output_format}")
        self.mode: str = output_format
        self.ident: int = 0

    @property
    def is_console(self) -> bool:
        return self.mode == "console"

    @property
    def is_csv(self) -> bool:
        return self.mode == "csv"

    @property
    def is_json(self) -> bool:
        return self.mode == "json"

    def print_json_start(self) -> None:
        if not self.is_json:
            return
        self.ident += 1
        print(identate("[", self.ident - 1))

    def print_json_end(self) -> None:
        if not self.is_json:
            return
        self.ident = max(self.ident - 1, 0)
        print(identate("]", self.ident))

    def get_result_output(self, site_name: str, username: str, result: Result) -> str:
        if result == None:
            result = Result.error("Invalid return value: None")

        if isinstance(result, int):
            result = Result.from_number(result)

        match (result.status, self.mode):
            case (Status.AVAILABLE, "console"):
                return f"  {Fore.GREEN}[✔] {site_name} ({username}): Available{Style.RESET_ALL}"

            case (Status.TAKEN, "console"):
                return f"  {Fore.RED}[✘] {site_name} ({username}): Taken{Style.RESET_ALL}"

            case (Status.ERROR, "console"):
                reason = ""
                if isinstance(result, Result) and result.has_reason():
                    reason = f" ({result.get_reason()})"
                return f"  {Fore.YELLOW}[!] {site_name} ({username}): Error{reason}{Style.RESET_ALL}"

            case (Status.AVAILABLE, "json") | (Status.TAKEN, "json"):
                msg = identate(JSON_TEMPLATE, self.ident).format(
                    site_name=site_name,
                    username=username,
                    result=str(result.status)
                )
                return msg

            case (Status.ERROR, "json"):
                msg = identate(JSON_TEMPLATE_ERROR, self.ident).format(
                    site_name=site_name,
                    username=username,
                    reason=result.get_reason()
                )
                return msg

