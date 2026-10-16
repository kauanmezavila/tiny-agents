
import re
from prompt_toolkit.styles import Style

def ansi_to_prompt_style(ansi: str) -> str:
    codes = re.findall(r"\033\[([0-9;]*)m", ansi)

    attributes = []
    foreground = None
    background = None

    for code in codes:
        values = [int(value or 0) for value in code.split(";")]

        i = 0
        while i < len(values):
            value = values[i]

            if value == 0:
                attributes.clear()
                foreground = None
                background = None
            elif value == 1:
                if "bold" not in attributes:
                    attributes.append("bold")
            elif value == 2:
                if "dim" not in attributes:
                    attributes.append("dim")
            elif value == 3:
                if "italic" not in attributes:
                    attributes.append("italic")
            elif value == 4:
                if "underline" not in attributes:
                    attributes.append("underline")
            elif value == 22:
                attributes = [
                    attr for attr in attributes
                    if attr not in ("bold", "dim")
                ]
            elif value == 23:
                attributes = [a for a in attributes if a != "italic"]
            elif value == 24:
                attributes = [a for a in attributes if a != "underline"]
            elif 30 <= value <= 37:
                foreground = [
                    "ansiblack", "ansired", "ansigreen", "ansiyellow",
                    "ansiblue", "ansimagenta", "ansicyan", "ansiwhite"
                ][value - 30]
            elif 90 <= value <= 97:
                foreground = [
                    "ansibrightblack", "ansibrightred",
                    "ansibrightgreen", "ansibrightyellow",
                    "ansibrightblue", "ansibrightmagenta",
                    "ansibrightcyan", "ansibrightwhite"
                ][value - 90]
            elif value == 39:
                foreground = None
            elif 40 <= value <= 47:
                background = [
                    "ansiblack", "ansired", "ansigreen", "ansiyellow",
                    "ansiblue", "ansimagenta", "ansicyan", "ansiwhite"
                ][value - 40]
            elif 100 <= value <= 107:
                background = [
                    "ansibrightblack", "ansibrightred",
                    "ansibrightgreen", "ansibrightyellow",
                    "ansibrightblue", "ansibrightmagenta",
                    "ansibrightcyan", "ansiwhite"
                ][value - 100]
            elif value == 49:
                background = None
            elif value in (38, 48) and i + 1 < len(values):
                target = "fg" if value == 38 else "bg"
                mode = values[i + 1]

                if mode == 2 and i + 4 < len(values):
                    r, g, b = values[i + 2:i + 5]
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    if target == "fg":
                        foreground = color
                    else:
                        background = color
                    i += 4
                elif mode == 5 and i + 2 < len(values):
                    color = values[i + 2]
                    if target == "fg":
                        foreground = f"ansicolor{color}"
                    else:
                        background = f"ansicolor{color}"
                    i += 2

            i += 1

    result = list(attributes)

    if foreground:
        result.append(f"fg:{foreground}")
    if background:
        result.append(f"bg:{background}")

    return " ".join(result)


def create_style(config: dict) -> Style:
    return Style.from_dict({
        name: ansi_to_prompt_style(value)
        for name, value in config.items()
    })
