import asyncio
import json
import logging
import mcp.types as types
from typing import Any

from user_scanner.core import engine
from user_scanner.core.formatter import into_json
from user_scanner.core.helpers import find_module, load_categories, load_modules, get_site_name, ScanConfig, set_proxy_manager, set_global_timeout
from user_scanner.core.cross_scan import run_cross_scan, CrossScanConfig
from user_scanner.core.orchestrator import set_concurrency as set_user_concurrency
from user_scanner.core.email_orchestrator import set_concurrency as set_email_concurrency

logger = logging.getLogger("user-scanner-mcp")

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
    
    if proxies:
        logger.info(f"Setting up proxy manager with {len(proxies)} proxies.")
        set_proxy_manager(proxies=proxies)
    else:
        # Clear it just in case this is a subsequent request
        set_proxy_manager(proxies=None)
        
    timeout = arguments.get("timeout")
    if timeout is not None:
        set_global_timeout(float(timeout))
    else:
        set_global_timeout(None)  # type: ignore
        
    concurrency = arguments.get("concurrency")
    if concurrency is not None:
        set_user_concurrency(int(concurrency))
        set_email_concurrency(int(concurrency))
    
    cross_scan = arguments.get("cross_scan", False)
    cross_links = arguments.get("cross_links", "all")
    cross_emails = arguments.get("cross_emails", "verified")
    cross_depth = arguments.get("cross_depth", 1)
    cross_sweep = arguments.get("cross_sweep", 3)

    if category and module_name:
        raise ValueError("Cannot specify both 'category' and 'module'. Choose one.")

    logger.info(f"Executing {'email' if is_email else 'username'} scan for: {target}")
    
    # Construct base config
    config = ScanConfig(allow_loud=allow_loud, no_nsfw=no_nsfw, timeout=timeout)
    
    # 1. Run Initial Scan
    results = []
    if module_name:
        modules = find_module(module_name, is_email=is_email, no_nsfw=no_nsfw)
        if not modules:
            return [types.TextContent(type="text", text=f"Error: Module '{module_name}' not found.")]
        # For simplicity in MCP, we just use engine.check which ignores loud checks if directly targeted
        # But to be safe, we just run the first module
        result = await engine.check(modules[0], target)
        results = [result]
    elif category:
        try:
            results = await engine.check_category(category, target, is_email=is_email)
        except ValueError as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
    else:
        results = await engine.check_all(target, is_email=is_email)

    # 2. Cross-Scan if requested
    if cross_scan:
        logger.info(f"Running cross-scan (depth={cross_depth}, sweep={cross_sweep})")
        cross_configs = CrossScanConfig(
            links=cross_links,
            emails=cross_emails,
            sweep=cross_sweep,
            depth=cross_depth,
            modules=(module_name,) if module_name else (),
            categories=(category,) if category else (),
        )
        # run_cross_scan modifies/returns a list of new results
        cross_results = await asyncio.to_thread(run_cross_scan, results, config, cross_configs)
        results.extend(cross_results)
        
    # 3. Filter and Format
    # Filter out empty results to save LLM context window limits
    found = [r for r in results if r.is_found()]
    logger.info(f"Found {len(found)} total valid results.")
    return [types.TextContent(type="text", text=into_json(found))]

async def handle_list_available_modules(arguments: dict) -> list[types.TextContent]:
    is_email = arguments.get("is_email", False)
    categories = load_categories(is_email=is_email)
    
    output: dict[str, Any] = {"scan_type": "email" if is_email else "username", "categories": {}}
    
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
