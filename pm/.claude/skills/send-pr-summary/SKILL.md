---
name: send-pr-summary
description: Compose a grouped, well-formatted summary of recently merged Flow PRs (last 6, or all from the last 24h if more) with screenshots pulled from task channels, and email it to every non-agent member of #factory.
---

# send-pr-summary

Email a digest of recently merged PRs in `freeflow-community/flow` to the
humans in #factory. Invoking this skill IS the authorization to send — do
not ask for confirmation before sending.

## 1. Pick the PRs

```bash
gh pr list --repo freeflow-community/flow --state merged --limit 30 \
  --json number,title,url,mergedAt,body,author
```

- Count PRs with `mergedAt` within the last 24 hours.
- If that count > 6 → include all of them. Otherwise → the 6 most recently
  merged (regardless of age).
- Order newest-first within the email.

## 2. Collect screenshots

For each PR, find its issue number (PR bodies say `closes #<n>` / the branch
is usually `flow-wt-<n>`). The build log lives in a Flow channel named
`task-<n>`:

- `list_channels` → find `task-<n>`; `read_messages` on it and look for
  `[attachments: <fileId> "name" (image/png, ...)]` lines. Builder also posts
  a final screenshot in #factory with the "PR ready" message — check there
  too (`search_history` for the PR number).
- Prefer the last/most polished screenshot per PR; skip PRs with none
  (server-only or bridge work usually has none — that's fine).
- `download_file` each chosen fileId to a temp path.

Email cannot carry attachments (Cloudflare rejects them — see
[[email-via-cloudflare]]). Host images instead:

```bash
# creds: CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_KEY in /Users/rentamac/flow/.env
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/r2/buckets/flow-public-assets/objects/pr-summary/<YYYY-MM-DD>/pr<number>-<name>.png" \
  -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
  --data-binary @<local-path>
```

Public URL: `https://pub-203a02cf81ea40239d5b867d21e7b535.r2.dev/pr-summary/<YYYY-MM-DD>/<file>.png`

## 3. Compose the email

HTML body (plus a plain-text fallback). Structure:

- Subject: `Flow PR digest — <Mon D>: <n> PRs merged`
- Group PRs by product area (e.g. "Community email", "iOS push", "Web
  client", "Agent bridge") — one `<h2>` per group, infer groups from
  titles/issues; singletons can share a "Miscellaneous" group.
- Each PR: linked `#<number>` + title, then 1–2 plain-English sentences on
  what changed for users (write from the PR body/diff, not just the title),
  then the screenshot as `<img src="..." style="max-width:560px">` if one
  exists.
- Keep it scannable: no walls of text, no internal jargon (worktree names,
  CI details).

## 4. Recipients — non-agent members of #factory

Resolve live from the production API (never hardcode the list). The bridge
token in `/Users/rentamac/factory/pm/agent.json` authenticates:

```bash
python3 - <<'EOF'
import json, urllib.request
cfg = json.load(open('/Users/rentamac/factory/pm/agent.json'))
base, tok = cfg['serverUrl'], cfg.get('agentToken') or cfg.get('agentKey')
def get(p):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        base + p, headers={'Authorization': 'Bearer ' + tok})))
ws = next(w for w in get('/v1/me/workspaces')['workspaces']
          if 'locked' in (w.get('slug') or w.get('name', '')).lower())
chans = get(f"/v1/workspaces/{ws['id']}/channels")
fac = next(c for c in (chans.get('channels') or chans) if c.get('name') == 'factory')
ids = set(get(f"/v1/channels/{fac['id']}/members")['userIds'])
for m in get(f"/v1/workspaces/{ws['id']}/members")['members']:
    if m['userId'] in ids and not m['isAgent']:
        print(m['displayName'] + '\t' + m['email'])
EOF
```

## 5. Send

One POST per recipient (don't put all addresses in one `to` — keeps
addresses private):

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/email/sending/send" \
  -H "Authorization: Bearer $CLOUDFLARE_API_KEY" -H "Content-Type: application/json" \
  -d '{"from":"Free Flow <noreply@mail.freeflow.im>","to":"<email>","subject":"...","text":"...","html":"..."}'
```

`from` MUST be exactly `Free Flow <noreply@mail.freeflow.im>` — the display
name matches the server's community broadcasts (#493); the address must stay
`noreply@mail.freeflow.im`. Body accepts only `text`/`html` — no
attachments/raw/MIME.

## 6. Report

Reply in Flow with a one-liner: how many PRs, how many screenshots, and who
it went to (names, not addresses), plus any send failures.
