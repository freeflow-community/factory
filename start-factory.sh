#!/bin/bash
# Start the three factory bridges, one log each. Skips an agent whose bridge
# is already running. An agent with no agent.json yet has not been onboarded:
# run `npx flow-agent-bridge <invite-code>` in its folder once — setup reads
# the folder's agent.example.json for all defaults and writes agent.json.
set -euo pipefail
cd "$(dirname "$0")"
for a in pm builder mergemaster; do
  if pgrep -f "flow-agent-bridge.*factory/$a/agent.json" >/dev/null; then
    echo "$a: already running"
    continue
  fi
  if [ ! -f "$a/agent.json" ]; then
    echo "$a: no agent.json — cd $a && npx flow-agent-bridge <invite-code>  (uses agent.example.json)"
    continue
  fi
  (cd "$a" && nohup npx flow-agent-bridge agent.json >> bridge.out 2>&1 &)
  echo "$a: started (log: $a/agent.log)"
done
