from Packages.colors import *


def prettyResolve(text):
    result = []

    bold = False
    title_color = ""
    title_active = False
    line_start = True
    i = 0

    def apply_style():
        result.append((title_color or "") + (BOLD if bold or title_active else ""))

    while i < len(text):
        if line_start:
            if text[i : i + 4] == "### ":
                title_color = CYAN
                title_active = True
                result.append(title_color + BOLD)
                i += 4
                line_start = False
                continue

            elif text[i : i + 3] == "## ":
                title_color = BLUE
                title_active = True
                result.append(title_color + BOLD)
                i += 3
                line_start = False
                continue

            elif text[i : i + 2] == "# ":
                title_color = YELLOW
                title_active = True
                result.append(title_color + BOLD)
                i += 2
                line_start = False
                continue

        if text[i : i + 2] == "**":
            bold = not bold
            result.append(RESET)
            apply_style()
            i += 2
            line_start = False
            continue

        if text[i] == "*":
            bold = not bold
            result.append(RESET)
            apply_style()
            i += 1
            line_start = False
            continue

        char = text[i]
        result.append(char)
        i += 1

        if char == "\n":

            result.append(RESET)

            bold = False
            title_color = ""
            title_active = False
            line_start = True
        else:
            line_start = False

    result.append(RESET)

    return "".join(result)
