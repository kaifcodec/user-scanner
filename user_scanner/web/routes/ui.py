"""UI routes for rendering modular templates."""
import os
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

async def index_view(request: Request) -> HTMLResponse:
    target = request.query_params.get("u") or request.query_params.get("username") or ""
    email = request.query_params.get("e") or request.query_params.get("email") or ""
    category = request.query_params.get("c") or request.query_params.get("category") or "ALL"
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "prefill_target": target or email,
            "prefill_type": "email" if email else "username",
            "prefill_category": category.upper(),
            "version": "1.5.1.2"
        }
    )
