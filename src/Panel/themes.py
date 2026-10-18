BASE_STYLE = {
    "model": "",
    "radio": "fg:#7f8c9f",
    "radio-checked": "fg:#45c7e8 bold",
    "error": "fg:#ff6b6b",
    "context-low": "fg:#4caf80",
    "context-warning": "fg:#e9b949",
    "context-full": "fg:#ef6461 bold",
}


def _palette(background, foreground, muted, accent, user_background):
    return {
        "": f"bg:{background} {foreground}",
        "chat-area": f"bg:{background} {foreground}",
        "model": foreground,
        "user": f"bg:{user_background} {foreground}",
        "hint": muted,
        "separator": muted,
        "input-field": f"bg:{user_background} {foreground}",
        "completion-menu": f"bg:{user_background} {foreground}",
        "completion-menu.completion.current": f"bg:{accent} {background}",
        "radio": f"fg:{muted}",
        "radio-checked": f"fg:{accent} bold",
        "scrollbar": f"bg:{background}",
        "scrollbar.button": f"bg:{accent}",
    }


THEMES = {
    "default": {},
    "dark": _palette("#151922", "#e5e9f0", "#8692a6", "#88c0d0", "#293447"),
    "light": {
        **_palette("#f7f8fa", "#202938", "#526174", "#2869b8", "#dce8f5"),
        "error": "fg:#b42318",
        "context-low": "fg:#18794e",
        "context-warning": "fg:#946200",
        "context-full": "fg:#b42318 bold",
    },
    "ocean": _palette("#0c202b", "#daf4f4", "#81a9b7", "#46d3c0", "#173f50"),
}
