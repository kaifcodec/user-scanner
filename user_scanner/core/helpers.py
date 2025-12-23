def get_site_name(module) -> str:
    name = module.__name__.split('.')[-1].capitalize().replace("_", ".")
    if name == "X":
        return "X (Twitter)"
    return name


def is_last_value(values, i: int) -> bool:
    return i == len(values) - 1
