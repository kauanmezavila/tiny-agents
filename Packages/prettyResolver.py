from Packages.colors import *


def prettyResolve(text):
    result = []
    bold = False
    i = 0
    line_start = True
    title_color = ""
    title_active = False

    while i < len(text):
        if line_start:
            if text[i : i + 4] == "### ":
                title_active = True
                title_color = CYAN
                result.append(title_color + BOLD)
                i += 4
                line_start = False
                continue

            elif text[i : i + 3] == "## ":
                title_active = True
                title_color = BLUE
                result.append(title_color + BOLD)
                i += 3
                line_start = False
                continue

            elif text[i : i + 2] == "# ":
                title_active = True
                title_color = YELLOW
                result.append(title_color + BOLD)
                i += 2
                line_start = False
                continue

        if text[i : i + 2] == "**":
            bold = not bold
            result.append(
                (title_color if title_color else "") + (BOLD if bold else RESET)
            )
            i += 2

        else:
            char = text[i]
            result.append(char)
            i += 1

            if char == "\n":
                line_start = True
                bold = False
                title_color = ""

                if title_active:
                    result.append(RESET)
                    title_active = False
            else:
                line_start = False

    result.append(RESET)
    return "".join(result)
