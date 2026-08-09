# Cross-scan

An email scan answers *does an account exist here*. It almost never learns the
account's **name**, so it can only ever reach the sites that expose an email
check. A username scan reaches far more sites, but needs a handle to start from.

`--cross-scan` bridges the two: it runs the scan, mines the metadata the results
carry for usernames **and email addresses**, and scans each against the modules
for its own kind.

```
user-scanner -e target@example.com --cross-scan
user-scanner -u target --cross-scan
```

Either pass can be the source as well as the destination, so all four directions
work off one mechanism:

| Direction | What it mines |
| --- | --- |
| `-e` → username | a handle the email's profile reports, or a link it carries |
| `-u` → username | the person's *other* handles, advertised on the profiles found |
| `-u` → email | an address published on a profile the username pass found |
| `-e` → email | a second address exposed by the first one's profiles |

A pass's own target starts out excluded — a `-u` handle as already swept, a `-e`
address as already scanned — since that pass ran every module against it.

---

## Where pivots come from

Two shapes of metadata carry a username:

| Shape | Example | Becomes |
| --- | --- | --- |
| A handle the site reports for the email | Gravatar `username: johndoe` | username `johndoe` |
| A link on the profile | `https://github.com/johndoe` | username `johndoe`, site `github` |

Links resolve to a `(site, username)` pair through a route table in
`user_scanner/core/pivots.py` — hosts, path shapes (`/in/{user}`,
`/users/{id}/{user}`, `/@{user}`) and `{user}.host` subdomains. A link to a root
domain with no path (`https://johndoe.com/`) yields the domain label as a
username with no particular site attached.

A link whose path names a site page rather than a person
(`github.com/settings`, `youtube.com/channel/UC…`) yields nothing — an ID is not
a handle, and a reserved word is not a person.

---

## Link classes

Pivots are classified by how much the source platform vouches for them:

| Class | Meaning | Example |
| --- | --- | --- |
| `handle` | The site itself reported this account's name for the scanned email | Gravatar's `username` |
| `verified` | The owner proved control of the far side — OAuth connection or a `rel="me"` round-trip | Gravatar's `verified_accounts` |
| `link` | Free text the owner typed into their profile | Gravatar's `links`, `websites`, `bio` |

`--cross-links` picks which classes may be pivoted from:

| Value | Uses |
| --- | --- |
| `all` (default) | every class |
| `verified` | `handle` + `verified` — nothing the owner could have typed |
| `none` | `handle` only |

`verified` is the setting to reach for when a false link would be costly: anyone
can paste someone else's URL into their own bio, but they cannot complete the
platform's verification handshake for an account they do not control.

---

## Email classes

Addresses are classified the same way, by how the source presented them:

| Class | Meaning | Example |
| --- | --- | --- |
| `field` | The site published it in its own email field for the account | GitHub's `email`, Gravatar's `emails` |
| `text` | An address read out of prose, where nothing says whose mailbox it is | an address inside a `bio` |

`--cross-emails` picks which may be scanned:

| Value | Uses |
| --- | --- |
| `all` | both classes |
| `verified` (default) | `field` only |
| `none` | nothing — no address is scanned |

It defaults tighter than `--cross-links` because the cost of being wrong is not
symmetric. A stray username pivot wastes a request; a stray address puts a third
party into the report, and hands their mailbox to modules that can write to it.

Two traps this classification exists to avoid:

- **An email field is not a guarantee of ownership.** `verified` says the site
  published the address, not that the site was right about whose it is. PyPI
  fills its `email` from a package's author/maintainer metadata, so a hit there
  can carry a co-maintainer's address or a mailing list. Keys that name the
  third party outright (`author_email`, `maintainer_email`) are read as `text`,
  but a module that folds them into `email` defeats that.
- **Some addresses reach nobody.** Role mailboxes (`noreply@`, `postmaster@`),
  RFC 2606 placeholders (`@example.com`), reserved TLDs and GitHub's
  `@users.noreply.github.com` relay are dropped outright. `hello@` and
  `contact@` are *not* — that is how a freelancer takes mail.

`none` means none, unlike its `--cross-links` namesake, which still yields
handle pivots. A handle is not a link; every email class is an address.

---

## The sweep, and why hits are not equal

Two very different things produce a hit:

| | What it proves |
| --- | --- |
| **Named check** — a pivot gave the site *and* the handle (`github.com/johndoe`) | The target's own profile pointed here |
| **Sweep** — the handle tried on every other module | The handle is registered there, by *anyone* |

A common handle collides. One sweep of a plausible handle turned up five
different people alongside the real owner — so a sweep hit is a lead, not an
identification.

`--cross-sweep 0` turns the sweep off and runs only the named checks. Far fewer
accounts, zero collisions.

### Usernames and addresses share the budget

`--cross-sweep` counts *targets*, not usernames: sweeping either kind costs one
full pass over its scan type (227 username modules, 153 email ones). Half the
budget is offered to addresses, rounded down, and whatever one kind cannot use
falls to the other:

| Budget | Usernames available | Addresses available | Spent on |
| --- | --- | --- | --- |
| 3 | 5 | 2 | 2 usernames, 1 address |
| 3 | 0 | 2 | 2 addresses |
| 3 | 5 | 0 | 3 usernames |
| 1 | 2 | 2 | 1 username |

A budget of 1 still goes to a username, which is what it did before addresses
existed. `--cross-sweep 0` leaves only named checks, so no address is scanned —
an address has no named-site equivalent to fall back on.

---

## Confidence

Every hit is rated, and the rating is written to `extra.confidence`:

| Rating | Meaning |
| --- | --- |
| `confirmed` | A pivot named this exact site and handle |
| `likely` | Metadata matches the confirmed profiles |
| `candidate` | The handle is registered; nothing ties it to the target |
| `conflicting` | Metadata names someone else |

`likely` and `conflicting` are decided against **anchors** — the names, personal
domains, e-mail addresses, profile URLs and confirmed *accounts* harvested from
the `confirmed` hits. A hit that echoes an anchor is promoted; a hit whose name
field reads as a different person's name is demoted.

The strongest of those signals is a link **to a confirmed account**. If X is
confirmed and a swept Twitch profile links that same X account, the Twitch
account is `likely` — someone else holding the handle would not advertise the
target's Twitter. Matching is on the resolved `(site, handle)` pair rather than
the URL text, so a renamed host or a different casing still lands:
`twitter.com/JohnDoe2` and `x.com/johndoe2` both resolve to `("x", "johndoe2")`.

Links are read from **every** field a module emits, not a fixed list of text
keys — sites split them across `bio`, `website`, `showcased_links`, or one key
per platform, and a Linktree that lists three confirmed accounts should not go
unrated because its field happens to be named something new.

Two rules keep the demotion honest. A name that merely restates the handle
(`john.d.oe`, `JohnDoe`) is an echo of the search rather than evidence, so it is
ignored. And a field that packs a descriptor around the name (some sites
render one as `Other Person, 44, male`) is read up to its first comma, so the
rest is not mistaken for a mismatch.

Scoring runs after the pass finishes, because the anchors come from that same
pass's confirmed hits. Ratings therefore appear in the export and the closing
summary, not on the per-result lines as they stream past.

### Addresses are rated before they are scanned

An address is rated on how independently it was reported, and the accounts it
finds inherit that rating — an account is only as well tied to the target as the
address that led to it:

| Rating | Earned by |
| --- | --- |
| `confirmed` | two or more sites published it in their own email field |
| `likely` | one site published it in an email field, or it sits on a domain the target links to |
| `candidate` | prose only, with nothing tying it back |

Independent agreement is the strongest signal available without sending mail, so
it outranks a single site saying it once. `conflicting` is never used: an
address carries no name to disagree with, and inferring a mismatch from the
local part would mislabel every shared mailbox.

The rating deliberately ignores the anchor *emails* and *domains* — those are
harvested from the very profiles being rated, so consulting them would promote
every address on the strength of its own appearance. Only domains the target was
seen to **link** to count.

### What confidence does not do

- **A `candidate` is not a negative.** Most hits land there simply because the
  site exposes no metadata to judge — `Roblox`, `Scratch` and `Px500` return a
  handle and little else.
- **Location is not used.** "Brazil" fits millions of people, and people move,
  so a location match would promote hits it cannot justify.
- **Nothing is dropped.** Every hit reaches the export whatever its rating.

---

## Scope

`-m` and `-c` narrow the cross-scan exactly as they narrow the first pass, so a
restricted run stays restricted:

```
-u johndoe -m gravatar --cross-scan     # 1 module in the first pass, 1 in the sweep
-u johndoe -c dev --cross-scan          # 44 dev modules in both
```

Both the sweep and the named checks honour it, so a pivot naming a site outside
the restriction is not checked either. Names are re-resolved against `user_scan`,
because an email run's `-m` names *email* modules while the sweep needs the
username module of the same site.

Addresses resolve the same name against `email_scan`, so `-m github` narrows the
sweep to `user_scan/dev/github.py` and any address scan to
`email_scan/dev/github.py`. Only a restriction that names **neither** a username
nor an email module leaves nothing to cross-scan, and the run says so.

### Loud modules are skipped, not prompted

23 email modules notify the address they are given — a password reset or a
verification mail. In a first pass that address is the one you typed, so
`--allow-loud` and a per-module prompt are the right bar. In a cross-scan it
came off somebody else's profile, so those modules are dropped without asking.
`--allow-loud` puts them back for a caller who has accepted that.

---

## Depth: following a chain of links

`--cross-depth N` runs N rounds. Each round pivots off the accounts the previous
one found, so a handle that only appears deep in a chain is still reached:

```
Gravatar --verified--> Dev.to --website--> somebrand.com  ->  handle "somebrand"
```

Round 1 never sees that handle: Gravatar does not link Dev.to, and `somebrand`
appears nowhere in the email results. Only a second round reaches it.

Breadth and depth are separate axes, so they combine:

| | `--cross-sweep N` (default 3) | `--cross-sweep 0` |
| --- | --- | --- |
| `--cross-depth 1` | every module × the top handles | only the sites links named |
| `--cross-depth 2` | the above, plus handles found one hop deeper | follow links two hops, still never guessing |

`--cross-sweep 0 --cross-depth 2` is the cheap, high-precision mode: it walks
the link graph without ever trying a handle on a site nothing pointed at, so it
cannot produce a collision.

Two rules keep extra rounds from wandering:

- **Nothing is scanned twice.** A swept username has already had every module run
  against it, so it is never revisited; a named site+handle pair is retired once
  checked.
- **A `conflicting` account is not followed.** Its metadata names someone else,
  so its links lead into a stranger's footprint rather than the target's.

---

## Cost

A sweep runs **every** module of its kind, so each swept username costs roughly
one full `-u` scan and each scanned address roughly one full `-e` scan.
`--cross-sweep` is that shared budget: it caps how many targets get the
treatment (default 3) **across all rounds and both kinds**, and `0` turns
sweeping off altogether. Raising `--cross-depth` never multiplies the bill on
its own — a deeper run with the default budget spends it in round 1 and reaches
later rounds with named checks only. Raise both together.

Usernames are ranked `handle` → `verified` → `link`, then by how many pivots
mention them. Those past the budget are named in the output rather than dropped
silently, and any pivot that named a specific site is still checked against that
one site — cheap, and it keeps a capped run from missing a confirmed link.

Ranking is by how well a handle is vouched for, not by how useful it looks, so
an opaque platform ID that arrived through a verified link (Spotify hands out
`21jxv335g4w6dikpyyhtlbybq`) can outrank a real handle and spend a sweep on a
string no other site will ever have. Watch the pivot table and raise the cap, or
drop to `--cross-sweep 0`, when a run is full of them.

---

## Reading the output

Cross-scan hits carry `pivot_source` (why the target was scanned) and
`confidence` (how well the account is tied to the target). An account reached
through an address records which profile published it:

```json
{
  "status": "Found",
  "username": "john@acme.dev",
  "site_name": "Spotify",
  "is_email": true,
  "extra": {
    "pivot_source": "address from Github (email), Gravatar (emails)",
    "confidence": "confirmed"
  }
}
```

and one reached through a handle records the pivot class:

```json
{
  "status": "Found",
  "username": "johndoe",
  "site_name": "Github",
  "extra": {
    "pivot_source": "verified from Gravatar (verified_accounts)",
    "confidence": "confirmed"
  }
}
```

The closing summary counts each rating, names the `confirmed`, `likely` and
`conflicting` hits, and lists the sites the second pass reached that the first
pass never did.

---

## Limits

- A username pass (`-u` / `-uf`) can be cross-scanned too. Its own target starts
  out marked as swept, since that pass already ran every module against it and
  most sites report the handle straight back as a pivot.
- Link shorteners are dead ends. `t.co/abc123` yields no pivot, and the redirect
  is never followed, so whatever it points at stays invisible at any depth.
- A pivot is a lead, not proof of identity. A link on a profile says the profile
  owner pointed at that account, and `verified` says the platform checked it —
  neither says the two accounts belong to the same person in every case.
- Confidence is a triage aid, not a verdict. It reads only the metadata a module
  happened to extract, so it cannot rate a site that exposes none.
