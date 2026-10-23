#!/usr/bin/env bash
# Runs a command whose output contains scraped text (job titles, feed entries,
# server error messages) with GitHub workflow commands paused, so that a line
# starting with "::" can never be interpreted as a command. The run summary
# written by tracker/gha.py to $GHA_NOTICES is printed once commands resume.
set -uo pipefail
token="$(openssl rand -hex 16)"
echo "::stop-commands::${token}"
"$@" 2>&1 | tee -a run.log
status=${PIPESTATUS[0]}
echo "::${token}::"
if [ -n "${GHA_NOTICES:-}" ] && [ -s "${GHA_NOTICES}" ]; then
  cat "${GHA_NOTICES}"
  rm -f "${GHA_NOTICES}"
fi
exit "${status}"
