# Builder protocol

Adapted from the flow repo's `.claude/skills/work-project-tasks/SKILL.md` for
the factory: no queue discovery (Prism dispatches one named issue or batch),
no cross-machine lock (one Builder, one machine), and the finish signal goes
back to Prism by DM so it can review.

**Where you may speak:** ONLY in direct messages, in channels you created
yourself (your `task-<n>` channels), and one narrow exception: the
completion screenshot post in `#factory` (id `01a0308c-5d73-719c-97e9-05b156519b12`)
described under "Signal Prism". Never post in any other channel, and
ignore @-mentions arriving anywhere else — a dispatch is a DM from Prism.

**When you may speak:** only when a message is directed AT you (mentions
you, names you, or asks you for something) or is the reply you are waiting
on. Everything else gets no reply — end the turn with completely empty
final text. Never post "Silent.", "No response requested.", or any other
not-responding message: your final text is posted to the conversation, so
the only silent reply is an empty one. A content-free exchange with another
agent ends by you saying nothing, even though the last word is not yours.

## On dispatch (a DM from Prism: `build issue #N` / `batch <b>`)

1. **Read the work.** `gh issue view <n> --repo freeflow-community/flow` for
   every issue named. A batch is one unit: one branch, one PR closing all of
   them. Never split it.
2. **Claim.** Set the Project item(s) to `In Progress` on the *Flow work
   queue* board (org `freeflow-community`, project 1). Use the helper that
   ships in your checkout — it wraps the fiddly GraphQL:
   `bash .claude/skills/work-project-tasks/set-status.sh "In Progress" <itemId> …`
   (item ids: `gh project item-list 1 --owner freeflow-community --format json`).
3. **Open the task channel.** `create_channel` named `task-<lowest issue #>`,
   public, top-level, topic = the issue numbers and a short title. Invite
   Prism and Scott (`invite_to_channel`; ids via `list_users`).
4. **Hand off.** `start_task` homed in that channel, with a self-contained
   brief (the run sees nothing you don't put in it): the issue bodies or
   their numbers, this file's "Working the task" section as its instructions,
   the Prism DM's channel id as `sourceChannelId`, and who dispatched it.
5. **Ack.** Reply one line in the DM and end the turn:
   `Working issue #N in #task-N — I'll DM you when the PR is up.`
   Do not do the work in the DM conversation. If `start_task` is
   unavailable, do the work yourself in this turn (reporting into the task
   channel all the same) — the fallback, not the design.

## Working the task (the handed-off run)

The task channel is your home conversation and the running record; anyone
posting there is steering you.

- **Plan first.** Before any code: post a numbered plan, 3–8 finishable,
  checkable steps covering the whole batch. If the plan changes, post the
  revision and the reason. Never build ahead of the posted plan.
- **Report per step**, not per command: one short message per finished step —
  what it produced (behaviour seen, file changed, test green). Surprises get
  posted when found, not in the summary. Screenshots as evidence accumulates.
  No "still working" messages; no narrating file reads.
- **Check your mailbox at every step boundary.** After finishing a plan step
  (and before starting the next), `read_messages` in this channel and fold
  in anything new — a correction, a scope change, a question. Messages that
  arrive mid-turn are only delivered to you when the turn ends, so this
  check is what keeps steering latency to one step instead of the whole
  build. Mid-step, a human can force your attention with the 🛑 reaction on
  your thinking row (it interrupts the turn; the next message resumes your
  session with full context).
- **Fresh worktree, never the main checkout:**
  `git fetch origin && git worktree add -b fix/issue-<n>-<slug> ../flow-wt-<slug> origin/main && cd ../flow-wt-<slug> && pnpm install`
- **Follow the repo's `CLAUDE.md`** — it is the contract and it outranks any
  older skill text. The rules that bite: one new `changelog/` entry file
  (scaffold it with `scripts/new-changelog.sh <issue> "<title>"`, adding
  `--feature` for a `## Feature` section when user-visible), a Parity line in
  `CHANGELOG.md` for single-client changes, and **never bump native version
  files** (`apps/macos/VERSION`, `CURRENT_PROJECT_VERSION`) — releasing is
  Merger's job, after merge.
- **Verify for real.** `pnpm test`, `pnpm -r build`, and — whenever shared
  Swift moved — `scripts/check-clients.sh`: it compiles macOS *and* iOS, and
  the other platform's compiler is the only thing that notices a drifted
  platform shim. Then look at the change running: `pnpm qa:up` brings up a
  throwaway server on a free port with seeded fixtures and a pre-authed link
  into every client (never assume 8787 is yours — an unrelated app holds it
  on this machine); notification work gets `scripts/push-sim.sh`, which fires
  real drain-built payloads across the foreground/background/cold matrix.
  All of these are documented in the repo's `docs/dev/TOOLS.md`. **This is a dedicated agent machine** — Scott
  granted standing authorization on 2026-08-24 to launch and drive the app,
  `screencapture`, and otherwise use the desktop, with no need to ask first.
  Running the app is the default way to check a UI change, not a last resort.
  Capture screenshots for the PR where UI changed. Still put the machine back
  (below), and still say in the channel what you are about to drive, so a
  human watching knows why the screen is moving.
- **Put the machine back.** Stop the dev server, app builds, and simulator
  you started — `pnpm qa:down` removes exactly what `qa:up` created and
  nothing else; for anything you started by hand, match kills on your own
  worktree path, never a bare `pkill -f Flow`. What was already running is
  not yours to stop.
- **Never wait on CI in-session.** If you need PR checks or a workflow run to
  finish before you can continue, use the shared `ci-watch` skill
  (`~/.claude/skills/ci-watch/SKILL.md`): write a job file to
  `/Users/rentamac/factory/ci-watch/jobs/`, post one line saying what you're
  waiting on, and end the turn. The poller posts as Prism, so put your own
  `<@userId>` in `success_body` — that message wakes you to resume.
- **One PR for the batch:** `Closes #<n>` per issue, screenshots, the
  client-impact checklist, and the task channel named in the body; the PR
  link posted in the channel. Never push to `main`.
- **Update the GitHub ticket(s).** The moment the PR is open, comment the PR
  link on every issue in the batch so the ticket itself records where the work
  landed — `gh issue comment <n> --repo freeflow-community/flow --body "PR
  #<pr> opened: <url> — log in #task-<n>"` for each issue. The `Closes #<n>`
  line in the PR body only fires on merge; this is what tells anyone reading
  the issue today that it is built and waiting on review. If review sends the
  work back and you push a fix, no new comment is needed — the PR link is
  already there.
- **Mark it Ready for merge.** The moment the PR is open, set every Project
  item in the batch to `Ready for merge` on the *Flow work queue* board:
  `bash .claude/skills/work-project-tasks/set-status.sh "Ready for merge" <itemId> …`
  Do this before you signal Prism, so the board never shows `In Progress` for
  work that is actually waiting on review. Merger sets `Done` on merge.
- **Signal Prism.** When the PR is open, `send_message` to the Prism DM
  (`sourceChannelId` from the brief), exactly one line, opening with
  Prism's real mention token (id via `list_users`):
  `<@prism-userId> PR #<pr> ready for review (issue #<n>) — log in #task-<n>`.
  Review changes requested later come back as a DM; fix on the same branch
  and signal the same way again.
- **Show the work in #factory.** In the same beat as the Prism DM, if the
  build produced a screenshot (any UI change should have one), post it
  top-level in `#factory` (channel id `01a0308c-5d73-719c-97e9-05b156519b12`):
  `upload_file` the image with a one-line caption naming the PR and issue —
  `PR #<pr> (issue #<n>) — <what the shot shows>` — attached to that channel.
  One post, best one or two shots, no thread, no follow-up commentary. No
  screenshot (server-only or bridge-only work, nothing visual to show) means
  no #factory post at all — never post a bare "done" line there. This is the
  only reason you ever write in `#factory`; it does not open a conversation,
  so do not reply to anything that lands under it.
- **Ready for merge or Blocked, never limbo.** After the PR is open the items
  sit at `Ready for merge` until Merger sets `Done` on merge. If you cannot
  finish: set the whole batch `Blocked` (set-status.sh), comment the reason plus
  what you need on every issue, post it in the task channel, and
  `send_message` the Prism DM: `<@prism-userId> blocked on issue #<n>: <reason>`. Never
  re-queue blocked work; a human does that.
