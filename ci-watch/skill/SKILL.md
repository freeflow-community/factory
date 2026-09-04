---
name: ci-watch
description: Never wait on GitHub CI inside a session. Drop a watch-job file and end the turn; a launchd poller posts a Flow message (which can mention and wake an agent) when the PR checks or workflow run finish. Use whenever you would otherwise poll `gh pr checks`, `gh run watch`, or sleep until CI is green.
---

# ci-watch — hand a CI wait to the out-of-session poller

In-session waits die with the turn and leave you unresponsive for minutes.
Instead, file a job and END YOUR TURN. A launchd job
(`im.freeflow.factory.ci-watch`, every 120s) runs
`/Users/rentamac/factory/ci-watch/ci-watch.py`, and when the watched checks
are terminal it posts your message to Flow and deletes the job file.

## File a job

Write `/Users/rentamac/factory/ci-watch/jobs/<something-unique>.json`:

```json
{
  "pr": 496,
  "repo": "freeflow-community/flow",
  "success_body": "<@your-userId> PR #496 checks green — resume the merge",
  "fail_body": "<@scott-userId> PR #496 CI failed",
  "channel_id": "01a03cc2-b7d9-76fa-8e33-ae57d46e3662",
  "thread_root_id": "<message id, optional>"
}
```

- Watch a **PR's checks** with `"pr"`, or a **single workflow run** with
  `"run": <run-id>` (e.g. a post-merge run on main) — one of the two, not both.
- `channel_id` defaults to #factory; add `thread_root_id` to reply into the
  thread you're working in (use your dispatch thread, not a new top-level post).
- `success_body` / `fail_body` are markdown; real `<@userId>` mention tokens
  notify. On failure the failing check names are appended automatically.
- Every wait fails loudly: if checks are still pending after
  `"timeout_minutes"` (default 60), the poller posts `fail_body` with a
  deadline note and drops the job — a stuck run strands nobody.
- **Waking rules:** the bridge never wakes an agent on its *own* message. The
  poller posts as **Prism** by default, so Builder/Merger wake themselves by
  mentioning their own `<@userId>` in the body. Prism must instead mention
  whoever acts next (or set `"token_file"` to another agent's
  `/Users/rentamac/factory/<agent>/agent.json` and mention itself).

## After filing

Post one line saying what you're waiting on (e.g. "CI re-running on #496 —
ci-watch will ping when it's terminal"), then end the turn. When the poller's
message wakes you, continue from where you left off.

Log: `/Users/rentamac/factory/ci-watch/ci-watch.log`. A job that errors (e.g.
bad PR number) stays in `jobs/` and logs the error each cycle — check the log
if no ping arrives within ~5 minutes of CI actually finishing.
