#!/bin/bash
# Optional startup tracer, added for the startup-time investigation.
#
#   FORNAX_STARTUP_TRACE=1  -> trace start.sh to /tmp/startup-trace.log
#   FORNAX_STARTUP_TRACE=2  -> trace start.sh to stderr (visible in pod logs)
#   unset / anything else   -> exec start.sh unchanged (zero overhead)
#
# Trace lines are prefixed with +[<epoch.microseconds>] so per-phase durations
# can be computed from the log (see anvil scripts/perf/analyze.py).
# Trace mode also appends --debug to NOTEBOOK_ARGS, which makes the jupyter
# server log per-extension load times.

case "${FORNAX_STARTUP_TRACE:-}" in
    1)  exec 9>> /tmp/startup-trace.log ;;
    2)  exec 9>&2 ;;
    *)  exec /usr/local/bin/start.sh "$@" ;;
esac

BASH_XTRACEFD=9
PS4='+[${EPOCHREALTIME}] '
export NOTEBOOK_ARGS="${NOTEBOOK_ARGS:-} --debug"
set -x
# Source (not exec) so the xtrace fd/PS4 apply to start.sh itself; with no
# arguments, `source` passes this script's "$@" through to start.sh.
source /usr/local/bin/start.sh
