from user_scanner.core.result import Result, Status


def test_status():
    assert str(Status.AVAILABLE) == "Available"
    assert str(Status.TAKEN) == "Taken"
    assert str(Status.ERROR) == "Error"


def test_equality():
    taken = Result.taken()
    assert taken == taken
    assert taken == Result.taken()
    assert taken == Status.TAKEN
    assert taken == 0
    assert taken.__eq__("str") == NotImplemented

    available = Result.available()
    assert available == available
    assert available == Result.available()
    assert available == Status.AVAILABLE
    assert available == 1
    assert available.__eq__("str") == NotImplemented

    error = Result.error()
    assert error == error
    assert error == Result.error()
    assert error == Status.ERROR
    assert error == 2
    assert error.__eq__("str") == NotImplemented


def test_get_reason():
    assert Result.available().get_reason() == ""
    assert Result.available("reason").get_reason() == "reason"
    assert Result.available(Exception("reason")).get_reason() == "Exception: Reason"

    assert Result.taken().get_reason() == ""
    assert Result.taken("reason").get_reason() == "reason"
    assert Result.taken(Exception("reason")).get_reason() == "Exception: Reason"

    assert Result.error().get_reason() == ""
    assert Result.error("reason").get_reason() == "reason"
    assert Result.error(Exception("reason")).get_reason() == "Exception: Reason"


def test_has_reason():
    assert not Result.available().has_reason()
    assert Result.available("Has reason").has_reason()

    assert not Result.taken().has_reason()
    assert Result.taken("Has reason").has_reason()

    assert not Result.error().has_reason()
    assert Result.error("Has reason").has_reason()


def test_to_number():
    assert Result.error().to_number() == 2
    assert Result.available().to_number() == 1
    assert Result.taken().to_number() == 0


def test_from_number():
    assert Result.from_number(0) == Status.TAKEN
    assert Result.from_number(1) == Status.AVAILABLE
    assert Result.from_number(2) == Status.ERROR
    for i in [-2, -1, 3, 4, 5, 6, 7, 8, 9, 10]:
        assert Result.from_number(i) == Status.ERROR


def test_number():
    a = Result.available()
    assert Result.from_number(a.to_number()) == a
    b = Result.taken()
    assert Result.from_number(b.to_number()) == b
    c = Result.error()
    assert Result.from_number(c.to_number()) == c


def test_update():
    a = Result.available()
    attrs = ("username", "site_name", "category")
    for attr in attrs:
        assert getattr(a, attr) is None

    a.update(username="name")
    assert getattr(a, "username") == "name"
    a.update(username="username", site_name="site_name", category="category")
    for attr in attrs:
        assert getattr(a, attr) == attr
