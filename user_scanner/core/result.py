from enum import Enum
from typing import Literal


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


class Result:
    def __init__(self, status: Status, reason: str | Exception | None = None):
        self.status = status
        self.reason = reason

    @classmethod
    def taken(cls):
        return cls(Status.TAKEN)

    @classmethod
    def available(cls):
        return cls(Status.AVAILABLE)

    @classmethod
    def error(cls, reason: str | Exception | None = None):
        return cls(Status.ERROR, reason)

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
        return self.reason != None

    def get_reason(self) -> str:
        if self.reason == None:
            return ""
        if isinstance(self.reason, str):
            return self.reason
        #Format the exception
        msg = humanize_exception(self.reason)
        return f"{type(self.reason).__name__}: {msg.capitalize()}"

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


AnyResult = Literal[0, 1, 2] | Result
