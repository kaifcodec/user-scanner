# AI contributor guide

This file orients an AI assistant (or any new contributor) working in this
repository. `CLAUDE.md` imports it via `@AGENTS.md` — edit this file only.

## What this project is

A 2-in-1 OSINT suite for **email** and **username** intelligence. It checks
whether an account exists on a given platform and, when found, extracts rich
profile metadata. See `README.md` for the full feature list and install steps.

## Start here (read before writing code)

- `README.md` — overview, features, installation, usage examples.
- `CONTRIBUTING.md` — the authoritative guide for adding scan modules
  (naming, validator signatures, orchestrator helpers, return values, style).
- `docs/USAGE.md` — library-mode usage (calling the engine from Python).
- `docs/FLAGS.md` — every CLI flag.
- `docs/CROSS_SCAN.md` — how `--cross-scan` mines scan metadata for usernames.
- `docs/PATTERNS.md` — the username/email permutation pattern syntax.

## Repository layout

- `user_scanner/user_scan/<category>/<site>.py` — **username** availability
  modules. Synchronous. Export `def validate_<site>(user: str) -> Result`.
- `user_scanner/email_scan/<category>/<service>.py` — **email** OSINT modules.
  Asynchronous. Export `async def validate_<service>(email: str) -> Result`.
- `user_scanner/core/` — engine, orchestrator, helpers, `Result`, formatters,
  exporters (JSON/CSV/PDF). Changes here affect every module; review carefully.
- `abandoned/<email_scan|user_scan>/<category>/<site>.py` — retired modules
  (dead sites, permanently broken detection). See "Retiring a module" below.
- `tests/` — pytest suite. Add tests for new core behavior only. **Do not
  add unit tests for individual scan modules** — modules are verified by
  live-testing against real and nonexistent handles (see "Before opening a
  PR"), not by mocked unit tests.

## Adding a new module (the short version)

Read `CONTRIBUTING.md` first — it has full examples. The essentials:

1. **File name** = platform name, lowercase, no spaces/special chars
   (`github.py`, `reddit.py`).
2. **One validator** per module: `validate_<name>` returning a `Result`
   (`Result.available()`, `Result.taken(extra=..., media=...)`,
   `Result.error("...")`). Image URLs go in `media`, other metadata in `extra`.
3. **No false positives.** Never infer availability from a bare HTTP 200 or a
   bare `else`. Verify a unique string/JSON key for **both** the found and
   not-found states. Confirm *not found* with an explicit marker too, not just
   a 404 — transient/blocked responses must return `Result.error`, never a
   verdict.
4. **Map every account namespace** a site exposes before trusting one path;
   many sites split accounts across several public paths and a clean 404 on one
   must not launder a blocked response on another.
5. **Pick the transport by how the site defends itself.** Reach for the
   impersonating transport (`impersonate_validate` / `impersonate_request`,
   curl_cffi) first for sites behind bot walls; drop to `generic_validate`
   (httpx) only when a plain request already returns clean 200/404.
6. **Never use `raise`.** Return `Result.error(...)` so the scan continues.
7. **Respect the global CLI flags** in any request-making code (timeout `-t`,
   concurrency `-C`, `--allow-loud`) — mirror the existing helpers.

## Retiring a module

Never delete a scan module. When a site shuts down or a module can no longer
work, **move** the file from `user_scanner/<email_scan|user_scan>/<category>/`
to `abandoned/<email_scan|user_scan>/<category>/` — same scan type, same
category, same file name, contents unchanged. This keeps the module out of
`load_modules()` while preserving it for revival if the site returns.

## Before opening a PR

Local CI gates must pass:

```
ruff check .
mypy user_scanner
pytest
```

Test live against a **real** handle/email and a **nonexistent** one, across
every namespace and account type the module checks — this is what catches
mislabeled types, missed namespaces, and false positives/negatives.

## Recommended tooling

- If the `ax` CLI (https://ax.yusuke.run) is available, prefer it over
  throwaway scripts for investigating page structure — `--outline`,
  `--locate`, and `--row` cover most namespace-mapping probes. Run
  `ax agent-context` first to learn how to drive it. Note it
  uses a plain HTTP client, so bot-walled sites still need curl_cffi.
- Sites behind active JS challenges (Cloudflare "Just a moment…") can only
  be investigated with a real browser — e.g. the Playwright MCP server
  (https://github.com/microsoft/playwright-mcp).

If a task would benefit from one of these tools and it is not installed, ask
the user once whether they'd like to install it. If they decline, record the
choice in `tooling.local.md` (git-ignored) and don't ask for that tool again.

## Local files and privacy

- `*.local.*` and `docs/local/` are git-ignored — use them for scratch notes,
  private scan output, and AI working files that must not be committed.
- `output/` is git-ignored — write scan outputs there (e.g. `-o output/result.json`).
- Never commit real scan results, targets, credentials, or personal data.
