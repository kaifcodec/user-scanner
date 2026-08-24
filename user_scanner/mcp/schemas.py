import mcp.types as types
from typing import Any


def get_tool_list() -> list[types.Tool]:
    """Provide the list of tools available from this server."""

    # Common cross-scan parameters schema
    cross_scan_props = {
        "cross_scan": {
            "type": "boolean",
            "description": (
                "Set to true to enable recursive OSINT pivoting. The engine will "
                "automatically extract emails, alternative usernames, and links "
                "found in the initial results and scan them too, building a deep "
                "web of connections."
            ),
        },
        "cross_links": {
            "type": "string",
            "enum": ["all", "verified", "none"],
            "description": (
                "Controls link pivoting strictness during a cross-scan. "
                "'all' pivots from any bio link. 'verified' only pivots from "
                "platform-proven connections. 'none' disables link pivoting. "
                "Default: 'all'."
            ),
        },
        "cross_emails": {
            "type": "string",
            "enum": ["all", "verified", "none"],
            "description": (
                "Controls email pivoting strictness during a cross-scan. "
                "'verified' (default) only scans addresses explicitly published "
                "in an email field. 'all' includes scraping emails from bio text."
            ),
        },
        "cross_depth": {
            "type": "integer",
            "description": (
                "How deep the recursive link-following should go. Default: 1. "
                "Increase for deeper but slower investigations."
            ),
        },
        "cross_sweep": {
            "type": "integer",
            "description": (
                "How many targets the cross-scan should automatically sweep "
                "against all modules. Default: 3. Set to 0 to only scan sites "
                "explicitly named in pivots (prevents handle collisions)."
            ),
        },
    }

    # Common basic parameters schema
    basic_props = {
        "category": {
            "type": "string",
            "description": (
                "Optional category to restrict the scan to (e.g. 'social', "
                "'gaming', 'dev'). Use list_available_modules to see options. "
                "Cannot be used with 'module'."
            ),
        },
        "module": {
            "type": "string",
            "description": (
                "Optional specific site/module to restrict the scan to "
                "(e.g. 'github'). Use list_available_modules to see options. "
                "Cannot be used with 'category'."
            ),
        },
        "allow_loud": {
            "type": "boolean",
            "description": (
                "WARNING: Set to true ONLY if stealth is not required. "
                "Enabling this runs aggressive modules that may trigger "
                "password reset emails and alert the target. "
                "Default: false (stealth mode)."
            ),
        },
        "no_nsfw": {
            "type": "boolean",
            "description": (
                "Set to true to disable scanning of adult/NSFW sites. "
                "Default: false."
            ),
        },
        "proxies": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "An optional list of proxy URLs (e.g. 'http://proxy:port') "
                "to use for the scan. Recommended to avoid rate limits."
            ),
        },
        "timeout": {
            "type": "integer",
            "description": (
                "Override default request timeout in seconds. Useful if the "
                "target sites are slow or you are using slow proxies."
            ),
        },
        "concurrency": {
            "type": "integer",
            "description": (
                "Override default concurrency limit (how many requests to "
                "make in parallel)."
            ),
        },
    }

    username_props: dict[str, Any] = {
        "username": {
            "type": "string",
            "description": "The handle/username to scan for.",
        },
    }
    username_props.update(basic_props)
    username_props.update(cross_scan_props)

    email_props: dict[str, Any] = {
        "email": {
            "type": "string",
            "description": "The email address to scan for.",
        },
    }
    email_props.update(basic_props)
    email_props.update(cross_scan_props)

    return [
        types.Tool(  # type: ignore[call-arg]
            name="scan_username",
            description=(
                "Scans for the presence of a username across platforms. "
                "Can be scoped to a specific category or module, and can "
                "recursively cross-scan linked profiles."
            ),
            inputSchema={
                "type": "object",
                "properties": username_props,
                "required": ["username"],
            },
        ),
        types.Tool(  # type: ignore[call-arg]
            name="scan_email",
            description=(
                "Scans for the presence of an email across platforms. "
                "Can be scoped to a specific category or module, and can "
                "recursively cross-scan linked profiles."
            ),
            inputSchema={
                "type": "object",
                "properties": email_props,
                "required": ["email"],
            },
        ),
        types.Tool(  # type: ignore[call-arg]
            name="list_available_modules",
            description=(
                "Lists all available categories and modules (sites) "
                "supported by the scanner. Use this to discover valid "
                "inputs for the 'category' and 'module' parameters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "is_email": {
                        "type": "boolean",
                        "description": (
                            "If true, lists email scan modules. "
                            "If false, lists username scan modules. "
                            "Default: false."
                        ),
                    },
                    "no_nsfw": {
                        "type": "boolean",
                        "description": (
                            "If true, excludes adult/NSFW modules from "
                            "the listing. Default: false."
                        ),
                    },
                },
            },
        ),
    ]
