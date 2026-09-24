"""
API routes for user-scanner web workbench:
- Case management & persistent storage (/api/cases)
- Modules and categories catalog (/api/modules)
- Proxy live validation (/api/proxies/validate)
- Hudson Rock infostealer check (/api/hudson/check)
- Real-time SSE streaming scan (/api/scan/stream) with bulk, cross-scan, OPSEC controls
- Multi-format exports matching user-scanner CLI: PDF, CSV, JSON (/api/export/...)
"""

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from itertools import islice
from typing import Any, Dict, List

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from user_scanner.core.helpers import (
    ScanConfig,
    load_categories,
    load_modules,
    get_site_name,
    find_module,
    find_category,
    is_loud,
    is_valid_email,
    set_proxy_manager,
    set_global_timeout,
    _validate_proxies_batch,
)
from user_scanner.core.orchestrator import _async_worker as _user_async_worker
from user_scanner.core.email_orchestrator import _async_worker as _email_async_worker
from user_scanner.core.patterns import expand_patterns_random
from user_scanner.core.pivots import (
    extract_pivots,
    select_pivots,
    extract_email_pivots,
    select_email_pivots,
    rank_usernames
)
from user_scanner.core.result import Status, Result
from user_scanner.core import formatter
from user_scanner.core.version import load_local_version

from user_scanner.web.session import (
    get_scan_session,
    save_scan_session,
    delete_scan_session,
    get_all_scan_sessions,
)

logger = logging.getLogger("user_scanner.web")

CATEGORY_COLORS = {
    "DEV": "#10B981",
    "SOCIAL": "#06B6D4",
    "GAMING": "#A855F7",
    "FINANCE": "#F59E0B",
    "COMMUNITY": "#3B82F6",
    "CREATIVE": "#EC4899",
    "CREATOR": "#10B981",
    "CRM": "#6366F1",
    "DATING": "#F43F5E",
    "DONATION": "#F59E0B",
    "EMAIL": "#EC4899",
    "ENTERTAINMENT": "#A855F7",
    "FITNESS": "#10B981",
    "HOSTING": "#3B82F6",
    "JOBS": "#06B6D4",
    "LEARNING": "#06B6D4",
    "MUSIC": "#EC4899",
    "NEWS": "#3B82F6",
    "POLITICAL": "#F59E0B",
    "SHOPPING": "#F59E0B",
    "SPORTS": "#10B981",
    "TRAVEL": "#06B6D4",
    "WOMEN_HEALTH": "#EC4899",
    "ADULT": "#E11D48",
    "OTHER": "#64748B",
    "GENERAL": "#64748B",
}


async def list_cases_view(request: Request) -> JSONResponse:
    """Returns list of saved scan sessions with optional date filtering."""
    timeline_from = request.query_params.get("timeline_from")
    timeline_to = request.query_params.get("timeline_to")

    sessions = get_all_scan_sessions()
    cases_list = []
    for cid, cdata in sessions.items():
        cases_list.append({
            "case_id": cid,
            "title": cdata.get("title", f"Scan: @{cdata.get('target', cid)}"),
            "category": cdata.get("category", "Live OSINT Scan"),
            "target": cdata.get("target") or cdata.get("threat_actor", cid),
            "threat_actor": cdata.get("threat_actor") or cdata.get("target", cid),
            "total_hits": cdata.get("total_hits", 0),
            "total_modules": cdata.get("total_modules", 0),
            "last_scan_date": cdata.get("last_scan_date", datetime.now(timezone.utc).isoformat()),
            "source": cdata.get("source", "Live OSINT Scan"),
            "description": cdata.get("description", "Dynamic scan session artifact.")
        })

    if timeline_from or timeline_to:
        filtered = []
        for c in cases_list:
            date_str = (c.get("last_scan_date") or "")[:10]
            if not date_str:
                filtered.append(c)
                continue
            if timeline_from and date_str < timeline_from:
                continue
            if timeline_to and date_str > timeline_to:
                continue
            filtered.append(c)
        cases_list = filtered

    return JSONResponse(cases_list)


async def get_case_view(request: Request) -> JSONResponse:
    """Returns full scan data including Cytoscape elements and metadata."""
    case_id = request.path_params.get("case_id", "")
    case_data = get_scan_session(case_id)

    if not case_data:
        return JSONResponse({"status": "error", "message": f"Case {case_id} not found"}, status_code=404)

    return JSONResponse(case_data)


async def delete_case_view(request: Request) -> JSONResponse:
    """Deletes a saved scan session."""
    case_id = request.path_params.get("case_id", "")
    delete_scan_session(case_id)
    return JSONResponse({"status": "success", "message": f"Case {case_id} deleted"})


async def list_modules_view(request: Request) -> JSONResponse:
    """
    Returns full module and category catalog for both username and email modes,
    annotating loud and adult/NSFW modules (-lu, -le).
    """
    is_email = request.query_params.get("is_email", "false").lower() in ("true", "1", "yes")
    no_nsfw = request.query_params.get("no_nsfw", "false").lower() in ("true", "1", "yes")

    cats = load_categories(is_email=is_email, no_nsfw=no_nsfw)
    catalog = {}
    total_mods = 0

    for cat_name, cat_path in sorted(cats.items()):
        mods = load_modules(cat_path)
        mod_items = []
        for m in sorted(mods, key=lambda x: get_site_name(x).lower()):
            site_name = get_site_name(m)
            mod_stem = m.__name__.split(".")[-1].lower()
            mod_items.append({
                "name": site_name,
                "stem": mod_stem,
                "is_loud": is_loud(site_name, is_email=is_email),
                "is_nsfw": cat_name.lower() == "adult"
            })
            total_mods += 1
        catalog[cat_name.upper()] = mod_items

    return JSONResponse({
        "status": "success",
        "is_email": is_email,
        "total_categories": len(catalog),
        "total_modules": total_mods,
        "categories": catalog
    })


async def validate_proxies_view(request: Request) -> JSONResponse:
    """
    Validates a list of proxies against gstatic.com/generate_204 (--validate-proxies).
    """
    try:
        body = await request.json()
        raw_proxies = body.get("proxies", [])
        if isinstance(raw_proxies, str):
            raw_proxies = [p.strip() for p in raw_proxies.splitlines() if p.strip() and not p.strip().startswith("#")]

        cleaned = []
        for p in raw_proxies:
            p_str = p.strip()
            if p_str and not p_str.startswith("#"):
                if "://" not in p_str:
                    p_str = "http://" + p_str
                cleaned.append(p_str)

        if not cleaned:
            return JSONResponse({"status": "error", "message": "No valid proxy URLs provided"}, status_code=400)

        timeout = int(body.get("timeout", 5))
        working = await _validate_proxies_batch(cleaned, timeout=timeout, max_workers=40)

        return JSONResponse({
            "status": "success",
            "total_tested": len(cleaned),
            "working_count": len(working),
            "working_proxies": working
        })
    except Exception as e:
        logger.error(f"Proxy validation error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def hudson_check_view(request: Request) -> JSONResponse:
    """
    Queries Hudson Rock Cavalier v2 API for infostealer intelligence (--hudson).
    """
    target = request.query_params.get("target", "").strip().lstrip("@")
    if not target and request.method == "POST":
        try:
            body = await request.json()
            target = (body.get("target") or body.get("target_handle") or "").strip().lstrip("@")
        except Exception:
            pass

    if not target:
        return JSONResponse({"status": "error", "message": "No target specified"}, status_code=400)

    is_email = "@" in target
    base_url = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/"
    endpoint = "search-by-email" if is_email else "search-by-username"
    param = "email" if is_email else "username"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{base_url}{endpoint}", params={param: target})
            if resp.status_code == 200:
                data = resp.json()
                stealers = data.get("stealers", [])
                return JSONResponse({
                    "status": "success",
                    "target": target,
                    "is_email": is_email,
                    "infected": len(stealers) > 0,
                    "total_infections": len(stealers),
                    "stealers": stealers
                })
            elif resp.status_code == 404:
                return JSONResponse({
                    "status": "success",
                    "target": target,
                    "is_email": is_email,
                    "infected": False,
                    "total_infections": 0,
                    "stealers": []
                })
            else:
                return JSONResponse({
                    "status": "error",
                    "message": f"Hudson Rock API returned HTTP {resp.status_code}"
                }, status_code=resp.status_code)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


def _extract_results_from_case(case_data: dict[str, Any]) -> tuple[str, str, int, list[Result]]:
    """
    Extracts or reconstructs native Result objects and metadata from case data.
    Returns: (target, scan_type, total_modules, results)
    """
    target = str(case_data.get("threat_actor") or case_data.get("target") or "target")

    scan_type = case_data.get("scan_type")
    if not scan_type:
        cat = str(case_data.get("category", "")).lower()
        base = "Email" if "@" in target else "Username"
        if "cross" in cat:
            scan_type = f"Cross-Scan ({base})"
        else:
            scan_type = base

    total_modules = int(case_data.get("total_modules") or case_data.get("total_checked") or case_data.get("total_hits") or 0)

    results: list[Result] = []

    # Priority 1: Use raw_results if saved by web scan engine or benchmark
    if "raw_results" in case_data and isinstance(case_data["raw_results"], list):
        for item in case_data["raw_results"]:
            if isinstance(item, Result):
                results.append(item)
            elif isinstance(item, dict):
                s_val = item.get("status", "")
                if isinstance(s_val, Status):
                    status = s_val
                else:
                    s_str = str(s_val).upper()
                    if s_str in ("FOUND", "REGISTERED", "TAKEN", "0", "STATUS.TAKEN"):
                        status = Status.TAKEN
                    elif s_str in ("NOT FOUND", "NOT REGISTERED", "AVAILABLE", "1", "STATUS.AVAILABLE"):
                        status = Status.AVAILABLE
                    elif s_str in ("SKIPPED", "3", "STATUS.SKIPPED"):
                        status = Status.SKIPPED
                    else:
                        status = Status.ERROR

                user = item.get("username") or item.get("email") or target
                is_em = bool(item.get("is_email") or item.get("email") or ("@" in str(user)))
                r = Result(
                    status=status,
                    reason=item.get("reason") or None,
                    username=user,
                    site_name=item.get("site_name") or item.get("platform") or "",
                    category=item.get("category", "OSINT"),
                    url=item.get("url", ""),
                    is_email=is_em,
                    extra=item.get("extra") if isinstance(item.get("extra"), dict) else {},
                    media=item.get("media") if isinstance(item.get("media"), dict) else {},
                )
                results.append(r)

    # Priority 2: Fallback reconstruction from graph elements for legacy cases
    if not results and "elements" in case_data:
        for el in case_data.get("elements", []):
            d = el.get("data", {})
            if d.get("type") in ("SOCIAL_ACCOUNT", "EMAIL"):
                site_name = d.get("label", "")
                meta = d.get("metadata", {})
                item_target = meta.get("target") or (meta.get("email") if d.get("type") == "EMAIL" else target)
                url = d.get("url") or meta.get("url") or ""
                cat = d.get("category") or "OSINT"
                extra = {k: v for k, v in meta.items() if k not in ("url", "category", "target", "email")}
                media = {}
                if d.get("avatar_url"):
                    media["avatar"] = d.get("avatar_url")

                r = Result.taken(
                    username=item_target,
                    site_name=site_name,
                    category=cat,
                    url=url,
                    extra=extra,
                    media=media,
                    is_email=(d.get("type") == "EMAIL" or "@" in str(item_target)),
                )
                results.append(r)

    if total_modules == 0:
        total_modules = len(results)

    return target, scan_type, total_modules, results


async def export_csv_view(request: Request) -> Response:
    """Exports case findings as CSV spreadsheet using native user-scanner core formatter (-f csv)."""
    case_id = request.path_params.get("case_id", "")
    case_data = get_scan_session(case_id)

    if not case_data:
        return JSONResponse({"status": "error", "message": "Case not found"}, status_code=404)

    target, _, _, results = _extract_results_from_case(case_data)
    csv_text = formatter.into_csv(results)

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="audit_{target}_{case_id}.csv"'}
    )


async def export_json_view(request: Request) -> Response:
    """Exports raw findings as structured JSON array using native user-scanner core formatter (-f json)."""
    case_id = request.path_params.get("case_id", "")
    case_data = get_scan_session(case_id)

    if not case_data:
        return JSONResponse({"status": "error", "message": "Case not found"}, status_code=404)

    target, _, _, results = _extract_results_from_case(case_data)
    json_text = formatter.into_json(results)

    return Response(
        content=json_text,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="results_{target}_{case_id}.json"'}
    )


async def export_pdf_view(request: Request) -> Response:
    """Exports case as professional executive PDF report using native user-scanner core formatter (-f pdf)."""
    case_id = request.path_params.get("case_id", "")
    case_data = get_scan_session(case_id)

    if not case_data:
        return JSONResponse({"status": "error", "message": "Case not found"}, status_code=404)

    target, scan_type, total_modules, results = _extract_results_from_case(case_data)
    version_str, _ = load_local_version()

    try:
        pdf_bytes = formatter.into_pdf(
            results=results,
            target=target,
            scan_type=scan_type,
            total_modules=total_modules,
            include_media=True,
            version=version_str,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report_{target}_{case_id}.pdf"'}
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": f"PDF Generation Error: {e}"}, status_code=500)


async def scan_stream_view(request: Request):
    """
    Real-time SSE streaming scan generator supporting all CLI options:
    - -u / -e (single username or email)
    - -uf / -ef (bulk targets list)
    - -m (specific modules)
    - -c (specific categories)
    - -s / --stop (permutations)
    - -t / --timeout (request timeout override)
    - -C / --concurrency (semaphore size)
    - -d / --delay (rate limiting)
    - -P / --proxy-file (proxy rotation)
    - --allow-loud (loud modules)
    - --no-nsfw (exclude adult sites)
    - --all (show all results)
    - --cross-scan, --cross-links, --cross-emails, --cross-depth, --cross-sweep
    - --hudson / --hudson-scan
    """
    body: Dict[str, Any] = {}
    if request.method == "POST":
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = json.loads(body_bytes)
        except Exception as e:
            logger.debug(f"Error parsing POST body: {e}")

    # Resolve target list
    raw_targets = body.get("targets") or body.get("target_handle") or body.get("target_url")
    if not raw_targets:
        raw_targets = request.query_params.get("target") or request.query_params.get("u") or request.query_params.get("email") or ""

    targets_list: List[str] = []
    if isinstance(raw_targets, list):
        targets_list = [str(t).strip().lstrip("@") for t in raw_targets if str(t).strip()]
    elif isinstance(raw_targets, str):
        if "\n" in raw_targets:
            targets_list = [t.strip().lstrip("@") for t in raw_targets.splitlines() if t.strip() and not t.strip().startswith("#")]
        elif "," in raw_targets:
            targets_list = [t.strip().lstrip("@") for t in raw_targets.split(",") if t.strip()]
        elif raw_targets.strip():
            targets_list = [raw_targets.strip().lstrip("@")]

    if not targets_list:
        async def err_gen():
            yield f"data: {json.dumps({'event': 'error', 'message': 'No target usernames or emails specified.'})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    # Resolve scan parameters
    scan_type = body.get("scan_type", "auto")
    category_filter = body.get("categories") or body.get("category") or request.query_params.get("category") or "ALL"
    requested_modules = body.get("modules") or []
    if isinstance(requested_modules, str):
        requested_modules = [m.strip().lower() for m in requested_modules.split(",") if m.strip()]

    allow_loud = bool(body.get("allow_loud", False))
    no_nsfw = bool(body.get("no_nsfw", False))
    show_all = bool(body.get("show_all", False))
    timeout = float(body["timeout"]) if "timeout" in body and body["timeout"] else None
    concurrency = int(body.get("concurrency", 0))
    delay = float(body.get("delay", 0))
    stop_permutations = int(body.get("stop_permutations", 1))
    proxies = body.get("proxies") or []
    hudson_scan = bool(body.get("hudson_scan", False))

    cross_scan = bool(body.get("cross_scan", False))
    cross_links = str(body.get("cross_links", "all")).lower()
    cross_emails = str(body.get("cross_emails", "verified")).lower()
    cross_depth = int(body.get("cross_depth", 1))
    cross_sweep = int(body.get("cross_sweep", 3))

    # Apply global timeout and proxy manager (or reset previous state)
    set_global_timeout(timeout if timeout else None)

    if proxies:
        if isinstance(proxies, str):
            proxies = [p.strip() for p in proxies.splitlines() if p.strip() and not p.strip().startswith("#")]
        try:
            set_proxy_manager(proxies=proxies)
            logger.info(f"Loaded {len(proxies)} proxies for scan session")
        except Exception as ex:
            logger.warning(f"Could not load proxies: {ex}")
    else:
        set_proxy_manager(proxies=None)

    async def event_generator():
        start_time = time.time()
        primary_target = targets_list[0]
        case_id = f"live-{primary_target.lower()}-{uuid.uuid4().hex[:6]}"

        accumulated_elements = []
        total_found = 0
        total_checked = 0
        category_counts: Dict[str, int] = {}

        # If permutations requested for single username
        expanded_targets = []
        if len(targets_list) == 1 and stop_permutations > 1:
            expanded_targets = list(islice(expand_patterns_random(primary_target), stop_permutations))
        if not expanded_targets:
            expanded_targets = targets_list

        # Calculate default concurrency and target type
        if scan_type == "email":
            is_primary_email = True
        elif scan_type == "username":
            is_primary_email = False
        else:
            is_primary_email = is_valid_email(primary_target)

        effective_concurrency = concurrency if concurrency > 0 else (25 if is_primary_email else 60)
        sem = asyncio.Semaphore(effective_concurrency)

        configs = ScanConfig(
            allow_loud=allow_loud,
            show_all=show_all,
            no_nsfw=no_nsfw,
            verbose=False,
            timeout=timeout,
        )

        def _resolve_target_modules(is_em: bool):
            mods = []
            if requested_modules:
                for mod_name in requested_modules:
                    clean_mod = mod_name.strip().lower().lstrip("@").removesuffix(".py")
                    if "." in clean_mod:
                        clean_mod = clean_mod.split(".")[0]
                    found = find_module(clean_mod.replace(".", "_"), is_em, no_nsfw)
                    for m in found:
                        s_name = get_site_name(m)
                        if not allow_loud and is_loud(s_name, is_email=is_em):
                            continue
                        mods.append((m, (find_category(m) or "CUSTOM").upper()))
            else:
                cats_dict = load_categories(is_email=is_em, no_nsfw=no_nsfw)
                if category_filter and category_filter != "ALL":
                    requested_cats = category_filter if isinstance(category_filter, list) else [c.strip().upper() for c in category_filter.split(",") if c.strip()]
                    cats_dict = {k: v for k, v in cats_dict.items() if k.upper() in requested_cats}

                for cat_name, cat_path in cats_dict.items():
                    mods_in_cat = load_modules(cat_path)
                    for m in mods_in_cat:
                        s_name = get_site_name(m)
                        if not allow_loud and is_loud(s_name, is_email=is_em):
                            continue
                        mods.append((m, cat_name.upper()))
            return mods

        target_modules_map: Dict[str, list] = {}
        total_expected_checks = 0
        for t_item in expanded_targets:
            c_t = t_item.strip().lstrip("@")
            if scan_type == "email":
                is_em = True
            elif scan_type == "username":
                is_em = False
            else:
                is_em = is_valid_email(c_t)
            t_mods = _resolve_target_modules(is_em)
            target_modules_map[c_t] = t_mods
            total_expected_checks += len(t_mods)

        if requested_modules:
            any_valid_module = False
            for mod_name in requested_modules:
                clean_mod = mod_name.strip().lower().lstrip("@").removesuffix(".py")
                if "." in clean_mod:
                    clean_mod = clean_mod.split(".")[0]
                if find_module(clean_mod.replace(".", "_"), is_primary_email, no_nsfw):
                    any_valid_module = True
                    break
            if not any_valid_module:
                msg = f"Specified module(s) ({', '.join(requested_modules)}) not found for {'email' if is_primary_email else 'username'} scan."
                yield f"data: {json.dumps({'event': 'error', 'message': msg})}\n\n"
                return

        # Initialize session state and root nodes
        initial_root_nodes = []
        for idx, t in enumerate(expanded_targets):
            if scan_type == "email":
                is_email_t = True
            elif scan_type == "username":
                is_email_t = False
            else:
                is_email_t = is_valid_email(t)
            root_id = f"actor_{re.sub(r'[^a-zA-Z0-9_]', '_', t.lower())}"
            root_node = {
                "data": {
                    "id": root_id,
                    "label": f"Email: {t}" if is_email_t else f"Target: @{t}",
                    "type": "TARGET",
                    "color": "#EF4444" if idx == 0 else "#F59E0B",
                    "shape": "octagon",
                    "metadata": {
                        "target": t,
                        "is_email": is_email_t,
                        "role": "Primary Target" if idx == 0 else "Batch Target",
                        "status": "Scanning",
                    }
                }
            }
            initial_root_nodes.append(root_node)
            accumulated_elements.append(root_node)

        init_payload = {
            "event": "init",
            "case_id": case_id,
            "target": primary_target,
            "threat_actor": primary_target,
            "targets_count": len(expanded_targets),
            "total_modules": total_expected_checks,
            "total_checks": total_expected_checks,
            "initial_elements": initial_root_nodes
        }
        yield f"data: {json.dumps(init_payload)}\n\n"
        await asyncio.sleep(0.01)

        base_scan_type = "Email" if scan_type == "email" else "Username"
        scan_type_str = f"Cross-Scan ({base_scan_type})" if cross_scan else base_scan_type

        # Pre-seed session immediately so exports are valid even if queried during scan
        save_scan_session(case_id, {
            "case_id": case_id,
            "target": primary_target,
            "threat_actor": primary_target,
            "title": f"OSINT Intelligence Session: @{primary_target}",
            "category": "Cross-Platform Intelligence" if cross_scan else f"{base_scan_type} Footprint",
            "scan_type": scan_type_str,
            "last_scan_date": datetime.now(timezone.utc).isoformat(),
            "source": "user-scanner Intelligence Suite",
            "description": f"Scan in progress across {total_expected_checks} checks.",
            "elements": list(accumulated_elements),
            "total_hits": 0,
            "total_modules": total_expected_checks,
            "category_counts": {},
            "raw_results": [],
        })

        primary_actor_id = f"actor_{re.sub(r'[^a-zA-Z0-9_]', '_', primary_target.lower())}"
        all_raw_results: List[Result] = []
        scanned_emails: set[str] = set()
        scanned_usernames: set[str] = set()
        for t_item in expanded_targets:
            c_t = t_item.strip().lstrip("@").lower()
            if "@" in c_t or scan_type == "email":
                scanned_emails.add(c_t)
            else:
                scanned_usernames.add(c_t)

        # Execute platform sweeps for queued targets
        for t_idx, target_item in enumerate(expanded_targets):
            clean_target = target_item.strip().lstrip("@")
            is_email = ("@" in clean_target) or (scan_type == "email")
            root_actor_id = f"actor_{re.sub(r'[^a-zA-Z0-9_]', '_', clean_target.lower())}"

            if t_idx > 0 and delay > 0:
                await asyncio.sleep(delay)

            # Optional: Hudson Rock Infostealer Check
            if hudson_scan:
                try:
                    base_url = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/"
                    endpoint = "search-by-email" if is_email else "search-by-username"
                    param = "email" if is_email else "username"
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        resp = await client.get(f"{base_url}{endpoint}", params={param: clean_target})
                        if resp.status_code == 200:
                            hdata = resp.json()
                            stealers = hdata.get("stealers", [])
                            hudson_payload = {
                                "event": "hudson",
                                "target": clean_target,
                                "infected": len(stealers) > 0,
                                "total_infections": len(stealers),
                                "stealers": stealers
                            }
                            yield f"data: {json.dumps(hudson_payload)}\n\n"
                except Exception as ex:
                    logger.debug(f"Hudson scan error for {clean_target}: {ex}")

            # Module Selection Logic (-m and -c)
            modules_to_run = target_modules_map.get(clean_target)
            if modules_to_run is None:
                modules_to_run = _resolve_target_modules(is_email)

            total_mods_target = len(modules_to_run)
            queue = asyncio.Queue()

            async def worker(mod, cat):
                try:
                    if is_email:
                        res = await _email_async_worker(mod, clean_target, sem, configs, cat_override=cat)
                    else:
                        res = await _user_async_worker(mod, clean_target, sem, configs, cat_override=cat)
                    await queue.put((mod, cat, res))
                except Exception:
                    await queue.put((mod, cat, None))

            for m, c in modules_to_run:
                asyncio.create_task(worker(m, c))

            raw_target_results: List[Result] = []

            for mod_idx in range(total_mods_target):
                mod, cat_upper, result = await queue.get()
                total_checked += 1

                if total_checked % 3 == 0 or total_checked == total_expected_checks or mod_idx == total_mods_target - 1:
                    remaining = max(0, total_expected_checks - total_checked)
                    pct = round((total_checked / total_expected_checks * 100), 1) if total_expected_checks > 0 else 0
                    progress_payload = {
                        "event": "progress",
                        "checked": total_checked,
                        "total": total_expected_checks,
                        "remaining": remaining,
                        "percent": pct,
                        "target": clean_target,
                        "found": total_found
                    }
                    yield f"data: {json.dumps(progress_payload)}\n\n"

                if result and getattr(result, "status", None) == Status.TAKEN:
                    total_found += 1
                    raw_target_results.append(result)
                    all_raw_results.append(result)
                    site = getattr(result, "site_name", "") or get_site_name(mod).capitalize()
                    clean_site_id = re.sub(r"[^a-zA-Z0-9_]", "", site.lower())
                    node_id = f"plat_{clean_target.lower()}_{clean_site_id}"
                    edge_id = f"edge_{clean_target.lower()}_{clean_site_id}"

                    extra = getattr(result, "extra", {}) or {}
                    media = getattr(result, "media", {}) or {}
                    bio = extra.get("bio") or extra.get("about") or extra.get("description") or ""

                    avatar_url = (
                        media.get("avatar") or media.get("image") or media.get("photo")
                        or extra.get("avatar_url") or extra.get("avatar") or None
                    )

                    # Extract emails
                    discovered_emails = []
                    if "email" in extra and extra["email"]:
                        discovered_emails.append(str(extra["email"]))
                    if bio:
                        e_matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}", str(bio))
                        discovered_emails.extend(e_matches)
                    discovered_emails = list(set(discovered_emails))

                    # Extract secondary handles
                    discovered_handles = []
                    if "links" in extra:
                        l_matches = re.findall(r"(?:github\.com/|instagram\.com/|t\.me/|x\.com/)([a-zA-Z0-9_.-]+)", str(extra["links"]))
                        discovered_handles.extend(l_matches)
                    discovered_handles = [h for h in set(discovered_handles) if h.lower() != clean_target.lower()]

                    color = CATEGORY_COLORS.get(cat_upper, "#10B981")
                    hit_node = {
                        "data": {
                            "id": node_id,
                            "label": site,
                            "type": "SOCIAL_ACCOUNT",
                            "category": cat_upper,
                            "color": color,
                            "shape": "round-diamond",
                            "url": getattr(result, "url", ""),
                            "bio": str(bio)[:300] if bio else "",
                            "avatar_url": avatar_url,
                            "metadata": {
                                "platform": site,
                                "category": cat_upper,
                                "url": getattr(result, "url", ""),
                                "bio": str(bio),
                                "avatar_url": avatar_url,
                                "linked_emails": discovered_emails,
                                "linked_handles": discovered_handles,
                                **{k: str(v) for k, v in extra.items() if k not in ("bio", "about")}
                            }
                        }
                    }

                    hit_edge = {
                        "data": {
                            "id": edge_id,
                            "source": root_actor_id,
                            "target": node_id,
                            "relation": "REGISTERED_ON"
                        }
                    }

                    accumulated_elements.extend([hit_node, hit_edge])
                    category_counts[cat_upper] = category_counts.get(cat_upper, 0) + 1

                    hit_payload = {
                        "event": "hit",
                        "platform": site,
                        "target": clean_target,
                        "hit_index": total_found,
                        "actor_node_id": root_actor_id,
                        "category": cat_upper,
                        "node": hit_node,
                        "edge": hit_edge
                    }
                    yield f"data: {json.dumps(hit_payload)}\n\n"

                    # Add email pivot nodes
                    for em in discovered_emails:
                        em_id = f"piv_em_{re.sub(r'[^a-zA-Z0-9]', '_', em)}"
                        em_node = {
                            "data": {
                                "id": em_id,
                                "label": em,
                                "type": "EMAIL",
                                "color": "#EC4899",
                                "shape": "round-rectangle",
                                "metadata": {"email": em, "source": f"Scraped from {site} bio"}
                            }
                        }
                        em_edge = {
                            "data": {
                                "id": f"edge_{node_id}_{em_id}",
                                "source": node_id,
                                "target": em_id,
                                "relation": "EXPOSES_EMAIL"
                            }
                        }
                        accumulated_elements.extend([em_node, em_edge])
                        category_counts["PIVOTS"] = category_counts.get("PIVOTS", 0) + 1

                        pivot_payload = {
                            "event": "hit",
                            "platform": f"Email: {em}",
                            "hit_index": total_found + 1,
                            "actor_node_id": node_id,
                            "category": "PIVOTS",
                            "node": em_node,
                            "edge": em_edge
                        }
                        yield f"data: {json.dumps(pivot_payload)}\n\n"

        # Cross-Scan Multi-Round Pivot Execution (--cross-scan)
        if cross_scan and all_raw_results:
            try:
                current_round_results = list(all_raw_results)
                for round_num in range(1, cross_depth + 1):
                    # Extract fresh username pivots
                    try:
                        raw_user_pivots = extract_pivots(current_round_results)
                        filtered_user_pivots = select_pivots(raw_user_pivots, links=cross_links)
                    except Exception as ex:
                        logger.debug(f"Extract user pivots error: {ex}")
                        filtered_user_pivots = []

                    fresh_user_pivots = [
                        p for p in filtered_user_pivots
                        if p.username.lower() not in scanned_usernames
                    ]
                    ranked_usernames = rank_usernames(fresh_user_pivots)

                    # Also collect any secondary handles discovered in bio / links
                    for r in current_round_results:
                        extra_data = getattr(r, "extra", {}) or {}
                        if "links" in extra_data:
                            l_matches = re.findall(r"(?:github\.com/|instagram\.com/|t\.me/|x\.com/)([a-zA-Z0-9_.-]+)", str(extra_data["links"]))
                            for h in l_matches:
                                hl = h.strip().lower()
                                if hl not in scanned_usernames and hl not in [u.lower() for u in ranked_usernames]:
                                    ranked_usernames.append(h)

                    # Extract fresh email pivots
                    try:
                        raw_email_pivots = extract_email_pivots(current_round_results)
                        filtered_email_pivots = select_email_pivots(raw_email_pivots, emails=cross_emails)
                    except Exception as ex:
                        logger.debug(f"Extract email pivots error: {ex}")
                        filtered_email_pivots = []

                    ranked_emails = [
                        ep.email for ep in filtered_email_pivots
                        if ep.email.lower() not in scanned_emails
                    ]
                    # If verified tier yielded nothing or emails == 'all', fallback to all email pivots
                    if not ranked_emails and cross_emails != "none":
                        ranked_emails = [
                            ep.email for ep in raw_email_pivots
                            if ep.email.lower() not in scanned_emails
                        ]

                    # Also collect any emails discovered in bio / extra
                    for r in current_round_results:
                        extra_data = getattr(r, "extra", {}) or {}
                        if "email" in extra_data and extra_data["email"]:
                            em_cand = str(extra_data["email"]).strip()
                            if is_valid_email(em_cand) and em_cand.lower() not in scanned_emails and em_cand not in ranked_emails:
                                ranked_emails.append(em_cand)
                        bio_cand = extra_data.get("bio") or extra_data.get("about") or ""
                        if bio_cand:
                            for em_m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}", str(bio_cand)):
                                if is_valid_email(em_m) and em_m.lower() not in scanned_emails and em_m not in ranked_emails:
                                    ranked_emails.append(em_m)

                    # Stop if no new pivots to follow
                    if not ranked_usernames and not ranked_emails:
                        break

                    # Allocate pivot budget
                    budget = max(1, cross_sweep)
                    for_emails = min(budget // 2 if ranked_usernames else budget, len(ranked_emails))
                    for_usernames = min(budget - for_emails, len(ranked_usernames))
                    if for_emails == 0 and ranked_emails and (budget - for_usernames) > 0:
                        for_emails = min(budget - for_usernames, len(ranked_emails))

                    targets_to_scan_emails = ranked_emails[:for_emails]
                    targets_to_scan_users = ranked_usernames[:for_usernames]

                    round_discovered_results: List[Result] = []

                    # Sweep email targets
                    for sec_email in targets_to_scan_emails:
                        sec_email_clean = sec_email.strip().lower()
                        scanned_emails.add(sec_email_clean)

                        em_node_id = f"piv_em_{re.sub(r'[^a-zA-Z0-9]', '_', sec_email_clean)}"
                        existing_node = next((el for el in accumulated_elements if el.get("data", {}).get("id") == em_node_id), None)
                        if not existing_node:
                            em_node = {
                                "data": {
                                    "id": em_node_id,
                                    "label": sec_email_clean,
                                    "type": "EMAIL",
                                    "color": "#EC4899",
                                    "shape": "round-rectangle",
                                    "metadata": {
                                        "email": sec_email_clean,
                                        "role": "Cross-Scan Pivot Target",
                                        "status": "Scanning",
                                        "round": round_num
                                    }
                                }
                            }
                            em_edge = {
                                "data": {
                                    "id": f"edge_pivot_{primary_actor_id}_{em_node_id}",
                                    "source": primary_actor_id,
                                    "target": em_node_id,
                                    "relation": "PIVOT_EMAIL"
                                }
                            }
                            accumulated_elements.extend([em_node, em_edge])
                        else:
                            em_node = existing_node
                            em_edge = None

                        # Sweep email modules against the target
                        email_mods_to_run = _resolve_target_modules(is_em=True)
                        total_expected_checks += len(email_mods_to_run)

                        # Emit cross_round notification to frontend
                        cross_event = {
                            "event": "cross_round",
                            "round": round_num,
                            "target": sec_email_clean,
                            "target_type": "email",
                            "total_modules": total_expected_checks,
                            "actor_node_id": em_node_id,
                            "node": em_node,
                            "edge": em_edge
                        }
                        yield f"data: {json.dumps(cross_event)}\n\n"

                        email_queue = asyncio.Queue()
                        async def email_worker(m, cat):
                            try:
                                res = await _email_async_worker(m, sec_email_clean, sem, configs, cat_override=cat)
                                await email_queue.put((m, cat, res))
                            except Exception:
                                await email_queue.put((m, cat, None))

                        for m, c in email_mods_to_run:
                            asyncio.create_task(email_worker(m, c))

                        for mod_idx in range(len(email_mods_to_run)):
                            m, cat_upper, result = await email_queue.get()
                            total_checked += 1
                            if total_checked % 3 == 0 or total_checked == total_expected_checks or mod_idx == len(email_mods_to_run) - 1:
                                remaining = max(0, total_expected_checks - total_checked)
                                pct = round((total_checked / total_expected_checks * 100), 1) if total_expected_checks > 0 else 0
                                yield f"data: {json.dumps({'event': 'progress', 'checked': total_checked, 'total': total_expected_checks, 'remaining': remaining, 'percent': pct, 'target': sec_email_clean, 'found': total_found})}\n\n"

                            if result and getattr(result, "status", None) == Status.TAKEN:
                                total_found += 1
                                round_discovered_results.append(result)
                                all_raw_results.append(result)
                                csite = getattr(result, "site_name", "") or get_site_name(m).capitalize()
                                c_clean_id = re.sub(r'[^a-zA-Z0-9_]', '', csite.lower())
                                c_node_id = f"plat_{re.sub(r'[^a-zA-Z0-9_]', '_', sec_email_clean)}_{c_clean_id}"
                                extra_res = getattr(result, "extra", {}) or {}
                                bio_res = extra_res.get("bio") or extra_res.get("about") or ""
                                avatar_res = getattr(result, "media", {}).get("avatar") if hasattr(result, "media") else None

                                c_node = {
                                    "data": {
                                        "id": c_node_id,
                                        "label": csite,
                                        "type": "SOCIAL_ACCOUNT",
                                        "category": cat_upper,
                                        "color": CATEGORY_COLORS.get(cat_upper, "#EC4899"),
                                        "shape": "round-diamond",
                                        "url": getattr(result, "url", ""),
                                        "avatar_url": avatar_res,
                                        "metadata": {
                                            "platform": csite,
                                            "category": cat_upper,
                                            "url": getattr(result, "url", ""),
                                            "bio": str(bio_res),
                                            "target": sec_email_clean,
                                            **{k: str(v) for k, v in extra_res.items() if k not in ("bio", "about")}
                                        }
                                    }
                                }
                                c_edge = {
                                    "data": {
                                        "id": f"edge_{em_node_id}_{c_node_id}",
                                        "source": em_node_id,
                                        "target": c_node_id,
                                        "relation": "REGISTERED_ON"
                                    }
                                }
                                accumulated_elements.extend([c_node, c_edge])
                                category_counts[cat_upper] = category_counts.get(cat_upper, 0) + 1
                                yield f"data: {json.dumps({'event': 'hit', 'platform': csite, 'target': sec_email_clean, 'hit_index': total_found, 'actor_node_id': em_node_id, 'node': c_node, 'edge': c_edge})}\n\n"

                    # Sweep username targets
                    for sec_user in targets_to_scan_users:
                        sec_user_clean = sec_user.strip().lstrip("@")
                        scanned_usernames.add(sec_user_clean.lower())

                        sec_node_id = f"actor_piv_{re.sub(r'[^a-zA-Z0-9_]', '_', sec_user_clean.lower())}"
                        existing_user_node = next((el for el in accumulated_elements if el.get("data", {}).get("id") == sec_node_id), None)
                        if not existing_user_node:
                            sec_node = {
                                "data": {
                                    "id": sec_node_id,
                                    "label": f"Pivot: @{sec_user_clean}",
                                    "type": "PIVOT_USER",
                                    "color": "#A855F7",
                                    "shape": "hexagon",
                                    "metadata": {
                                        "target": sec_user_clean,
                                        "role": "Cross-Scan Pivot",
                                        "status": "Scanning",
                                        "round": round_num
                                    }
                                }
                            }
                            sec_edge = {
                                "data": {
                                    "id": f"edge_pivot_{primary_actor_id}_{sec_node_id}",
                                    "source": primary_actor_id,
                                    "target": sec_node_id,
                                    "relation": "CROSS_PIVOT_TO"
                                }
                            }
                            accumulated_elements.extend([sec_node, sec_edge])
                        else:
                            sec_node = existing_user_node
                            sec_edge = None

                        # Sweep username modules against the target
                        user_mods_to_run = _resolve_target_modules(is_em=False)
                        total_expected_checks += len(user_mods_to_run)

                        cross_event = {
                            "event": "cross_round",
                            "round": round_num,
                            "target": sec_user_clean,
                            "target_type": "username",
                            "total_modules": total_expected_checks,
                            "actor_node_id": sec_node_id,
                            "node": sec_node,
                            "edge": sec_edge
                        }
                        yield f"data: {json.dumps(cross_event)}\n\n"

                        user_queue = asyncio.Queue()
                        async def user_worker(m, cat):
                            try:
                                res = await _user_async_worker(m, sec_user_clean, sem, configs, cat_override=cat)
                                await user_queue.put((m, cat, res))
                            except Exception:
                                await user_queue.put((m, cat, None))

                        for m, c in user_mods_to_run:
                            asyncio.create_task(user_worker(m, c))

                        for mod_idx in range(len(user_mods_to_run)):
                            m, cat_upper, result = await user_queue.get()
                            total_checked += 1
                            if total_checked % 3 == 0 or total_checked == total_expected_checks or mod_idx == len(user_mods_to_run) - 1:
                                remaining = max(0, total_expected_checks - total_checked)
                                pct = round((total_checked / total_expected_checks * 100), 1) if total_expected_checks > 0 else 0
                                yield f"data: {json.dumps({'event': 'progress', 'checked': total_checked, 'total': total_expected_checks, 'remaining': remaining, 'percent': pct, 'target': sec_user_clean, 'found': total_found})}\n\n"

                            if result and getattr(result, "status", None) == Status.TAKEN:
                                total_found += 1
                                round_discovered_results.append(result)
                                all_raw_results.append(result)
                                csite = getattr(result, "site_name", "") or get_site_name(m).capitalize()
                                c_clean_id = re.sub(r'[^a-zA-Z0-9_]', '', csite.lower())
                                c_node_id = f"plat_{re.sub(r'[^a-zA-Z0-9_]', '_', sec_user_clean.lower())}_{c_clean_id}"
                                extra_res = getattr(result, "extra", {}) or {}
                                bio_res = extra_res.get("bio") or extra_res.get("about") or ""
                                avatar_res = getattr(result, "media", {}).get("avatar") if hasattr(result, "media") else None

                                c_node = {
                                    "data": {
                                        "id": c_node_id,
                                        "label": csite,
                                        "type": "SOCIAL_ACCOUNT",
                                        "category": cat_upper,
                                        "color": CATEGORY_COLORS.get(cat_upper, "#10B981"),
                                        "shape": "round-diamond",
                                        "url": getattr(result, "url", ""),
                                        "avatar_url": avatar_res,
                                        "metadata": {
                                            "platform": csite,
                                            "category": cat_upper,
                                            "url": getattr(result, "url", ""),
                                            "bio": str(bio_res),
                                            "target": sec_user_clean,
                                            **{k: str(v) for k, v in extra_res.items() if k not in ("bio", "about")}
                                        }
                                    }
                                }
                                c_edge = {
                                    "data": {
                                        "id": f"edge_{sec_node_id}_{c_node_id}",
                                        "source": sec_node_id,
                                        "target": c_node_id,
                                        "relation": "REGISTERED_ON"
                                    }
                                }
                                accumulated_elements.extend([c_node, c_edge])
                                category_counts[cat_upper] = category_counts.get(cat_upper, 0) + 1
                                yield f"data: {json.dumps({'event': 'hit', 'platform': csite, 'target': sec_user_clean, 'hit_index': total_found, 'actor_node_id': sec_node_id, 'node': c_node, 'edge': c_edge})}\n\n"

                    # Prepare for next round
                    if not round_discovered_results:
                        break
                    current_round_results = round_discovered_results
            except Exception as ex:
                logger.error(f"Cross-scan exception: {ex}", exc_info=True)

        # Finalize scan session and persist case
        elapsed = round(time.time() - start_time, 2)
        base_scan_type = "Email" if scan_type == "email" else "Username"
        scan_type_str = f"Cross-Scan ({base_scan_type})" if cross_scan else base_scan_type

        full_case = {
            "case_id": case_id,
            "target": primary_target,
            "threat_actor": primary_target,
            "title": f"OSINT Intelligence Session: @{primary_target}",
            "category": "Cross-Platform Intelligence" if cross_scan else f"{base_scan_type} Footprint",
            "scan_type": scan_type_str,
            "last_scan_date": datetime.now(timezone.utc).isoformat(),
            "source": "user-scanner Intelligence Suite",
            "description": f"Multi-vector sweep across {total_checked} checks in {elapsed}s. Identified {total_found} verified accounts.",
            "elements": accumulated_elements,
            "total_hits": total_found,
            "total_modules": total_checked,
            "category_counts": category_counts,
            "raw_results": [r.to_dict() for r in all_raw_results],
        }

        save_scan_session(case_id, full_case)

        complete_payload = {
            "event": "complete",
            "case_id": case_id,
            "total_hits": total_found,
            "total_checked": total_checked,
            "elapsed_seconds": elapsed,
            "category_counts": category_counts,
            "full_case": full_case
        }
        yield f"data: {json.dumps(complete_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
