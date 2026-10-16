import subprocess
from Packages.colors import DIM, RESET

def runInShell(cmd):
    logs = []

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if process.stdout:
        for line in process.stdout:
            logs.append(line)

    code = process.wait()

    return {
        "logs": logs,
        "exitCode": code
    }

def runInShellCool(cmd):
    print(f"{DIM}$ {cmd}")
    logs = []

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if process.stdout:
        for line in process.stdout:
            logs.append(line)
            print(line)

    code = process.wait()
    print(f"Exited with [{code}]{RESET}")

    return {
        "logs": logs,
        "exitCode": code
    }
