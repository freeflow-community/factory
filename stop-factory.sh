#!/bin/bash
# Kill the factory bridges and anything they spawned. Two sweeps:
#  1. any flow-agent-bridge run against an agent.json (matches relative or
#     absolute paths — but not the `flow-agent-bridge mcp` subprocesses that
#     interactive Claude Code sessions run)
#  2. any process whose cwd is one of the agent folders (catches orphaned
#     headless claude sessions the bridges spawned)
cd "$(dirname "$0")"
stopped=""
pkill -f 'flow-agent-bridge.*agent\.json' && stopped=1
pids=$(lsof -t -a -d cwd "$PWD/pm" "$PWD/builder" "$PWD/mergemaster" 2>/dev/null)
if [ -n "$pids" ]; then
  kill $pids 2>/dev/null && stopped=1
fi
[ -n "$stopped" ] && echo stopped || echo nothing running
