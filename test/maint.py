import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout import Float, FloatContainer
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import ANSI, to_formatted_text

from Packages.colors import *
from translate import create_style


def initPanel(confs: dict):

    def formatted(text):
        if isinstance(text, str):
            return to_formatted_text(ANSI(text))
        return to_formatted_text(text)

    messages = [
        *formatted(confs["NAME_TEXT"] + "\n"),
        *formatted(confs["SUBNAME_TEXT"] + "\n"),
    ]

    commands = WordCompleter(
        confs["COMMANDS_LIST"],
        sentence=True,
        match_middle=False,
    )

    input_field = TextArea(
        prompt="❯ ",
        multiline=False,
        style="class:input-field",
        height=1,
        completer=commands,
        complete_while_typing=True,
    )

    def get_messages():
        return messages

    chat_window = Window(
        content=FormattedTextControl(get_messages),
        wrap_lines=True,
    )

    separator = Window(
        height=1,
        char="─",
        style="class:separator",
    )

    kb = KeyBindings()

    @kb.add("enter")
    def submit(event):
        text = input_field.text.strip()

        if not text:
            return

        if text == "/exit":
            event.app.exit()
            return

        messages.extend(formatted(f"\n> {text}\n"))
        messages.extend(formatted(f"{text}\n"))

        input_field.text = ""
        event.app.invalidate()

    root = FloatContainer(
        content=HSplit([
            chat_window,
            separator,
            Window(
                content=FormattedTextControl(
                    lambda: formatted(
                        confs["INPUT_BOX_UPPER_TEXT"]
                    )
                ),
                height=1,
                style="class:hint",
            ),
            input_field,
        ]),
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(
                    max_height=6,
                    scroll_offset=1,
                ),
            )
        ],
    )

    style = create_style(confs["STYLE"])

    return Application(
        layout=Layout(root, focused_element=input_field),
        key_bindings=kb,
        style=style,
        full_screen=True,
    )


PANEL_CONFS = {
    "NAME_TEXT": f"{BOLD + BLUE}KML CODE{RESET}",
    "SUBNAME_TEXT": f"{ITALIC}The Tiny Agents Ultimate Framework{RESET}",
    "INPUT_BOX_UPPER_TEXT": f"{DIM}Try typing something{RESET}",
    "STYLE": {
        "title": BOLD + BLUE,
        "user": BOLD + BLUE,
        "separator": DIM + BLACK,
        "hint": DIM,
        "input-field": BG_BLUE + WHITE,

        "completion-menu": WHITE,
        "completion-menu.completion": WHITE,
        "completion-menu.completion.current": BG_BLUE + BOLD + BLUE,

        "scrollbar": BG_BLACK,
        "scrollbar.button": BG_BLACK + WHITE,
    },
    "COMMANDS_LIST": [
        "/help",
        "/model",
        "/files",
        "/clear",
        "/exit",
    ],
}

panel = initPanel(PANEL_CONFS)
panel.run()
