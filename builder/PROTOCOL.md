# Builder protocol

Adapted from the flow repo's `.claude/skills/work-project-tasks/SKILL.md` for
the factory: no queue discovery (Prism dispatches one named issue or batch),
no cross-machine lock (one Builder, one machine), and the finish signal goes
back to `#factory` so Prism can review.

## On dispatch (`@builder build issue #N` / `batch <b>` in #factory)

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
   the #factory channel id as `sourceChannelId`, and who dispatched it.
5. **Ack.** Reply one line in #factory and end the turn:
   `Working issue #N in #task-N — I'll ping @prism when the PR is up.`
   Do not do the work in the #factory conversation. If `start_task` is
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
- **Fresh worktree, never the main checkout:**
  `git fetch origin && git worktree add -b fix/issue-<n>-<slug> ../flow-wt-<slug> origin/main && cd ../flow-wt-<slug> && pnpm install`
- **Follow the repo's `CLAUDE.md`** — it is the contract and it outranks any
  older skill text. The rules that bite: one new `changelog/` entry file
  (with a `## Feature` section when user-visible), a Parity line in
  `CHANGELOG.md` for single-client changes, and **never bump native version
  files** (`apps/macos/VERSION`, `CURRENT_PROJECT_VERSION`) — releasing is
  Merger's job, after merge.
- **Verify for real.** `pnpm test`, `pnpm -r build`, then look at the change
  running: web via a headless/kernel browser or the local server, iOS via the
  simulator. This is Scott's own Mac, not a dedicated agent machine — the
  UI-automation gate in the QA manual applies: do not take over the desktop
  (macOS app driving, `screencapture` of the screen) without asking in the
  task channel first. Simulator and headless-browser evidence needs no
  permission. Capture screenshots for the PR where UI changed.
- **Put the machine back.** Stop the dev server, app builds, and simulator
  you started — match kills on your own worktree path, never a bare
  `pkill -f Flow`. What was already running is not yours to stop.
- **One PR for the batch:** `Closes #<n>` per issue, screenshots, the
  client-impact checklist, and the task channel named in the body; the PR
  link posted in the channel. Never push to `main`.
- **Signal Prism.** When the PR is open, `send_message` to the #factory
  channel (`sourceChannelId` from the brief), exactly one line:
  `@prism PR #<pr> ready for review (issue #<n>) — log in #task-<n>`.
  Review changes requested later come back as a #factory mention; fix on the
  same branch and signal the same way again.
- **Done or Blocked, never limbo.** After the PR is open, leave the items
  `In Progress` (Merger sets Done on merge). If you cannot finish: set the
  whole batch `Blocked` (set-status.sh), comment the one-line reason plus
  what you need on every issue, post it in the task channel, and
  `send_message` #factory: `@prism blocked on issue #<n>: <reason>`. Never
  re-queue blocked work; a human does that.
