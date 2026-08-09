# Cross-scan

An email scan answers *does an account exist here*. It almost never learns the
account's **name**, so it can only ever reach the sites that expose an email
check. A username scan reaches far more sites, but needs a handle to start from.

`--cross-scan` bridges the two: it runs the email scan, mines the metadata the
results carry for usernames, and scans those usernames across every username
module.

```
user-scanner -e target@example.com --cross-scan
```

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

### What confidence does not do

- **A `candidate` is not a negative.** Most hits land there simply because the
  site exposes no metadata to judge — `Roblox`, `Scratch` and `Px500` return a
  handle and little else.
- **Location is not used.** "Brazil" fits millions of people, and people move,
  so a location match would promote hits it cannot justify.
- **Nothing is dropped.** Every hit reaches the export whatever its rating.

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

A sweep runs **every** username module, so each swept username costs roughly one
full `-u` scan. `--cross-sweep` is that budget: it caps how many usernames get
the treatment (default 3) **across all rounds**, and `0` turns sweeping off
altogether. Raising `--cross-depth` never multiplies the bill on its own — a
deeper run with the default budget spends it in round 1 and reaches later rounds
with named checks only. Raise both together.

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

Cross-scan hits carry `pivot_source` (why the username was scanned) and
`confidence` (how well the account is tied to the target):

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

- Email mode only — `--cross-scan` with `-u` is an error, since a username scan
  is already the thing a cross-scan pivots *into*.
- Link shorteners are dead ends. `t.co/abc123` yields no pivot, and the redirect
  is never followed, so whatever it points at stays invisible at any depth.
- A pivot is a lead, not proof of identity. A link on a profile says the profile
  owner pointed at that account, and `verified` says the platform checked it —
  neither says the two accounts belong to the same person in every case.
- Confidence is a triage aid, not a verdict. It reads only the metadata a module
  happened to extract, so it cannot rate a site that exposes none.
