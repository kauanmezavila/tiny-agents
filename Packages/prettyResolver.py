import re

from Packages.colors import BLUE, BOLD, BRIGHT_CYAN, CYAN, DIM, RESET, YELLOW


def _inline(text):
    """Render the common inline Markdown marks without changing plain text."""
    pattern = re.compile(
        r"(\*\*.+?\*\*|(?<!\*)\*[^*\n]+\*(?!\*)|`[^`]+`|\[[^\]]+\]\([^)]+\))"
    )
    rendered = []
    for part in pattern.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            rendered.append(f"{BOLD}{part[2:-2]}{RESET}")
        elif part.startswith("*") and part.endswith("*"):
            rendered.append(f"\033[3m{part[1:-1]}{RESET}")
        elif part.startswith("`") and part.endswith("`"):
            rendered.append(f"{CYAN}{part[1:-1]}{RESET}")
        elif part.startswith("["):
            match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", part)
            rendered.append(f"{match.group(1)} ({match.group(2)})" if match else part)
        else:
            rendered.append(part)
    return "".join(rendered)


def _table(lines):
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines
    ]
    rows = [
        row for row in rows if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)
    ]
    if not rows:
        return []
    columns = max(map(len, rows))
    rows = [row + [""] * (columns - len(row)) for row in rows]
    widths = [max(len(row[i]) for row in rows) for i in range(columns)]
    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    output = [border]
    for index, row in enumerate(rows):
        output.append(
            "| "
            + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
            + " |"
        )
        if index == 0:
            output.append(border)
    output.append(border)
    return output


def prettyResolve(text):
    """Render common Markdown (headings, emphasis, lists, code, and tables) for a terminal."""
    lines = text.splitlines()
    output = []
    in_code = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_code:
                in_code = True
            else:
                in_code = False
            i += 1
            continue
        if in_code:
            output.append(f"{DIM}{line}{RESET}")
            i += 1
            continue
        if (
            "|" in line
            and i + 1 < len(lines)
            and re.fullmatch(
                r"\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*", lines[i + 1]
            )
        ):
            table_lines = [line]
            i += 2
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            output.extend(_table(table_lines))
            continue
        heading = re.match(r"^\s{0,3}(#{1,6})\s+(.*)$", line)
        if heading:
            color = {1: YELLOW, 2: BLUE, 3: CYAN}.get(
                len(heading.group(1)), BRIGHT_CYAN
            )
            output.append(f"{color}{BOLD}{_inline(heading.group(2))}{RESET}")
        else:
            bullet = re.match(r"^(\s*)([-+*])\s+(.*)$", line)
            numbered = re.match(r"^(\s*)(\d+[.)])\s+(.*)$", line)
            if bullet:
                output.append(f"{bullet.group(1)}• {_inline(bullet.group(3))}")
            elif numbered:
                output.append(
                    f"{numbered.group(1)}{numbered.group(2)} {_inline(numbered.group(3))}"
                )
            else:
                output.append(_inline(line))
        i += 1
    return "\n".join(output) + ("\n" if text.endswith("\n") else "")
