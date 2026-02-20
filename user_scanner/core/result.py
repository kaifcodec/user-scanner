from enum import Enum
from colorama import Fore, Style

# Added {url} to the debug message
DEBUG_MSG = """Result {{
  status: {status},
  reason: "{reason}",
  username: "{username}",
  site_name: "{site_name}",
  category: "{category}",
  url: "{url}",
  is_email: "{is_email}"
}}"""

# Added "url": "{url}" to the JSON template
JSON_TEMPLATE = """{{
\t"username": "{username}",
\t"category": "{category}",
\t"site_name": "{site_name}",
\t"status": "{status}",
\t"url": "{url}",
\t"reason": "{reason}"
}}"""

# Added {url} to the CSV template
CSV_TEMPLATE = "{username},{category},{site_name},{status},{url},{reason}"


def humanize_exception(e: Exception) -> str:
    msg = str(e).lower()
    if "10054" in msg:
        return "Connection closed by remote server"
    if "11001" in msg:
        return "Could not resolve hostname"
    return str(e)


class Status(Enum):
    TAKEN = 0
    AVAILABLE = 1
    ERROR = 2

    def to_label(self, is_email=False):
        if self == Status.ERROR:
            return "Error"
        if is_email:
            return "Registered" if self == Status.TAKEN else "Not Registered"
        return "Taken" if self == Status.TAKEN else "Available"

    def __str__(self):
        return self.to_label(is_email=False)


class Result:
    def __init__(self, status: Status, reason: str | Exception | None = None, **kwargs):
        self.status = status
        self.reason = reason
        self.username = None
        self.site_name = None
        self.category = None
        self.url = ""  # Initialized url field
        self.is_email = False
        self.update(**kwargs)

    def update(self, **kwargs):
        # Added "url" to the list of fields allowed for dynamic updates
        for field in ("username", "site_name", "category", "is_email", "url"):
            if field in kwargs and kwargs[field] is not None:
                setattr(self, field, kwargs[field])
        return self

    @classmethod
    def taken(cls, reason: str | Exception | None = None, **kwargs):
        return cls(Status.TAKEN, reason, **kwargs)

    @classmethod
    def available(cls, reason: str | Exception | None = None, **kwargs):
        return cls(Status.AVAILABLE, reason, **kwargs)

    @classmethod
    def error(cls, reason: str | Exception | None = None, **kwargs):
        return cls(Status.ERROR, reason, **kwargs)

    @classmethod
    def from_number(cls, i: int, reason: str | Exception | None = None):
        try:
            status = Status(i)
        except ValueError:
            return cls(Status.ERROR, "Invalid status. Please contact maintainers.")
        return cls(status, reason)

    def to_number(self) -> int:
        return self.status.value

    def has_reason(self) -> bool:
        return self.reason is not None

    def get_reason(self) -> str:
        if self.reason is None:
            return ""
        if isinstance(self.reason, str):
            return self.reason
        msg = humanize_exception(self.reason)
        return f"{type(self.reason).__name__}: {msg.capitalize()}"

    def as_dict(self) -> dict:
        return {
            "status": self.status.to_label(self.is_email),
            "reason": self.get_reason(),
            "username": self.username,
            "site_name": self.site_name,
            "category": self.category,
            "url": self.url, # Added url to dictionary output
            "is_email": self.is_email,
        }

    def debug(self) -> str:
        return DEBUG_MSG.format(**self.as_dict())

    def to_json(self) -> str:
        msg = JSON_TEMPLATE.format(**self.as_dict())
        if self.is_email:
            msg = msg.replace('\t"username":', '\t"email":')
        return msg

    def to_csv(self) -> str:
        return CSV_TEMPLATE.format(**self.as_dict())

    def __str__(self):
        return self.get_reason()

    def __eq__(self, other):
        if isinstance(other, Status):
            return self.status == other
        if isinstance(other, Result):
            return self.status == other.status
        if isinstance(other, int):
            return self.to_number() == other
        return NotImplemented

    def get_output_color(self) -> str:
        if self == Status.ERROR:
            return Fore.YELLOW
        elif self.is_email:
            return Fore.GREEN if self == Status.TAKEN else Fore.RED
        else:
            return Fore.GREEN if self == Status.AVAILABLE else Fore.RED

    def get_output_icon(self) -> str:
        if self == Status.ERROR:
            return "[!]"
        elif self.is_email:
            return "[✔]" if self == Status.TAKEN else "[✘]"
        else:
            return "[✔]" if self == Status.AVAILABLE else "[✘]"

    def get_console_output(self, show_url=False) -> str:
        site_name = self.site_name
        status_text = self.status.to_label(self.is_email)
        username = ""
        if self.username:
            username = f"({self.username})"
        
        # Added logic to include URL in console output if show_url is True
        url_display = f" [{self.url}]" if show_url and self.url else ""

        color = self.get_output_color()
        icon = self.get_output_icon()

        reason = f" ({self.get_reason()})" if self.has_reason() else ""
        return f"  {color}{icon} {site_name}{url_display} {username}: {status_text}{reason}{Style.RESET_ALL}"

    def show(self, show_url=False):
        """Prints the console output and returns itself for chaining"""
        # Updated show() to accept and pass the show_url flag
        print(self.get_console_output(show_url=show_url))
        return self
