"""UI routes for rendering modular templates."""
import functools
import os
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from user_scanner.core.helpers import load_categories, load_modules
from user_scanner.core.version import load_local_version

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@functools.lru_cache(maxsize=1)
def get_catalog_stats():
    """Dynamically counts modules and calculates rounded baseline display figures."""
    user_cats = load_categories(is_email=False)
    email_cats = load_categories(is_email=True)
    u_count = sum(len(load_modules(p)) for p in user_cats.values())
    e_count = sum(len(load_modules(p)) for p in email_cats.values())
    u_floor = (u_count // 5) * 5
    e_floor = (e_count // 5) * 5
    total_floor = u_floor + e_floor
    return {
        "user_raw": u_count,
        "email_raw": e_count,
        "user_rounded": f"{u_floor}+",
        "email_rounded": f"{e_floor}+",
        "total_rounded": f"{total_floor}+",
        "user_base": u_floor,
        "email_base": e_floor,
        "total_base": total_floor,
    }


async def index_view(request: Request) -> HTMLResponse:
    target = request.query_params.get("u") or request.query_params.get("username") or ""
    email = request.query_params.get("e") or request.query_params.get("email") or ""
    category = request.query_params.get("c") or request.query_params.get("category") or "ALL"
    version_str, _ = load_local_version()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "prefill_target": target or email,
            "prefill_type": "email" if email else "username",
            "prefill_category": category.upper(),
            "version": version_str,
            "stats": get_catalog_stats(),
        }
    )
