from user_scanner.core.result import Result
from user_scanner.user_scan.shopping.yaga_ee import _validate_yaga


def validate_yaga_co_za(user: str) -> Result:
    return _validate_yaga(user, "https://www.yaga.co.za")
