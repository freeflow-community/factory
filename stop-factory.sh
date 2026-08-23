#!/bin/bash
pkill -f 'flow-agent-bridge.*factory/(pm|builder|mergemaster)/agent.json' && echo stopped || echo nothing running
