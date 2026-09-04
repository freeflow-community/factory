#!/usr/bin/env python3
"""Shared CI watcher for the factory agents (runs from launchd, outside any agent session).

Scans jobs/*.json. Each job watches ONE thing — a PR's checks or a workflow run:
  {
    "pr": 480,                      // watch a PR's checks (this or "run", not both)
    "run": 33817718372,             // watch a single workflow run id
    "repo": "freeflow-community/flow",
    "success_body": "<@merger-id> merge PR #480 (...)",
    "fail_body": "<@scott-id> PR #480 CI failed",
    "channel_id": "...",            // optional; default #factory
    "thread_root_id": "...",        // optional; reply into a thread
    "token_file": "/Users/rentamac/factory/pm/agent.json"  // optional; who posts
  }
When the watched thing is terminal, posts success_body (green) or fail_body +
failing names (red/cancelled), then removes the job file.

The bridge never wakes an agent on its OWN messages: if the message must wake
you, post it with someone else's token (default poster is Prism, so Builder
and Merger can simply mention themselves in the body).
"""
import json, re, subprocess, sys, time, uuid, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
JOBS = BASE / "jobs"
LOCK = BASE / "ci-watch.lock"
SERVER = "https://app.freeflow.im"
FACTORY_CHANNEL = "01a03cc2-b7d9-76fa-8e33-ae57d46e3662"
DEFAULT_TOKEN_FILE = "/Users/rentamac/factory/pm/agent.json"
GH = "/opt/homebrew/bin/gh"


def post(token: str, channel_id: str, body: str, thread_root_id=None) -> None:
    mentions = list(dict.fromkeys(re.findall(r"<@([0-9a-f-]{36})>", body)))
    payload = {"clientMsgId": str(uuid.uuid4()), "body": body[:12000]}
    if thread_root_id:
        payload["threadRootId"] = thread_root_id
    if mentions:
        payload["mentions"] = mentions[:50]
    req = urllib.request.Request(
        f"{SERVER}/v1/channels/{channel_id}/messages",
        data=json.dumps(payload).encode(),
        headers={"authorization": f"Bearer {token}", "content-type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=30).read()


def check_pr(repo: str, pr: int):
    """Returns (done: bool, failed: [names]). Raises on gh errors."""
    out = subprocess.run(
        [GH, "pr", "checks", str(pr), "-R", repo, "--json", "name,bucket"],
        capture_output=True, text=True, timeout=60,
    )
    # gh exits 8 while checks are pending, 1 if some failed — both still emit JSON
    checks = json.loads(out.stdout) if out.stdout.strip() else None
    if checks is None:
        raise RuntimeError(f"gh pr checks gave no JSON: {out.stderr.strip()[:200]}")
    if any(c["bucket"] == "pending" for c in checks):
        return False, []
    return True, [c["name"] for c in checks if c["bucket"] in ("fail", "cancel")]


def check_run(repo: str, run: int):
    """Returns (done: bool, failed: [names]) for a single workflow run."""
    out = subprocess.run(
        [GH, "run", "view", str(run), "-R", repo, "--json", "status,conclusion,workflowName"],
        capture_output=True, text=True, timeout=60,
    )
    if not out.stdout.strip():
        raise RuntimeError(f"gh run view gave no JSON: {out.stderr.strip()[:200]}")
    r = json.loads(out.stdout)
    if r["status"] != "completed":
        return False, []
    ok = r["conclusion"] in ("success", "skipped", "neutral")
    return True, [] if ok else [f"{r['workflowName']} ({r['conclusion']})"]


def main() -> None:
    try:
        LOCK.mkdir()  # cheap mutex against overlapping fires
    except FileExistsError:
        return
    try:
        tokens = {}
        for job_file in sorted(JOBS.glob("*.json")):
            job = json.load(open(job_file))
            repo = job.get("repo", "freeflow-community/flow")
            label = f"pr {job['pr']}" if "pr" in job else f"run {job['run']}"
            try:
                if "pr" in job:
                    done, failed = check_pr(repo, job["pr"])
                else:
                    done, failed = check_run(repo, job["run"])
            except Exception as e:
                print(f"{label}: {e}", file=sys.stderr)
                continue
            if not done:
                age_min = (time.time() - job_file.stat().st_mtime) / 60
                limit = job.get("timeout_minutes", 60)
                if age_min > limit:
                    token_file = job.get("token_file", DEFAULT_TOKEN_FILE)
                    if token_file not in tokens:
                        tokens[token_file] = json.load(open(token_file))["agentToken"]
                    post(tokens[token_file], job.get("channel_id", FACTORY_CHANNEL),
                         f"{job['fail_body']} — ci-watch deadline hit ({limit}m), checks still pending",
                         job.get("thread_root_id"))
                    job_file.unlink()
                    print(f"{label}: posted deadline failure after {int(age_min)}m")
                continue
            if failed:
                body = f"{job['fail_body']} — failing checks: {', '.join(failed)}"
            else:
                body = job["success_body"]
            token_file = job.get("token_file", DEFAULT_TOKEN_FILE)
            if token_file not in tokens:
                tokens[token_file] = json.load(open(token_file))["agentToken"]
            post(tokens[token_file], job.get("channel_id", FACTORY_CHANNEL),
                 body, job.get("thread_root_id"))
            job_file.unlink()
            print(f"{label}: posted {'failure' if failed else 'success'} dispatch")
    finally:
        LOCK.rmdir()


if __name__ == "__main__":
    main()
