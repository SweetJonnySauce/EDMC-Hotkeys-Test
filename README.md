# EDMC-Hotkeys-Test

UI test plugin for validating [`EDMCHotkeys`](https://github.com/SweetJonnySauce/EDMCHotkeys) integration inside EDMC.

This plugin exists to verify:
- Action registration with `EDMCHotkeys`
- Callback dispatch (including `source`, `hotkey`, and `payload`)
- Binding lookup/rendering with `list_bindings(plugin_name="EDMC-Hotkeys-Test")`

## Installation
- Download zip file and extract into EDMC Plugin directory

## How It Works

### Plugin lifecycle
- `plugin_start3(...)` registers actions as soon as the plugin loads.
- `plugin_app(...)` builds the test UI, reapplies current state, re-registers actions, and refreshes binding legend text.
- `journal_entry(...)` and `dashboard_entry(...)` call registration again as a load-order safety net.
- `prefs_changed(...)` refreshes the legend from current bindings.
- `plugin_stop()` clears cached API references and UI pointers.

### Registered actions
The plugin registers 4 actions with `thread_policy="main"`:
- `On` (`Turn On`) -> sets power state to ON
- `Off` (`Turn Off`) -> sets power state to OFF
- `Toggle` (`Toggle`) -> flips toggle state
- `Color` (`Set Color`) -> sets color block from payload

`Color` is registered with:
- `cardinality="multi"` This allows for multiple hotkey bindings
- `params_schema` requiring `{ "color": "<string>" }`

### Callback signature and behavior
Each callback uses:

```python
(*, payload=None, source="hotkey", hotkey=None)
```

Behavior:
- Logs action with source/hotkey context.
- `On` and `Off` only affect the power button.
- `Toggle` only affects the toggle button.
- `Color` requires `payload.color`; invalid/missing values log warnings.

## UI Behavior

The plugin panel includes:
- `ON/OFF` button (manual test control)
- `Toggle ON/OFF` button (manual test control)
- Color preview block
- Binding legend text area

Legend behavior:
- Starts as `Bindings in EDMCHotkeys:\nUnconfirmed`
- Refreshes from `list_bindings(plugin_name="EDMC-Hotkeys-Test")`
- Shows only bindings that have `action_id`, `hotkey`, and `enabled=true`
- For `Color`, legend shows payload detail like `Color(red)`
- Refreshes on panel load, prefs save, and main-window focus-in

## Binding Format (v3)

The sample `bindings.json` in this repo uses schema `version: 3` and plugin name `EDMC-Hotkeys-Test`. This is only for reference and is not needed for this plugin or for `EDMCHotkeys`

Example rows:

```json
{
  "id": "hotkeys_test_on",
  "plugin": "EDMC-Hotkeys-Test",
  "modifiers": ["ctrl_l", "shift_l"],
  "key": "f1",
  "action_id": "On",
  "enabled": true
}
```

```json
{
  "id": "hotkeys_test_color_red",
  "plugin": "EDMC-Hotkeys-Test",
  "modifiers": ["ctrl_l", "shift_l"],
  "key": "f4",
  "action_id": "Color",
  "enabled": true,
  "payload": {
    "color": "red"
  }
}
```

## Quick Manual Verification

1. Enable both `EDMCHotkeys` and `EDMC-Hotkeys-Test` in EDMC.
2. Open the `EDMC-Hotkeys-Test` panel.
3. Confirm log lines like `Registered action 'On'`, `Registered action 'Off'`, `Registered action 'Toggle'`, `Registered action 'Color'`.
4. Press configured hotkeys and verify:
   - Buttons/color update as expected.
   - Logs include `source` and `hotkey`.
5. Change bindings in `EDMCHotkeys`, save prefs, and verify legend updates.
