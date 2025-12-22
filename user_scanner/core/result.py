from enum import Enum

DEBUG_MSG = """Result {{
  status: {status},
  reason: "{reason}",
  username: "{username}",
  site_name: "{site_name}",
  category: "{category}",
}}"""

JSON_TEMPLATE = """{{
\t"username": "{username}",
\t"category": "{category}",
\t"site_name": "{site_name}",
\t"status": "{status}",
\t"reason": "{reason}"
}}"""

CSV_TEMPLATE = "{username},{category},{site_name},{status},{reason}"


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

    def __str__(self):
        return super().__str__().split(".")[1].capitalize()


class Result:
    def __init__(self, status: Status, reason: str | Exception | None = None, **kwargs):
        self.status = status
        self.reason = reason

        self.username = None
        self.site_name = None
        self.category = None
        self.update(**kwargs)

    def update(self, **kwargs):
        for field in ("username", "site_name", "category"):
            if field in kwargs and kwargs[field] is not None:
                setattr(self, field, kwargs[field])

    @classmethod
    def taken(cls, **kwargs):
        return cls(Status.TAKEN, **kwargs)

    @classmethod
    def available(cls, **kwargs):
        return cls(Status.AVAILABLE, **kwargs)

    @classmethod
    def error(cls, reason: str | Exception | None = None, **kwargs):
        return cls(Status.ERROR, reason, **kwargs)

    @classmethod
    def from_number(cls, i: int, reason: str | Exception | None = None):
        try:
            status = Status(i)
        except ValueError:
            return cls(Status.ERROR, "Invalid status. Please contact maintainers.")

        return cls(status,  reason if status == Status.ERROR else None)

    def to_number(self) -> int:
        return self.status.value

    def has_reason(self) -> bool:
        return self.reason is not None

    def get_reason(self) -> str:
        if self.reason is None:
            return ""
        if isinstance(self.reason, str):
            return self.reason
        # Format the exception
        msg = humanize_exception(self.reason)
        return f"{type(self.reason).__name__}: {msg.capitalize()}"

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "reason": self.get_reason(),
            "username": self.username,
            "site_name": self.site_name,
            "category": self.category
        }

    def debug(self) -> str:
        return DEBUG_MSG.format(**self.as_dict())

    def to_json(self) -> str:
        return JSON_TEMPLATE.format(**self.as_dict())

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

