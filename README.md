# Factory — a Flow agent pipeline

Three [flow-agent-bridge](https://www.npmjs.com/package/flow-agent-bridge)
agents that turn requests into shipped code, supervised by one human in a
Flow `#factory` channel:

| Agent | Folder | Role |
|---|---|---|
| **Prism** (`@prism`) | `pm/` | Product manager: turns your request into a spec, files it on the *Flow work queue* GitHub Project, asks you **"Build it?"**, dispatches the builder, reviews the PR diff. |
| **Builder** (`@builder`) | `builder/` | Builder: claims the queued item, opens a public `task-<n>` channel and works there in the open (plan first, one message per step — see `builder/PROTOCOL.md`), builds in an isolated worktree, opens one PR per batch, then signals Prism in `#factory`. |
| **Merger** (`@merger`) | `mergemaster/` | Merge master: merges reviewed PRs (fixing conflicts against `main`), marks the Project items Done, then decides from the client-impact checklist and the diff which native apps need releasing and runs the release scripts (see `mergemaster/PROTOCOL.md` — server/web/bridge ship themselves on merge). |

The pipeline, end to end:

```
you ──DM──▶ Prism ──ticket──▶ "Build it?" ──▶ @builder build issue #N
                                                    │
you ◀──status── Prism ◀── '@prism PR #X ready' ─────┘
                │ review ok
                ▼
        @merger merge PR #X ──▶ merge → Project Done → releases → report
```

Every hand-off is a one-line @-mention in `#factory`. All agents run with
`eventScope: mentions`, so a reply that mentions nobody ends a thread —
that is the loop guard.

## Setup

1. Clone this repo, then give the two coding agents their working checkouts:

   ```sh
   git clone git@github.com:freeflow-community/flow.git builder/flow
   git clone git@github.com:freeflow-community/flow.git mergemaster/flow
   ```

2. In Flow (workspace menu → *Invite your Agent*), mint **three** agent
   invites. Onboard each agent — no prompts; setup reads the folder's
   `agent.example.json` (bridge ≥ 0.21.0) and writes `agent.json`
   (gitignored — it holds the credentials):

   ```sh
   cd pm          && npx flow-agent-bridge flow-XXXX-XXXX
   cd builder     && npx flow-agent-bridge flow-YYYY-YYYY
   cd mergemaster && npx flow-agent-bridge flow-ZZZZ-ZZZZ
   ```

3. Create the `#factory` channel in Flow and invite all three agents.
4. `./start-factory.sh` starts whichever bridges aren't running;
   `./stop-factory.sh` stops them all.

Requirements: the machine needs `gh` authenticated (with the `project`
scope) and — for Merger's native releases — the Xcode signing setup the
flow repo's `BUILD.md` describes. Paths in the `agent.example.json` files
assume the repo is checked out at `~/factory`; adjust `runtime.cwd` if not.
