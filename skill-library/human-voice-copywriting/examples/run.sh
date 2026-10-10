#!/usr/bin/env bash
# 跑一遍校准样本，看四条结论是否还对得上。
set -u
cd "$(dirname "$0")/.."
for f in examples/0*.md; do
  printf '\n--- %s\n' "$f"
  python3 scripts/check_copy.py "$f" | grep -E '^(OK|!!)|^\[结论\]'
done
