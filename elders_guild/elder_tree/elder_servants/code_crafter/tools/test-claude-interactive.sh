#!/usr/bin/env bash
# Test Claude interactive mode

# TTYを強制的に割り当てる
script -q -c 'claude --dangerously-skip-permissions' /dev/null
