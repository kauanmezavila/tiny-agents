from __future__ import annotations

import asyncio
import inspect
import re
import shlex
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from time import monotonic
from typing import Awaitable, Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prompt_toolkit.application import Application
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    DynamicContainer,
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Layout,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea

from .themes import BASE_STYLE, THEMES

from prompt_toolkit.patch_stdout import patch_stdout

try:
    from Packages.colors import *
except ImportError:
    pass

import threading


class AsyncWorker:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="KML-Agent-Worker",
        )
        self.thread.start()
        self.ready.wait()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.ready.set()
        self.loop.run_forever()

    async def run(self, coroutine):
        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            self.loop,
        )
        return await asyncio.wrap_future(future)


Handler = Callable[[list[str], "PanelContext"], str | None | Awaitable[str | None]]
Action = Callable[[], None]


@dataclass
class Command:
    name: str
    description: str
    handler: Handler


class PanelContext:

    def __init__(
        self,
        write: Callable[[str], None],
        clear: Action,
        exit: Action,
    ) -> None:
        self._write = write
        self._clear = clear
        self._exit = exit

    def write(self, text: str) -> None:
        self._write(str(text))

    def clear(self) -> None:
        self._clear()

    def exit(self) -> None:
        self._exit()


async def dispatch(
    text: str,
    registry: dict[str, Command],
    ctx: PanelContext,
) -> str | None:
    try:
        parts = shlex.split(text)
    except ValueError as exc:
        return f"[ERROR] Syntax error: {exc}"

    if not parts:
        return None

    name, *args = parts
    command = registry.get(name)
    if command is None:
        return f"[ERROR] Unknown command: {name}"

    try:
        if inspect.iscoroutinefunction(command.handler):
            result = await command.handler(args, ctx)
        else:
            result = await asyncio.to_thread(command.handler, args, ctx)
        if inspect.isawaitable(result):
            result = await result
        if result is not None and not isinstance(result, str):
            return str(result)
        return result
    except Exception as exc:
        return f"[ERROR] Failed to execute {name}: {exc}"


def ansi_to_prompt_style(ansi: str) -> str:
    codes = re.findall(r"\x1b\[([0-9;]*)m", ansi)
    attributes: list[str] = []
    foreground: str | None = None
    background: str | None = None

    normal_colors = [
        "ansiblack",
        "ansired",
        "ansigreen",
        "ansiyellow",
        "ansiblue",
        "ansimagenta",
        "ansicyan",
        "ansiwhite",
    ]
    bright_colors = [
        "ansibrightblack",
        "ansibrightred",
        "ansibrightgreen",
        "ansibrightyellow",
        "ansibrightblue",
        "ansibrightmagenta",
        "ansibrightcyan",
        "ansibrightwhite",
    ]

    def color_256(index: int) -> str:
        index = max(0, min(255, index))
        if index < 16:
            palette = [
                "#000000",
                "#800000",
                "#008000",
                "#808000",
                "#000080",
                "#800080",
                "#008080",
                "#c0c0c0",
                "#808080",
                "#ff0000",
                "#00ff00",
                "#ffff00",
                "#0000ff",
                "#ff00ff",
                "#00ffff",
                "#ffffff",
            ]
            return palette[index]
        if index < 232:
            index -= 16
            levels = [0, 95, 135, 175, 215, 255]
            r = levels[index // 36]
            g = levels[(index % 36) // 6]
            b = levels[index % 6]
            return f"#{r:02x}{g:02x}{b:02x}"
        gray = 8 + (index - 232) * 10
        return f"#{gray:02x}{gray:02x}{gray:02x}"

    for code in codes:
        values = [int(value or 0) for value in code.split(";")]
        i = 0
        while i < len(values):
            value = values[i]

            if value == 0:
                attributes.clear()
                foreground = None
                background = None
            elif value == 1 and "bold" not in attributes:
                attributes.append("bold")
            elif value == 2 and "dim" not in attributes:
                attributes.append("dim")
            elif value == 3 and "italic" not in attributes:
                attributes.append("italic")
            elif value == 4 and "underline" not in attributes:
                attributes.append("underline")
            elif value == 22:
                attributes = [a for a in attributes if a not in ("bold", "dim")]
            elif value == 23:
                attributes = [a for a in attributes if a != "italic"]
            elif value == 24:
                attributes = [a for a in attributes if a != "underline"]
            elif 30 <= value <= 37:
                foreground = normal_colors[value - 30]
            elif 90 <= value <= 97:
                foreground = bright_colors[value - 90]
            elif value == 39:
                foreground = None
            elif 40 <= value <= 47:
                background = normal_colors[value - 40]
            elif 100 <= value <= 107:
                background = bright_colors[value - 100]
            elif value == 49:
                background = None
            elif value in (38, 48) and i + 1 < len(values):
                target = "fg" if value == 38 else "bg"
                mode = values[i + 1]
                color: str | None = None
                if mode == 2 and i + 4 < len(values):
                    r, g, b = values[i + 2 : i + 5]
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    i += 4
                elif mode == 5 and i + 2 < len(values):
                    color = color_256(values[i + 2])
                    i += 2
                if color is not None:
                    if target == "fg":
                        foreground = color
                    else:
                        background = color
            i += 1

    result = list(attributes)
    if foreground:
        result.append(f"fg:{foreground}")
    if background:
        result.append(f"bg:{background}")
    return " ".join(result)


def create_style(config: dict) -> Style:
    return Style.from_dict(
        {
            name: (
                ansi_to_prompt_style(value)
                if isinstance(value, str) and "\x1b[" in value
                else str(value)
            )
            for name, value in config.items()
        }
    )


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


@lru_cache(maxsize=4096)
def _styled_ansi_line(text: str, base_style: str):
    return [
        (f"{base_style} {style}".strip(), fragment)
        for style, fragment in to_formatted_text(ANSI(text))
    ]


class ANSIChatLexer(Lexer):

    def __init__(self) -> None:
        self.ansi_lines: list[str] = [""]
        self.line_styles: list[str] = [""]

    def set_text(self, raw_text: str, line_styles: list[str] | None = None) -> None:
        self.ansi_lines = raw_text.split("\n")
        self.line_styles = line_styles or [""] * len(self.ansi_lines)

    def lex_document(self, document: Document):
        lines = self.ansi_lines
        styles = self.line_styles

        def get_line(lineno: int):
            if 0 <= lineno < len(lines):
                return _styled_ansi_line(lines[lineno], styles[lineno])
            return []

        return get_line


def initPanel(confs: dict) -> Application:

    messages: list[tuple[object, str]] = []
    message_styles: dict[object, str] = {}
    title_id = object()
    title_text = f'{confs.get("NAME_TEXT")}\n{confs.get("SUBNAME_TEXT")}'
    messages.append((title_id, title_text.rstrip()))

    app_ref: list[Application | None] = [None]
    busy = False
    thinking_label = str(confs.get("THINKING_TEXT", "Thinking..."))
    context_size = confs.get("CONTEXT_WINDOW_SIZE", lambda: 0)
    context_max = confs.get("CONTEXT_WINDOW_MAX", 10000)
    if not callable(context_size):
        raise TypeError(
            "CONTEXT_WINDOW_SIZE must be a function that takes no arguments."
        )
    if (
        isinstance(context_max, bool)
        or not isinstance(context_max, int)
        or context_max <= 0
    ):
        raise ValueError("CONTEXT_WINDOW_MAX must be a positive integer.")

    message_spacing = confs.get("MESSAGE_SPACING", 1)
    if (
        isinstance(message_spacing, bool)
        or not isinstance(message_spacing, int)
        or message_spacing < 0
    ):
        raise ValueError("MESSAGE_SPACING must be a non-negative integer.")
    message_separator = "\n" * (message_spacing + 1)

    def render_messages() -> str:
        return message_separator.join(text for _, text in messages)

    refresh_handle: asyncio.TimerHandle | None = None

    def refresh_chat(scroll_to_bottom: bool = True) -> None:
        nonlocal refresh_handle
        if refresh_handle is not None:
            refresh_handle.cancel()
            refresh_handle = None
        if not locals_ref.get("chat_area"):
            return
        raw_text = render_messages()
        line_styles: list[str] = []
        for index, (ident, text) in enumerate(messages):
            if index:
                line_styles.extend([""] * message_spacing)
            style = message_styles.get(ident, "")
            line_styles.extend([style] * len(text.split("\n")))
        chat_lexer.set_text(raw_text, line_styles)
        plain_text = strip_ansi(raw_text)
        cursor = (
            len(plain_text)
            if scroll_to_bottom
            else min(chat_area.buffer.cursor_position, len(plain_text))
        )
        chat_area.buffer.set_document(
            Document(plain_text, cursor_position=cursor), bypass_readonly=True
        )
        app = app_ref[0]
        if app is not None:
            app.invalidate()

    def schedule_refresh() -> None:
        nonlocal refresh_handle
        app = app_ref[0]
        if app is None or not app.is_running:
            refresh_chat()
        elif refresh_handle is None:
            refresh_handle = app.loop.call_later(0.03, refresh_chat)

    locals_ref: dict[str, bool] = {}

    def add_message(
        text: str, message_id: object | None = None, user: bool = False, kind: str = ""
    ) -> object:
        ident = message_id if message_id is not None else object()
        if user:
            kind = "user"
        elif strip_ansi(str(text)).startswith("[ERROR]"):
            kind = "error"
        if kind:
            message_styles[ident] = f"class:{kind}"
        messages.append((ident, str(text)))
        schedule_refresh()
        return ident

    def run_on_ui(callback: Callable, *args) -> None:
        app = app_ref[0]
        if app is None or not app.is_running:
            callback(*args)
            return

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is app.loop:
            callback(*args)
        else:
            app.loop.call_soon_threadsafe(callback, *args)

    def write_message(text: str) -> None:
        run_on_ui(add_message, str(text))

    def clear_messages_now() -> None:
        messages.clear()
        message_styles.clear()
        messages.append((title_id, title_text.rstrip()))
        refresh_chat()

    def clear_messages() -> None:
        run_on_ui(clear_messages_now)

    def exit_panel_now() -> None:
        app = app_ref[0]
        if app is not None and app.is_running:
            app.exit()

    def exit_panel() -> None:
        run_on_ui(exit_panel_now)

    ctx = PanelContext(
        write=write_message,
        clear=clear_messages,
        exit=exit_panel,
    )

    registry = {command.name: command for command in confs.get("COMMANDS", [])}

    model_options = confs.get("MODEL_OPTIONS", [])
    model_menu_open = False
    model_menu_index = 0
    if model_options:
        options = [str(option) for option in model_options]

        async def select_model(args: list[str], ctx: PanelContext):
            if not args:
                nonlocal model_menu_open, model_menu_index
                current = str(confs.get("MODEL_NAME") or "")
                model_menu_index = options.index(current) if current in options else 0
                model_menu_open = True
                app = app_ref[0]
                if app is not None:
                    app.layout.focus(input_field)
                    app.invalidate()
                return

            selected = " ".join(args)
            if selected.isdigit():
                index = int(selected) - 1
                if not 0 <= index < len(options):
                    return f"[ERROR] Invalid index. Choose between 1-{len(options)}."
                selected = options[index]
            elif selected not in options:
                return f"[ERROR] Invalid model: {selected}. Use /model to the options"

            on_select = confs.get("MODEL_SELECT_HANDLER")
            if on_select is not None:
                result = on_select(selected)
                if inspect.isawaitable(result):
                    await result
            confs["MODEL_NAME"] = selected
            return

        registry["/model"] = Command("/model", "List or select a model", select_model)

    command_suggestions = list(confs.get("COMMANDS_LIST", registry.keys()))
    if "/model" in registry and "/model" not in command_suggestions:
        command_suggestions.append("/model")
    commands = WordCompleter(
        command_suggestions,
        sentence=True,
        match_middle=False,
    )

    chat_lexer = ANSIChatLexer()
    initial_raw_text = render_messages()
    chat_lexer.set_text(initial_raw_text)

    chat_area = TextArea(
        text=strip_ansi(initial_raw_text),
        lexer=chat_lexer,
        multiline=True,
        read_only=True,
        focusable=False,
        focus_on_click=False,
        wrap_lines=True,
        scrollbar=True,
        style="class:chat-area",
    )
    locals_ref["chat_area"] = True
    chat_area.buffer.cursor_position = len(chat_area.text)

    input_field = TextArea(
        prompt="❯ ",
        multiline=False,
        style="class:input-field",
        height=1,
        completer=commands,
        complete_while_typing=True,
    )

    separator = Window(
        height=1,
        char="─",
        style="class:separator",
    )

    def get_hint_text():
        configured_hint = str(confs.get("INPUT_BOX_UPPER_TEXT", "")).strip()
        scroll_hint = "Chat: PgUp/PgDn scroll | Ctrl+Home start | Ctrl+End end"
        if configured_hint:
            return f"{scroll_hint}  │  {configured_hint}"
        return scroll_hint

    def model_label() -> str:
        model_name = str(confs.get("MODEL_NAME") or "")
        return f"Model: {model_name}" if model_name else ""

    hint_window = Window(
        content=FormattedTextControl(lambda: to_formatted_text(ANSI(get_hint_text()))),
        height=1,
        style="class:hint",
    )

    spinner_frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def thinking_text() -> str:
        if not busy:
            return ""
        frame = spinner_frames[int(monotonic() / 0.1) % len(spinner_frames)]
        return f"{frame} {thinking_label}"

    context_used = 0

    def update_context(app) -> None:
        nonlocal context_used
        context_used = max(0, int(context_size()))

    def context_text() -> str:
        used = context_used
        ratio = min(1, used / context_max)
        filled = int(ratio * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"Context [{bar}] {used}/{context_max} ({used / context_max:.0%})"

    def context_fragments():
        ratio = context_used / context_max
        level = "full" if ratio >= 0.9 else "warning" if ratio >= 0.7 else "low"
        return [(f"class:context-{level}", context_text())]

    status_row = VSplit(
        [
            Window(
                content=FormattedTextControl(
                    lambda: to_formatted_text(ANSI(thinking_text()))
                ),
                height=1,
                style="class:hint",
                wrap_lines=False,
            ),
            Window(
                content=FormattedTextControl(context_fragments),
                width=lambda: len(context_text()),
                height=1,
                style="class:hint",
                wrap_lines=False,
            ),
        ],
        padding=1,
    )

    hint_row = VSplit(
        [
            hint_window,
            Window(
                content=FormattedTextControl(model_label),
                width=lambda: len(model_label()),
                height=1,
                style="class:hint",
                wrap_lines=False,
            ),
        ],
        padding=1,
    )

    kb = KeyBindings()

    async def apply_menu_model(app: Application) -> None:
        nonlocal model_menu_open
        selected = options[model_menu_index]
        try:
            on_select = confs.get("MODEL_SELECT_HANDLER")
            if on_select is not None:
                result = on_select(selected)
                if inspect.isawaitable(result):
                    await result
            confs["MODEL_NAME"] = selected
            add_message(f"Model selected: {selected}")
        except Exception as exc:
            add_message(f"[ERROR] Fail selecting the model: {exc}")
        finally:
            model_menu_open = False
            app.invalidate()

    menu_is_open = Condition(lambda: model_menu_open)

    @kb.add("up", filter=menu_is_open, eager=True)
    def model_menu_up(event) -> None:
        nonlocal model_menu_index
        if model_menu_open:
            model_menu_index = (model_menu_index - 1) % len(options)
            event.app.invalidate()

    @kb.add("down", filter=menu_is_open, eager=True)
    def model_menu_down(event) -> None:
        nonlocal model_menu_index
        if model_menu_open:
            model_menu_index = (model_menu_index + 1) % len(options)
            event.app.invalidate()

    @kb.add("escape", filter=menu_is_open, eager=True)
    def close_model_menu(event) -> None:
        nonlocal model_menu_open
        if model_menu_open:
            model_menu_open = False
            event.app.invalidate()

    def move_chat_cursor(direction: int, event) -> None:
        doc = chat_area.buffer.document
        current_row = doc.cursor_position_row
        info = chat_area.window.render_info
        visible_rows = info.window_height if info is not None else 12
        step = max(3, visible_rows - 2)
        target_row = max(0, min(len(doc.lines) - 1, current_row + direction * step))
        target_col = min(doc.cursor_position_col, len(doc.lines[target_row]))
        chat_area.buffer.cursor_position = doc.translate_row_col_to_index(
            target_row, target_col
        )
        event.app.invalidate()

    @kb.add("pageup", eager=True)
    def page_up(event) -> None:
        move_chat_cursor(-1, event)

    @kb.add("pagedown", eager=True)
    def page_down(event) -> None:
        move_chat_cursor(1, event)

    @kb.add("c-home")
    def chat_home(event) -> None:
        chat_area.buffer.cursor_position = 0
        event.app.invalidate()

    @kb.add("c-end")
    def chat_end(event) -> None:
        chat_area.buffer.cursor_position = len(chat_area.text)
        event.app.invalidate()

    async def invoke_model(text: str):
        model_handler = confs.get("MODEL_HANDLER")
        if model_handler is None:
            raise RuntimeError("No model handler configured in MODEL_HANDLER.")

        if inspect.iscoroutinefunction(model_handler):
            return await model_handler(text, ctx)

        result = await asyncio.to_thread(model_handler, text, ctx)
        if inspect.isawaitable(result):
            return await result
        return result

    async def animate_activity(app: Application) -> None:
        while busy:
            app.invalidate()
            await asyncio.sleep(0.1)

    async def process_model(text: str, app: Application) -> None:
        nonlocal busy
        animation = app.create_background_task(animate_activity(app))
        try:
            result = await invoke_model(text)
            if result is not None:
                add_message(str(result), kind="model")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            add_message(
                f"[ERROR] Model request failed: {type(exc).__name__}: {exc}",
            )
        finally:
            animation.cancel()
            busy = False
            refresh_chat()
            app.invalidate()

    async def process_command(
        text: str, app: Application, tracks_activity: bool
    ) -> None:
        nonlocal busy
        animation = (
            app.create_background_task(animate_activity(app))
            if tracks_activity
            else None
        )
        try:
            result = await dispatch(text, registry, ctx)
            if result is not None:
                ctx.write(result)
        finally:
            if tracks_activity:
                busy = False
            if animation is not None:
                animation.cancel()
            refresh_chat()
            app.invalidate()

    @kb.add("enter")
    def submit(event) -> None:
        nonlocal busy

        if model_menu_open:
            event.app.create_background_task(apply_menu_model(event.app))
            return

        if event.app.layout.current_buffer is not input_field.buffer:
            event.app.layout.focus(input_field)
            return

        text = input_field.text.strip()
        if not text:
            return

        add_message(f"> {text}", user=True)
        input_field.text = ""

        if text.startswith("/"):
            try:
                name = shlex.split(text)[0]
            except ValueError:
                name = ""
            command = registry.get(name)
            tracks_activity = command is not None and inspect.iscoroutinefunction(
                command.handler
            )
            if tracks_activity and busy:
                add_message(
                    "[INFO] A request is already running. Please wait for the response."
                )
                return
            if tracks_activity:
                busy = True
            event.app.create_background_task(
                process_command(text, event.app, tracks_activity)
            )
            event.app.invalidate()
            return

        if busy:
            add_message(
                "[INFO] A request is already running. Please wait for the response."
            )
            return

        busy = True
        event.app.create_background_task(process_model(text, event.app))
        event.app.invalidate()

    root = FloatContainer(
        content=HSplit(
            [
                chat_area,
                separator,
                status_row,
                hint_row,
                *(
                    [
                        DynamicContainer(
                            lambda: (
                                Window(
                                    content=FormattedTextControl(
                                        lambda: [
                                            ("class:title", " Select model "),
                                            (
                                                "",
                                                "\n↑/↓ navigation | Enter selects | Esc quit\n\n",
                                            ),
                                            *[
                                                (
                                                    (
                                                        "class:radio-checked"
                                                        if index == model_menu_index
                                                        else "class:radio"
                                                    ),
                                                    f"{'❯' if index == model_menu_index else ' '} {option}{'  (actual)' if option == confs.get('MODEL_NAME') else ''}\n",
                                                )
                                                for index, option in enumerate(options)
                                            ],
                                        ]
                                    ),
                                    height=len(options) + 3,
                                    style="class:completion-menu",
                                )
                                if model_menu_open
                                else Window(height=0)
                            )
                        )
                    ]
                    if model_options
                    else []
                ),
                input_field,
            ]
        ),
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(
                    max_height=6,
                    scroll_offset=1,
                ),
            ),
        ],
    )

    theme = confs.get("THEME", "default")
    if theme not in THEMES:
        raise ValueError(f"Invalid THEME: {theme!r}. Options: {', '.join(THEMES)}")
    style_config = {**BASE_STYLE, **THEMES[theme], **confs.get("STYLE", {})}
    style = create_style(style_config)

    app = Application(
        layout=Layout(root, focused_element=input_field),
        key_bindings=kb,
        style=style,
        full_screen=True,
        mouse_support=True,
        min_redraw_interval=0.03,
        before_render=update_context,
    )

    app_ref[0] = app
    return app
