# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A desktop Pomodoro timer built with Python + tkinter. Single-file GUI application (`pomodoro.py`, ~530 lines). No external dependencies — uses only Python standard library (`tkinter`, `threading`, `winsound`, `json`).

## Running

```bash
python pomodoro.py          # normal launch (console window appears)
pythonw pomodoro.py         # windowless launch (preferred on Windows)
```

`pomodoro.bat` is the desktop launcher — uses `pythonw` to avoid a console window.

## Commands

```bash
python -m py_compile pomodoro.py   # syntax check (no test suite exists)
```

No build step, no test framework, no linter configured.

## Architecture

`pomodoro.py` contains everything in one file:

- **`load_config()` / `save_config()`** — JSON persistence to `pomodoro_config.json`. Stores durations (in minutes) and `always_on_top` preference.
- **`_draw_round_rect()`** — Canvas helper that draws rounded rectangles via polygon smoothing.
- **`RoundedButton`** — Custom Canvas-based button with hover/disabled states, hex color manipulation, and click handling. All UI buttons use this class.
- **`SettingsDialog`** — Modal `Toplevel` for customizing work/break durations and long-break interval. Writes through `save_config()`.
- **`PomodoroTimer`** — Main application class:
  - Timer engine runs on a daemon thread (`_timer_loop`), ticking every 0.2s. Shared state (`running`, `paused`, `current_sec`, `mode`) is protected by `threading.Lock`.
  - UI updates are scheduled on the main thread via `root.after(0, ...)`.
  - On finish: rings a melody on a separate thread, shows a `Toplevel` notification popup (deferred 50ms via `after` to avoid the `grab_set` deadlock that previously occurred).
  - Mode auto-transitions: work → short break (or long break every N sessions).
- **`main()`** — Creates `Tk` root, centers the window on screen, applies `always_on_top` from config.

## Key constraints

- `grab_set()` on a `Toplevel` before it's fully mapped causes a tkinter deadlock on Windows — this happened before, so notification popups use `after(50, _create)` + `lift()` + `focus_set()` instead.
- `self.mode` is a bare string (`"work"`, `"short_break"`, `"long_break"`). Mode-specific labels are in class constants (`IDLE_LABELS`, `RUNNING_LABELS`, `FINISHED_LABELS`, `POPUP_MESSAGES`).
- Duration config is stored in minutes, converted to seconds at load time.
- `winsound` is Windows-only — this app will not run on macOS/Linux without modification.
