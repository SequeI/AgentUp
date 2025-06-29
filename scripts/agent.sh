#!/usr/bin/env bash
set -euo pipefail
 
echo "=== Creating Agent ==="
echo

temp_folder="/tmp/$(pwgen -1 -A 4)"
agentup create-agent -q --no-git --output-dir "$temp_folder" myagent

cd $temp_folder

uv sync --active
agentup dev


trap 'rm -rf "$temp_folder"' EXIT



