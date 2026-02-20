# PR #184 Integration: Pattern Expansion Feature

This branch integrates the **Patterns** feature from [PR #184](https://github.com/kaifcodec/user-scanner/pull/184) (by VamatoHD) with additional testing, documentation, and code-quality improvements.

## Summary

Replaces the legacy `generate_permutations` / `-p, --permute` system with inline pattern syntax.

### Pattern syntax

- `[chars]` — single character from set (e.g. `[a-z]`, `[0-9]`, `[abc]`)
- `[chars]{n}` — exactly n characters
- `[chars]{n-m}` — n to m characters
- `[chars]{n;m}` — discrete lengths n and m
- Escaping: `\[`, `\]`, `\\` for literals

### Examples

```bash
user-scanner -u "john[0-9]" -m github           # john0..john9
user-scanner -u "user[0-9]{1-2}" -s 50          # limit to 50 expansions
user-scanner -e "test[ab]@mail.com" -m github  # emails with pattern
user-scanner -u "id[0-9]{2}" -r                # random order (-r)
```

### Changes

1. **`user_scanner/core/patterns.py`** — New module with lexer/parser and `expand_patterns` / `expand_patterns_random`
2. **`user_scanner/__main__.py`** — Uses pattern expansion for all targets; removed `-p/--permute`; added `-r/--random`
3. **`user_scanner/core/helpers.py`** — Removed `generate_permutations`
4. **`tests/test_patterns.py`** — 15 new tests
5. **Docs** — README, FLAGS.md updated

## Contributing to kaifcodec/user-scanner

To open a PR to the original repo:

1. Ensure your fork is up to date:
   ```bash
   git remote add upstream https://github.com/kaifcodec/user-scanner.git  # if not already
   git fetch upstream
   git rebase upstream/main  # or merge
   ```

2. Push your branch:
   ```bash
   git push -u origin cursor/pr-184-integration-9f55
   ```

3. Open a PR at https://github.com/kaifcodec/user-scanner/compare with base `main` and your branch.
   - Reference original PR: "Integrates and completes PR #184 (Patterns feature)"
   - Link: https://github.com/kaifcodec/user-scanner/pull/184

4. If offering as a patch for someone else to apply:
   - `git format-patch upstream/main..HEAD` creates patch files
   - Or share the branch and they can cherry-pick/merge

## Verification

- [x] All 79 tests pass
- [x] Ruff lint passes
- [x] Mypy passes (with types-colorama)
- [x] Backward compatible: plain usernames/emails work unchanged
- [x] File-based scanning supports patterns in each line
