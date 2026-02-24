"""EDMC test plugin for EDMC-Hotkeys action registration."""

from __future__ import annotations

import logging
import os
import tkinter as tk
import tkinter.ttk as ttk
from typing import Any, Optional

import plug


ActionType = None


def _build_plugin_logger(name: str) -> logging.Logger:
    try:
        from config import appcmdname, appname  # type: ignore

        base_logger_name = appcmdname if os.getenv("EDMC_NO_UI") else appname
        return logging.getLogger(f"{base_logger_name}.{name}")
    except Exception:
        return logging.getLogger(name)


plugin_name = "EDMC-Hotkeys-Test"
logger = _build_plugin_logger(plugin_name)

_power_on = False
_toggle_on = False
_color_name = "gray"
_registered_action_ids: set[str] = set()

ACTION_ON = "edmc_hotkeys_test.on"
ACTION_OFF = "edmc_hotkeys_test.off"
ACTION_TOGGLE = "edmc_hotkeys_test.toggle"
ACTION_COLOR = "edmc_hotkeys_test.color"
LEGEND_TEXT = (
    "Legend (Hotkey -> Action)\n"
    "Ctrl+Shift+F1 -> On\n"
    "Ctrl+Shift+F2 -> Off\n"
    "Ctrl+Shift+F3 -> Toggle\n"
    "Ctrl+Shift+F4 -> Color Red\n"
    "Ctrl+Shift+F5 -> Color Lime\n"
    "Ctrl+Shift+F6 -> Color DeepSkyBlue"
)


class _UiState:
    def __init__(self, frame: tk.Frame, power_button: tk.Button, toggle_button: tk.Button, color_block: tk.Label):
        self.frame = frame
        self.power_button = power_button
        self.toggle_button = toggle_button
        self.color_block = color_block


_ui: Optional[_UiState] = None


def plugin_start3(plugin_dir: str) -> str:
    del plugin_dir
    _register_hotkey_actions()
    return plugin_name


def plugin_stop() -> None:
    global _ui
    _ui = None
    _registered_action_ids.clear()


def plugin_app(parent: tk.Widget) -> tk.Frame:
    global _ui

    frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    title = ttk.Label(frame, text="EDMC-Hotkeys Test")
    title.grid(row=0, column=0, sticky="w", padx=6, pady=(4, 2))

    power_button = tk.Button(frame, width=14, command=_manual_toggle_power)
    power_button.grid(row=1, column=0, sticky="w", padx=6, pady=2)

    toggle_button = tk.Button(frame, text="Toggle", width=14, command=_manual_toggle_toggle)
    toggle_button.grid(row=2, column=0, sticky="w", padx=6, pady=2)

    color_block = tk.Label(frame, text="", width=16, height=2, relief=tk.SUNKEN, bd=1)
    color_block.grid(row=3, column=0, sticky="w", padx=6, pady=(4, 6))

    legend_label = ttk.Label(frame, text=LEGEND_TEXT, justify=tk.LEFT)
    legend_label.grid(row=1, column=1, rowspan=4, sticky="nw", padx=(16, 6), pady=2)

    _ui = _UiState(
        frame=frame,
        power_button=power_button,
        toggle_button=toggle_button,
        color_block=color_block,
    )
    _apply_ui_state()
    _register_hotkey_actions()
    return frame


def journal_entry(
    cmdr: str,
    is_beta: bool,
    system: str,
    station: str,
    entry: dict[str, Any],
    state: dict[str, Any],
) -> Optional[str]:
    del cmdr, is_beta, system, station, entry, state
    _register_hotkey_actions()
    return None


def dashboard_entry(cmdr: str, is_beta: bool, entry: dict[str, Any]) -> None:
    del cmdr, is_beta, entry
    _register_hotkey_actions()


def _manual_toggle_power() -> None:
    _set_power(not _power_on)


def _manual_toggle_toggle() -> None:
    _set_toggle(not _toggle_on)


def _set_power(value: bool) -> None:
    global _power_on
    _power_on = bool(value)
    _apply_ui_state()


def _set_toggle(value: bool) -> None:
    global _toggle_on
    _toggle_on = bool(value)
    _apply_ui_state()


def _set_color_named(color_name: str) -> None:
    global _color_name
    normalized = str(color_name).strip()
    if not normalized:
        return
    _color_name = normalized
    _apply_ui_state()


def _apply_ui_state() -> None:
    if _ui is None:
        return

    if _power_on:
        _ui.power_button.configure(text="ON", bg="#2f8f2f", fg="white", activebackground="#3ca43c")
    else:
        _ui.power_button.configure(text="OFF", bg="#9a2f2f", fg="white", activebackground="#b63b3b")

    if _toggle_on:
        _ui.toggle_button.configure(text="Toggle ON", bg="#2f8f2f", fg="white", activebackground="#3ca43c")
    else:
        _ui.toggle_button.configure(text="Toggle OFF", bg="#9a2f2f", fg="white", activebackground="#b63b3b")

    try:
        _ui.color_block.configure(bg=_color_name)
    except tk.TclError:
        logger.warning("Invalid color '%s'; using gray", _color_name)
        _ui.color_block.configure(bg="gray")


def _register_hotkey_actions() -> None:
    action_type = _resolve_action_type()
    if action_type is None:
        logger.warning("Unable to import edmc_hotkeys.registry.Action; hotkey actions not registered")
        return

    for action in _build_actions(action_type):
        if action.id in _registered_action_ids:
            continue

        result = plug.invoke("EDMC-Hotkeys", None, "register_action", action)
        if result is True:
            _registered_action_ids.add(action.id)
            logger.info("Registered action '%s' with EDMC-Hotkeys", action.id)
            continue

        existing_action = plug.invoke("EDMC-Hotkeys", None, "get_action", action.id)
        if existing_action is not None:
            _registered_action_ids.add(action.id)
            logger.info("Action '%s' already present in EDMC-Hotkeys", action.id)
            continue

        logger.debug("EDMC-Hotkeys action registration pending for '%s'", action.id)


def _resolve_action_type() -> Any:
    global ActionType
    if ActionType is not None:
        return ActionType
    try:
        from edmc_hotkeys.registry import Action
    except Exception:
        return None
    ActionType = Action
    return ActionType


def _build_actions(action_type: Any) -> list[Any]:
    return [
        action_type(
            id=ACTION_ON,
            label="Hotkeys Test: Turn On",
            plugin=plugin_name,
            callback=_action_turn_on,
        ),
        action_type(
            id=ACTION_OFF,
            label="Hotkeys Test: Turn Off",
            plugin=plugin_name,
            callback=_action_turn_off,
        ),
        action_type(
            id=ACTION_TOGGLE,
            label="Hotkeys Test: Toggle",
            plugin=plugin_name,
            callback=_action_toggle,
        ),
        action_type(
            id=ACTION_COLOR,
            label="Hotkeys Test: Change Color",
            plugin=plugin_name,
            callback=_action_change_color,
            params_schema={
                "type": "object",
                "properties": {
                    "color": {"type": "string"},
                },
                "required": ["color"],
            },
        ),
    ]


def _action_turn_on(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey") -> None:
    del payload, source
    _set_power(True)


def _action_turn_off(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey") -> None:
    del payload, source
    _set_power(False)


def _action_toggle(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey") -> None:
    del payload, source
    _set_toggle(not _toggle_on)


def _action_change_color(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey") -> None:
    del source
    if not isinstance(payload, dict):
        logger.warning("Color action requires payload with a 'color' string")
        return

    candidate = payload.get("color")
    if not isinstance(candidate, str) or not candidate.strip():
        logger.warning("Color action payload is missing a valid 'color' value")
        return

    _set_color_named(candidate)
