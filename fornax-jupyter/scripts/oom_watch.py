#!/usr/bin/env python3
import time
import os
import signal
from pathlib import Path

# Processes that must NEVER be killed (Jupyter UI, init system, shells, etc.)
PROTECTED = ['jupyter', 'tini', 'watchdog', 'bash', 'sh', 'node']
NOTIFICATION_FILE = (Path(os.environ.get("HOME", "/home/jovyan")) /
                     "_PROCESS_KILLED_DUE_TO_MEMORY.txt")
# Do not kill processes using less than this amount of memory
MIN_KILL_MB = 1024


def read_int(paths, default=None):
    """Helper to read the first valid integer from a list of
    paths (handles cgroup v2 & v1)"""
    for p in paths:
        try:
            txt = Path(p).read_text().strip()
            return default if txt == 'max' else int(txt)
        except Exception:
            continue
    return default


def watchdog():
    limit = read_int(['/sys/fs/cgroup/memory.max',
                      '/sys/fs/cgroup/memory/memory.limit_in_bytes'])
    if not limit:
        return print("[Watchdog] No memory limit found. Exiting.")

    # Tiered buffer: 1GB for <16GB limits, 2.5GB for larger
    buffer_bytes = int((1.0 if (limit / 1024**3) < 16 else 2.5) * 1024**3)
    print((f"[Watchdog] Started. Limit: {limit//1024**2}MB, "
           f"Buffer: {buffer_bytes//1024**2}MB"))

    while True:
        time.sleep(0.5)
        used = read_int(['/sys/fs/cgroup/memory.current',
                         '/sys/fs/cgroup/memory/memory.usage_in_bytes'])

        # If memory is safe, do nothing
        if not used or (limit - used) > buffer_bytes:
            continue

        print(("[Watchdog] Low memory! "
               f"({used//1024**2}MB / {limit//1024**2}MB). Scanning..."))
        processes = []

        # Scan all numeric directories in /proc
        for p in Path('/proc').glob('[0-9]*'):
            try:
                cmd = p.joinpath(
                    'cmdline').read_text().replace('\0', ' ').strip()
                pid = int(p.name)

                # Skip empty commands, protected system processes,
                # and the watchdog itself
                if (
                    not cmd or
                    any(x in cmd for x in PROTECTED) or
                    pid == os.getpid()
                ):
                    continue

                # statm 2nd column is RSS in 4KB pages
                mem_bytes = int(
                    p.joinpath('statm').read_text().split()[1]) * 4096

                # Only add to our list if it's actually large enough to matter
                if mem_bytes >= (MIN_KILL_MB * 1024 * 1024):
                    processes.append((pid, mem_bytes, cmd))

            except Exception:
                pass  # Process exited while reading

        if processes:
            # Find the largest non-protected process
            pid, mem, cmd = max(processes, key=lambda x: x[1])
            mem_mb = mem // 1024**2
            print(f"[Watchdog] Killing PID {pid} ({mem_mb}MB): {cmd[:100]}")

            # Notify user and kill
            msg = ("SYSTEM ALERT: Process terminated to prevent server "
                   f"crash.\nTime: {time.ctime()}\nProcess: "
                   f"{cmd}\nMemory: ~{mem_mb} MB")
            try:
                NOTIFICATION_FILE.write_text(msg)
            except Exception:
                pass

            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

            # Wait for OS to reclaim memory before checking again
            time.sleep(10)


if __name__ == "__main__":
    watchdog()
