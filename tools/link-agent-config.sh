#!/usr/bin/env bash
# Links .opencode/{agents,commands} to .claude/{agents,commands}.
#
# Agent and command definitions live once, in .claude/. Claude Code reads them there;
# opencode only scans .opencode/, so we point it at the same files with a symlink.
#
# Run once per clone:
#   tools/link-agent-config.sh

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for name in agents commands; do
    link="$repo/.opencode/$name"
    target="$repo/.claude/$name"

    if [ ! -d "$target" ]; then
        echo "error: missing source directory: $target" >&2
        exit 1
    fi

    if [ -e "$link" ]; then
        if [ -L "$link" ]; then
            echo "ok    .opencode/$name -> .claude/$name (already linked)"
            continue
        fi
        echo "error: .opencode/$name exists and is a real directory. Delete it first, then re-run." >&2
        exit 1
    fi

    ln -s "$target" "$link"
    echo "link  .opencode/$name -> .claude/$name"
done
