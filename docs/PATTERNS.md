# Pattern Syntax Guide

The pattern system allows you to generate multiple username or email variations from a single compact pattern definition. This is useful for searching variations of a username/email similar to your desire.

## Quick Start

Use patterns directly with the `-u` (username) or `-e` (email) flags:

```bash
# Scan "johna", "johnb", "johnc"
user-scanner -u "john[a-c]"

# Scan up to 50 permutations instead of default 100
user-scanner -u "john[0-9]{0-2}" -s 50

# Scan multiple variations with case differences
user-scanner -u "[jJ]ohn[0-9]{1-2}"

# With emails
user-scanner -e "user[a-z]{0-1}@example.com"
```

The `-s` flag (short for `--stop`) limits how many permutations are scanned. By default, only the first 100 are checked.

## Pattern Syntax

### Character Sets: `[chars]`

Define a character set using square brackets. Characters between the brackets will each become a separate variation.

**Examples:**

```
john[abc]         → "johna", "johnb", "johnc"
user[0-9]         → "user0", "user1", ..., "user9"
test[a-zA-Z]      → "testa", "testb", ..., "testZ"
site[_.-]         → "site_", "site.", "site-"
```

**Character Range Syntax:**

- `[a-z]` - lowercase letters a through z
- `[A-Z]` - uppercase letters A through Z
- `[0-9]` - digits 0 through 9
- `[a-zA-Z0-9]` - combined ranges
- `[abc]` - literal characters a, b, c

**Note**: "-" must be placed at the beginning or at the end of the range to be interpreted as a character.

### Length Control: `[chars]{len}`

Specify the length of expansions from a character set.

**Examples:**

```
john[a-z]{0-2}    → "john", "johna", "johnb", ..., "johnz", "johnaa", ..., "johnzz"
code[0-9]{2}      → "code00", "code01", ..., "code99"
user[a-c]{1;3}    → "usera", "userb", "userc", "useraa", ..., "userccc"
text[0-1]{1-3}    → "text0", "text1", "text00", "text01", "text10", "text11", ..., "text111"
```

**Length Syntax:**

- `{n}` - exactly n characters
- `{n-m}` - between n and m characters (inclusive)
- `{n;m}` - exactly n or m characters
- `{0-n}` - zero to n characters

## Common Use Cases

### Username Variations with Numbers

```bash
user-scanner -u "john[0-9]{0-3}"
```

Scans up to 100 variations: `john`, `john0`–`john9`, `john00`–`john99`, `john000`–`john999`

### Multiple Name Parts with Case Variations

```bash
user-scanner -u "[jJ]ohn[0-9]{0-2}"
```

Scans variations like: `john`, `John`, `john0`–`john99`, `John0`–`John99`

### Underscore and Dot Variations

```bash
user-scanner -u "user[_.]name"
```

Scans: `user_name`, `user.name`

### Email with Variations

```bash
user-scanner -e "user[a-z]{0-1}@example.com"
```

Scans email addresses: `user@example.com`, `usera@example.com`–`userz@example.com`

### Limiting Scan Results

Use the `-s` or `--stop` flag to limit how many permutations are checked:

```bash
# Check only 10 permutations instead of default 100
user-scanner -u "john[0-9]{0-3}" -s 10
```

The tool will show you how many permutations are available:

```
[+] Scanning 10 of 1111 permutations
```

### Viewing Available Permutations

The tool automatically shows how many variations were found and scans up to the limit you set.

## Performance Tips

1. **Start with limits** - Always use `-s` to limit how many permutations you scan:

   ```bash
   user-scanner -u "pattern[0-9]{0-3}" -s 25
   ```

2. **Check pattern complexity** - A pattern like `[a-z]{5}` would generate 11,881,376 combinations. Start small and increase gradually.

3. **Use moderate ranges** - Keep character sets and length ranges reasonable:
   - Good: `[a-c]{0-2}` (~15 variations)
   - Risky: `[a-z]{0-3}` (~18,278 variations)

4. **Combine with other filters** - Use `-c` (category) or `-m` (module) to narrow the scope:

   ```bash
   user-scanner -u "user[a-z]{0-1}" -c social -s 50
   ```

5. **Add delays between requests** - Use the `--delay` flag to avoid rate limiting:
   ```bash
   user-scanner -u "test[0-9]{1-2}" --delay 1.0
   ```

## CLI Examples

### Simple usernames with numbers

```bash
user-scanner -u "johnny[0-9]{0-2}"
```

### Case variations

```bash
user-scanner -u "[jJ]ohn[0-9]{1-2}"
```

### Multiple separators

```bash
user-scanner -u "john[._-]doe"
```

### Complex pattern with limited scans

```bash
user-scanner -u "user[a-z]{0-1}[0-9]{0-2}" -s 50
```

### Email pattern variations

```bash
user-scanner -e "[jJ]ohn[_.]doe@example.com"
```

### Combining with other flags

```bash
# Scan a pattern with verbose output and delay between requests
user-scanner -u "admin[0-9]{1-2}" -v --delay 0.5 -s 25

# Scan with a specific category
user-scanner -u "user[a-c]" -c social -s 50
```

## Pattern Limitations

- Do not nest brackets: `[[a-z]]` is invalid
- Ranges must go from lower to higher ASCII values (e.g., `[z-a]` is invalid)
- The pattern engine is designed for generating variations, not complex regex-like patterns
