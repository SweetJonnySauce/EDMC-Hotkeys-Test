# EDMC-Hotkeys-Test

Small EDMC UI plugin used to validate `EDMC-Hotkeys` action registration, callback dispatch, and binding assignment display.

## Compatibility Note (EDMC-Hotkeys v3)

This plugin is compatible with the latest `EDMC-Hotkeys` behavior:

- Registers actions via `importlib.import_module("EDMC-Hotkeys.load")` and `register_action(...)`.
- Uses namespaced stable action IDs:
  - `hotkeys_test.on`
  - `hotkeys_test.off`
  - `hotkeys_test.toggle`
  - `hotkeys_test.color`
- Reads assigned bindings via `list_bindings(plugin_name="EDMC-Hotkeys-Test")`.
- Uses the callback signature `(*, payload=None, source="hotkey", hotkey=None)`.
- Expects `Binding.hotkey` as pretty display text (for example `CtrlL+ShiftR+F1`).
- Uses bindings schema v3 (`version: 3`) where each row includes required `plugin`.
- Requires canonical side-specific modifiers only:
  - `ctrl_l`, `ctrl_r`, `alt_l`, `alt_r`, `shift_l`, `shift_r`, `win_l`, `win_r`
  - Generic `ctrl`/`alt`/`shift` are invalid in saved bindings.

## Canonical v3 Binding Examples

`hotkeys_test.on`

```json
{
  "id": "test_on",
  "plugin": "EDMC-Hotkeys-Test",
  "modifiers": ["ctrl_l", "shift_l"],
  "key": "f1",
  "action_id": "hotkeys_test.on",
  "enabled": true
}
```

`hotkeys_test.off`

```json
{
  "id": "test_off",
  "plugin": "EDMC-Hotkeys-Test",
  "modifiers": ["ctrl_l", "shift_l"],
  "key": "f2",
  "action_id": "hotkeys_test.off",
  "enabled": true
}
```

`hotkeys_test.toggle`

```json
{
  "id": "test_toggle",
  "plugin": "EDMC-Hotkeys-Test",
  "modifiers": ["ctrl_l", "shift_l"],
  "key": "f3",
  "action_id": "hotkeys_test.toggle",
  "enabled": true
}
```

`hotkeys_test.color` (red payload)

```json
{
  "id": "test_color_red",
  "plugin": "EDMC-Hotkeys-Test",
  "modifiers": ["ctrl_l", "shift_l"],
  "key": "f4",
  "action_id": "hotkeys_test.color",
  "payload": {"color": "red"},
  "enabled": true
}
```

## Manual Verification Checklist

1. Start EDMC with both `EDMC-Hotkeys` and `EDMC-Hotkeys-Test` enabled.
2. Open the `EDMC-Hotkeys-Test` panel.
3. Confirm actions register:
   - Check EDMC log for lines like `Registered action 'hotkeys_test.on' with EDMC-Hotkeys`.
4. Confirm assigned hotkeys load from API at startup (`list_bindings("EDMC-Hotkeys-Test")`):
   - Legend should show resolved hotkeys instead of `Unconfirmed` for configured bindings.
   - If you use the sample rows above, confirm entries for `test_on`, `test_off`, `test_toggle`, and `test_color_red` appear with expected pretty hotkey strings.
5. Confirm callback hotkey/source forwarding:
   - Trigger a binding and verify logs include `source` and `hotkey` in action callback log messages.
6. Confirm payload color handling:
   - Trigger a color binding (`hotkeys_test.color`) with payload `{"color": "..."}`.
   - Verify color block updates to the payload color.
7. Confirm bindings changes are reflected:
   - Change a binding in EDMC-Hotkeys preferences, save, then click `Refresh Hotkeys`.
   - Verify the legend updates to the new pretty hotkey string for the affected action.
8. Confirm independent control behavior:
   - `hotkeys_test.on/off` only changes the on/off button.
   - `hotkeys_test.toggle` only changes the toggle button.
