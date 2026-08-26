import asyncio
import contextlib
import json
import logging
import sys
import mcp.types as types
from typing import Any

from user_scanner.core.formatter import into_json
from user_scanner.core.helpers import (
    find_module,
    load_categories,
    load_modules,
    get_site_name,
    ScanConfig,
    set_proxy_manager,
    set_global_timeout,
)
from user_scanner.core.cross_scan import run_cross_scan, CrossScanConfig
from user_scanner.core.orchestrator import (
    run_user_full,
    run_user_category,
    run_user_module,
    set_concurrency as set_user_concurrency,
)
from user_scanner.core.email_orchestrator import (
    run_email_full_batch,
    run_email_category_batch,
    run_email_module_batch,
    set_concurrency as set_email_concurrency,
)
from user_scanner.core.result import Status

logger = logging.getLogger("user-scanner-mcp")

# Default concurrency values (must match orchestrator/email_orchestrator defaults)
_DEFAULT_USER_CONCURRENCY = 60
_DEFAULT_EMAIL_CONCURRENCY = 25

# Serialise scans so concurrent tool calls don't stomp global state
_scan_lock = asyncio.Lock()


async def execute_scan(arguments: dict, is_email: bool) -> list[types.TextContent]:
    target_key = "email" if is_email else "username"
    target = arguments.get(target_key)

    if not target:
        raise ValueError(f"Missing '{target_key}' argument")

    category = arguments.get("category")
    module_name = arguments.get("module")
    allow_loud = arguments.get("allow_loud", False)
    no_nsfw = arguments.get("no_nsfw", False)
    proxies = arguments.get("proxies")
    timeout = arguments.get("timeout")
    concurrency = arguments.get("concurrency")

    cross_scan = arguments.get("cross_scan", False)
    cross_links = arguments.get("cross_links", "all")
    cross_emails = arguments.get("cross_emails", "verified")
    cross_depth = arguments.get("cross_depth", 1)
    cross_sweep = arguments.get("cross_sweep", 3)

    if category and module_name:
        raise ValueError("Cannot specify both 'category' and 'module'. Choose one.")

    # Normalise module name the same way the CLI does (__main__.py:518)
    if module_name:
        module_name = module_name.replace(".", "_")

    logger.info(f"Executing {'email' if is_email else 'username'} scan for: {target}")

    config = ScanConfig(allow_loud=allow_loud, no_nsfw=no_nsfw, timeout=timeout)

    async with _scan_lock:
        # Apply global settings, wrapped in try/finally to always restore
        try:
            if proxies:
                logger.info(f"Setting up proxy manager with {len(proxies)} proxies.")
                set_proxy_manager(proxies=proxies)
            else:
                set_proxy_manager(proxies=None)

            if timeout is not None:
                set_global_timeout(float(timeout))
            else:
                set_global_timeout(None)

            if concurrency is not None:
                set_user_concurrency(int(concurrency))
                set_email_concurrency(int(concurrency))
            else:
                set_user_concurrency(_DEFAULT_USER_CONCURRENCY)
                set_email_concurrency(_DEFAULT_EMAIL_CONCURRENCY)

            # Redirect stdout to stderr so orchestrator print() calls
            # don't corrupt the JSON-RPC stdio stream
            with contextlib.redirect_stdout(sys.stderr):
                results = await asyncio.to_thread(
                    _run_scan, target, config, is_email, category, module_name
                )

                if cross_scan:
                    logger.info(
                        f"Running cross-scan (depth={cross_depth}, sweep={cross_sweep})"
                    )
                    cross_configs = CrossScanConfig(
                        links=cross_links,
                        emails=cross_emails,
                        sweep=cross_sweep,
                        depth=cross_depth,
                        modules=(module_name,) if module_name else (),
                        categories=(category,) if category else (),
                    )
                    cross_results = run_cross_scan(results, config, cross_configs)
                    results.extend(cross_results)
        finally:
            # Restore defaults so the next request starts clean
            set_proxy_manager(proxies=None)
            set_global_timeout(None)
            set_user_concurrency(_DEFAULT_USER_CONCURRENCY)
            set_email_concurrency(_DEFAULT_EMAIL_CONCURRENCY)

    # Build response envelope with per-status counts
    found = [r for r in results if r.status == Status.TAKEN]
    errors = [r for r in results if r.status == Status.ERROR]
    skipped = [r for r in results if r.status == Status.SKIPPED]

    envelope: dict[str, Any] = {
        "summary": {
            "total_scanned": len(results),
            "found": len(found),
            "not_found": len(results) - len(found) - len(errors) - len(skipped),
            "errors": len(errors),
            "skipped": len(skipped),
        },
        "results": json.loads(into_json(found)),
    }

    if errors:
        envelope["errored_sites"] = [
            r.site_name for r in errors if r.site_name
        ]

    logger.info(f"Found {len(found)} total valid results.")
    return [types.TextContent(type="text", text=json.dumps(envelope, indent=2))]


def _run_scan(
    target: str,
    config: ScanConfig,
    is_email: bool,
    category: str | None,
    module_name: str | None,
) -> list:
    """Run the scan synchronously via the orchestrators (not engine.check*).

    The orchestrators enforce allow_loud, no_nsfw, and loud-module gating
    exactly as the CLI does.
    """
    if module_name:
        modules = find_module(module_name, is_email=is_email, no_nsfw=config.no_nsfw)
        if not modules:
            return []
        fn = run_email_module_batch if is_email else run_user_module
        return fn(modules, target, config)
    elif category:
        cats = load_categories(is_email, config.no_nsfw)
        cat_path = cats.get(category)
        if not cat_path:
            return []
        fn_cat = run_email_category_batch if is_email else run_user_category
        return fn_cat(cat_path, target, config)
    else:
        fn_full = run_email_full_batch if is_email else run_user_full
        return fn_full(target, config)


async def handle_list_available_modules(arguments: dict) -> list[types.TextContent]:
    is_email = arguments.get("is_email", False)
    no_nsfw = arguments.get("no_nsfw", False)
    categories = load_categories(is_email=is_email, no_nsfw=no_nsfw)

    output: dict[str, Any] = {
        "scan_type": "email" if is_email else "username",
        "categories": {},
    }

    for cat_name, cat_path in categories.items():
        modules = load_modules(cat_path)
        site_names = [get_site_name(m) for m in modules]
        output["categories"][cat_name] = site_names

    return [types.TextContent(type="text", text=json.dumps(output, indent=2))]


async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Route the tool call to the correct handler."""
    if not arguments:
        arguments = {}

    if name == "scan_username":
        return await execute_scan(arguments, is_email=False)
    elif name == "scan_email":
        return await execute_scan(arguments, is_email=True)
    elif name == "list_available_modules":
        return await handle_list_available_modules(arguments)
    else:
        logger.error(f"Unknown tool called: {name}")
        raise ValueError(f"Unknown tool: {name}")
