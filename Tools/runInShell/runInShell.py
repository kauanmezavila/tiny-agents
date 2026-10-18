import subprocess
from Packages.colors import (
    BOLD,
    BRIGHT_BLUE,
    BRIGHT_GREEN,
    BRIGHT_RED,
    DIM,
    RESET,
)


def runInShell(cmd):
    logs = []

    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    if process.stdout:
        for line in process.stdout:
            logs.append(line)

    code = process.wait()

    return {"logs": logs, "exitCode": code}


def runInShellCool(cmd, write=print):
    write(f"{BRIGHT_BLUE}{BOLD}╭─ $ {cmd}{RESET}")
    logs = []

    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    if process.stdout:
        for line in process.stdout:
            logs.append(line)
            text = line.rstrip("\r\n")
            write(f"{DIM}│ {text}{RESET}")

    code = process.wait()
    if code == 0:
        write(f"{DIM}{BRIGHT_GREEN}{BOLD}╰─ ✓ Completed{RESET} (exit code {code}){RESET}")
    else:
        write(f"{DIM}{BRIGHT_RED}{BOLD}╰─ ✗ Failed{RESET} (exit code {code}){RESET}")

    return {"logs": logs, "exitCode": code}
