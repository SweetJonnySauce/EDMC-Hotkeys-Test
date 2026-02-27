"""Minimal EDMC test plugin for EDMC-Hotkeys action registration."""

from __future__ import annotations

import importlib
import logging
import os
import tkinter as tk
import tkinter.ttk as ttk
from typing import Any, Optional


plugin_name = "EDMC-Hotkeys-Test"
ACTION_ON = "On"
ACTION_OFF = "Off"
ACTION_TOGGLE = "Toggle"
ACTION_COLOR = "Color"


def _build_plugin_logger(name: str) -> logging.Logger:
    try:
        from config import appcmdname, appname  # type: ignore

        base_logger_name = appcmdname if os.getenv("EDMC_NO_UI") else appname
        return logging.getLogger(f"{base_logger_name}.{name}")
    except Exception:
        return logging.getLogger(name)


logger = _build_plugin_logger(plugin_name)
_hotkeys_api: Optional[Any] = None
_registered_action_ids: set[str] = set()

_power_on = False
_toggle_on = False
_color_name = "gray"

_ui_frame: Optional[tk.Frame] = None
_ui_power_button: Optional[tk.Button] = None
_ui_toggle_button: Optional[tk.Button] = None
_ui_color_block: Optional[tk.Label] = None
_ui_legend_var: Optional[tk.StringVar] = None
_ui_root: Optional[tk.Widget] = None


def plugin_start3(plugin_dir: str) -> str:
    del plugin_dir
    _register_hotkey_actions()
    return plugin_name


def plugin_stop() -> None:
    global _hotkeys_api, _ui_frame, _ui_power_button, _ui_toggle_button, _ui_color_block, _ui_legend_var, _ui_root
    _hotkeys_api = None
    _registered_action_ids.clear()
    _ui_frame = None
    _ui_power_button = None
    _ui_toggle_button = None
    _ui_color_block = None
    _ui_legend_var = None
    _ui_root = None


def plugin_app(parent: tk.Widget) -> tk.Frame:
    global _ui_frame, _ui_power_button, _ui_toggle_button, _ui_color_block, _ui_legend_var, _ui_root

    frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="EDMC-Hotkeys Test").grid(row=0, column=0, sticky="w", padx=6, pady=(4, 2))

    power_button = tk.Button(frame, width=14, command=_manual_toggle_power)
    power_button.grid(row=1, column=0, sticky="w", padx=6, pady=2)

    toggle_button = tk.Button(frame, width=14, command=_manual_toggle_toggle)
    toggle_button.grid(row=2, column=0, sticky="w", padx=6, pady=2)

    color_block = tk.Label(frame, text="", width=16, height=2, relief=tk.SUNKEN, bd=1)
    color_block.grid(row=3, column=0, sticky="w", padx=6, pady=(4, 6))

    legend_var = tk.StringVar(value="Bindings in EDMC-Hotkeys:\nUnconfirmed")
    ttk.Label(frame, textvariable=legend_var, justify=tk.LEFT).grid(
        row=1, column=1, rowspan=3, sticky="nw", padx=(16, 6), pady=2
    )

    _ui_frame = frame
    _ui_power_button = power_button
    _ui_toggle_button = toggle_button
    _ui_color_block = color_block
    _ui_legend_var = legend_var
    _ui_root = frame.winfo_toplevel()
    try:
        _ui_root.bind("<FocusIn>", _on_main_focus_in, add="+")
    except Exception:
        pass

    _apply_ui_state()
    _register_hotkey_actions()
    _refresh_hotkeys_from_api()
    return frame


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    del cmdr, is_beta
    _refresh_hotkeys_from_api()


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
    if _ui_power_button is not None:
        if _power_on:
            _ui_power_button.configure(text="ON", bg="#2f8f2f", fg="white", activebackground="#3ca43c")
        else:
            _ui_power_button.configure(text="OFF", bg="#9a2f2f", fg="white", activebackground="#b63b3b")

    if _ui_toggle_button is not None:
        if _toggle_on:
            _ui_toggle_button.configure(text="Toggle ON", bg="#2f8f2f", fg="white", activebackground="#3ca43c")
        else:
            _ui_toggle_button.configure(text="Toggle OFF", bg="#9a2f2f", fg="white", activebackground="#b63b3b")

    if _ui_color_block is not None:
        try:
            _ui_color_block.configure(bg=_color_name)
        except tk.TclError:
            logger.warning("Invalid color '%s'; using gray", _color_name)
            _ui_color_block.configure(bg="gray")


def _ensure_hotkeys_api() -> Optional[Any]:
    global _hotkeys_api
    if _hotkeys_api is not None:
        return _hotkeys_api
    try:
        _hotkeys_api = importlib.import_module("EDMC-Hotkeys.load")
    except Exception as exc:
        logger.debug("Could not import EDMC-Hotkeys.load", exc_info=exc)
        return None
    return _hotkeys_api


def _register_hotkey_actions() -> None:
    hotkeys_api = _ensure_hotkeys_api()
    if hotkeys_api is None:
        return

    action_type = getattr(hotkeys_api, "Action", None)
    if action_type is None:
        logger.warning("EDMC-Hotkeys API does not expose Action")
        return

    actions = [
        action_type(id=ACTION_ON, label="Turn On", plugin=plugin_name, callback=_action_turn_on, thread_policy="main"),
        action_type(id=ACTION_OFF, label="Turn Off", plugin=plugin_name, callback=_action_turn_off, thread_policy="main"),
        action_type(id=ACTION_TOGGLE, label="Toggle", plugin=plugin_name, callback=_action_toggle, thread_policy="main"),
        action_type(
            id=ACTION_COLOR,
            label="Set Color",
            plugin=plugin_name,
            callback=_action_change_color,
            params_schema={
                "type": "object",
                "properties": {"color": {"type": "string"}},
                "required": ["color"],
            },
            thread_policy="main",
            cardinality="multi",
        ),
    ]

    for action in actions:
        if action.id in _registered_action_ids:
            continue

        try:
            ok = hotkeys_api.register_action(action)
        except Exception as exc:
            logger.warning("Failed to register action '%s'", action.id)
            logger.debug("register_action failure", exc_info=exc)
            continue

        if ok or hotkeys_api.get_action(action.id) is not None:
            _registered_action_ids.add(action.id)
            logger.info("Registered action '%s'", action.id)
    _refresh_hotkeys_from_api()


def _on_main_focus_in(event: tk.Event) -> None:
    del event
    _refresh_hotkeys_from_api()


def _refresh_hotkeys_from_api() -> None:
    hotkeys_api = _ensure_hotkeys_api()
    if hotkeys_api is None:
        return

    try:
        bindings = hotkeys_api.list_bindings(plugin_name=plugin_name)
    except Exception as exc:
        logger.debug("list_bindings failed", exc_info=exc)
        return

    if not isinstance(bindings, list):
        return

    lines = ["Bindings in EDMC-Hotkeys:"]
    for binding in bindings:
        action_id = _binding_field(binding, "action_id", "")
        hotkey = _binding_field(binding, "hotkey", "")
        payload = _binding_field(binding, "payload", None)
        enabled = bool(_binding_field(binding, "enabled", True))
        if not action_id or not hotkey or not enabled:
            continue

        label = str(action_id)
        if action_id == ACTION_COLOR and isinstance(payload, dict):
            color_name = payload.get("color")
            if isinstance(color_name, str) and color_name.strip():
                label = f"{label}({color_name.strip()})"

        lines.append(f"{hotkey} -> {label}")

    if len(lines) == 1:
        lines.append("Unconfirmed")

    if _ui_legend_var is not None:
        _ui_legend_var.set("\n".join(lines))


def _binding_field(binding: Any, name: str, default: Any) -> Any:
    if isinstance(binding, dict):
        return binding.get(name, default)
    return getattr(binding, name, default)


def _action_turn_on(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey", hotkey: Optional[str] = None) -> None:
    del payload
    logger.info("%s from %s (hotkey=%s)", ACTION_ON, source, hotkey)
    _set_power(True)


def _action_turn_off(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey", hotkey: Optional[str] = None) -> None:
    del payload
    logger.info("%s from %s (hotkey=%s)", ACTION_OFF, source, hotkey)
    _set_power(False)


def _action_toggle(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey", hotkey: Optional[str] = None) -> None:
    del payload
    logger.info("%s from %s (hotkey=%s)", ACTION_TOGGLE, source, hotkey)
    _set_toggle(not _toggle_on)


def _action_change_color(*, payload: Optional[dict[str, Any]] = None, source: str = "hotkey", hotkey: Optional[str] = None) -> None:
    logger.info("%s from %s (hotkey=%s)", ACTION_COLOR, source, hotkey)
    if not isinstance(payload, dict):
        logger.warning("Color action requires payload with 'color'")
        return

    color_name = payload.get("color")
    if not isinstance(color_name, str) or not color_name.strip():
        logger.warning("Color action payload missing valid 'color'")
        return

    _set_color_named(color_name)
