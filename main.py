import os
from dotenv import load_dotenv
from prompt_toolkit.patch_stdout import patch_stdout

from tinyAgents import *
from tinyAgents.panel import initPanel, PanelContext, Command, AsyncWorker
from tinyAgents.colors import *

agent_worker = AsyncWorker()

load_dotenv()

apiKeyNvidia = os.getenv("API_KEY_NVIDIA")
apiKeyOllama = os.getenv("API_KEY_OLLAMA")

profiles = {
    "nvidia": {
        "models": ["openai/gpt-oss-20b"],
        "apiKey": apiKeyNvidia,
    },
    "cloud-ollama": {
        "models": ["gpt-oss:20b"],
        "apiKey": apiKeyOllama,
    }
}

selected = ["nvidia", "openai/gpt-oss-20b"]

toolsJsonPath = os.path.join("Tools", "tools.json")
toolsCallJsonPath = os.path.join("Tools", "toolsCall.json")

TOOLS = loadTools(toolsJsonPath)
TOOLS_HANDLERS = loadToolHandlers(toolsCallJsonPath)

prePrompt = "You are a helpful agent that provides detailed answers. Use tools only if what the user requested needs to."
agent = AgentHarness(
    profiles=profiles,
    selected=selected,
    tools=TOOLS,
    tool_handlers=TOOLS_HANDLERS,
    pre_prompt=prePrompt,
    worker=agent_worker,
    serialized_tools={"runInShell", "runInShellCool"},
    approval_tools={"runInShell", "runInShellCool"},
)


def echo(args: list[str], ctx: PanelContext) -> str:
    return " ".join(args)


def clear_command(args: list[str], ctx: PanelContext) -> None:
    ctx.clear()


def exit_command(args: list[str], ctx: PanelContext) -> None:
    ctx.exit()


COMMANDS = [
    Command("/echo", "Repeat the arguments", echo),
    Command("/clear", "Clear the panel", clear_command),
    Command("/exit", "Exit the panel", exit_command),
    Command("/compact", "Compact the context window", agent.compact_context),
]

PANEL_CONFS = {
    "NAME_TEXT": f"{BOLD + BRIGHT_CYAN}JuCode{RESET}",
    "SUBNAME_TEXT": f"{DIM + ITALIC}Powered by Tiny Agents{RESET}",
    "INPUT_BOX_UPPER_TEXT": f"{DIM}Type a message | / for commands | Tab to complete{RESET}",
    "THINKING_TEXT": "Thinking...",
    "MODEL_NAME": agent.model,
    "MODEL_PROVIDER": agent.provider,
    "MODEL_OPTION": agent.model_option,
    "CONTEXT_WINDOW_SIZE": contextWindowSize,
    "CONTEXT_WINDOW_MAX": 10000,
    "THEME": "default",
    "MESSAGE_SPACING": 1,
    "STYLE": {
        "title": BOLD + BRIGHT_CYAN,
        "user": BG_BLUE + WHITE,
        "model": WHITE,
        "error": RED,
        "separator": DIM + BLACK,
        "hint": DIM,
        "input-field": BG_BLUE + WHITE,
        "completion-menu": BG_BRIGHT_BLACK + WHITE,
        "completion-menu.completion": WHITE,
        "completion-menu.completion.current": BG_BLUE + BOLD + WHITE,
        "radio": DIM + WHITE,
        "radio-checked": BOLD + BRIGHT_CYAN,
        "scrollbar": BG_BLACK,
        "scrollbar.button": BG_BLACK + WHITE,
    },
    "COMMANDS": COMMANDS,
    "COMMANDS_LIST": [command.name for command in COMMANDS],
    "MODEL_HANDLER": agent.model_handler,
    "MODEL_OPTIONS": agent.model_options(),
    "MODEL_OPTION_LABELS": agent.model_option_labels(),
    "MODEL_SELECT_HANDLER": agent.select_model,
}

panel = initPanel(PANEL_CONFS)

with patch_stdout():
    panel.run()
