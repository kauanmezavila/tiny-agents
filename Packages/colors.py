import os
import sys
import time
import random

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"
STRIKE = "\033[9m"


BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"


BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

BG_BRIGHT_BLACK = "\033[100m"
BG_BRIGHT_RED = "\033[101m"
BG_BRIGHT_GREEN = "\033[102m"
BG_BRIGHT_YELLOW = "\033[103m"
BG_BRIGHT_BLUE = "\033[104m"
BG_BRIGHT_MAGENTA = "\033[105m"
BG_BRIGHT_CYAN = "\033[106m"
BG_BRIGHT_WHITE = "\033[107m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def bg_rgb(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"


def hex_color(value):
    value = value.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    return rgb(r, g, b)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def slow(text, delay=0.03, color=""):
    for char in text:
        sys.stdout.write(color + char + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def loading(text="Loading", duration=2, color=CYAN):
    frames = ["|", "/", "-", "\\"]
    end = time.time() + duration

    while time.time() < end:
        for frame in frames:
            sys.stdout.write(f"\r{color}{frame} {text}...{RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
            if time.time() >= end:
                break

    print(f"\r{GREEN}✓ {text} completed!{RESET}")


def progress(total=20, delay=0.05, color=GREEN):
    for i in range(total + 1):
        percent = int(i / total * 100)
        bar = "█" * i + "░" * (total - i)

        sys.stdout.write(f"\r{color}[{bar}] {percent}%{RESET}")
        sys.stdout.flush()
        time.sleep(delay)

    print()


def rainbow(text):
    colors = [RED, YELLOW, GREEN, CYAN, BLUE, MAGENTA]
    for i, char in enumerate(text):
        sys.stdout.write(colors[i % len(colors)] + char)
    print(RESET, end="")


def flash(text, times=3, delay=0.2, color=YELLOW):
    for _ in range(times):
        print(f"\r{color}{BOLD}{text}{RESET}", end="", flush=True)
        time.sleep(delay)
        print("\r" + " " * len(text), end="", flush=True)
        time.sleep(delay)
    print(f"\r{color}{BOLD}{text}{RESET}")


def random_color(text):
    colors = [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, BRIGHT_WHITE]
    print(f"{random.choice(colors)}{text}{RESET}")


def box(text, color=CYAN):
    lines = text.splitlines() or [""]
    width = max(map(len, lines))
    border = "+" + "-" * (width + 2) + "+"

    print(f"{color}{border}{RESET}")
    for line in lines:
        print(f"{color}|{RESET} {line:<{width}} {color}|{RESET}")
    print(f"{color}{border}{RESET}")


def title(text, color=BRIGHT_CYAN):
    print(f"\n{color}{BOLD}{'=' * 40}")
    print(f"  {text}")
    print(f"{'=' * 40}{RESET}\n")
