#!/usr/bin/env python3
"""Type clipboard contents line-by-line, pressing Tab between lines.

Reads the clipboard, then after a countdown "types" each line into the
focused window, followed by a configurable number of Tab key presses.
Useful for filling forms spread across multiple tabs of input fields.
"""

import argparse
import sys
import time

try:
    from pynput import keyboard
except ImportError:
    print("Missing dependency. Install with: pip install pynput", file=sys.stderr)
    sys.exit(1)


def get_clipboard_lines(max_items):
    # macOS, Windows: pbpaste / ctypes; fall back to xclip/xsel on Linux.
    import platform
    system = platform.system()
    text = None
    if system == "Darwin":
        import subprocess
        text = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, check=True
        ).stdout
    elif system == "Windows":
        import ctypes
        CF_UNICODETEXT = 13
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        user32.OpenClipboard(0)
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if handle:
                locked = kernel32.GlobalLock(handle)
                try:
                    text = ctypes.c_wchar_p(locked).value
                finally:
                    kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()
    else:
        import shutil
        text = shutil.paste()
    if text is None:
        print("Could not read clipboard.", file=sys.stderr)
        sys.exit(1)
    lines = [line for line in text.splitlines() if line.strip()]
    if max_items:
        lines = lines[:max_items]
    if not lines:
        print("Clipboard is empty.", file=sys.stderr)
        sys.exit(1)
    return lines


def clear_field(controller):
    # Select all (Cmd+A on macOS, Ctrl+A elsewhere), then delete.
    import platform
    mod = keyboard.Key.cmd if platform.system() == "Darwin" else keyboard.Key.ctrl
    with controller.pressed(mod):
        controller.press("a")
        controller.release("a")
    controller.press(keyboard.Key.backspace)
    controller.release(keyboard.Key.backspace)


def type_lines(lines, tabs, delay):
    controller = keyboard.Controller()
    for i, line in enumerate(lines):
        clear_field(controller)
        time.sleep(delay)
        controller.type(line)
        if i < len(lines) - 1:
            for _ in range(tabs):
                controller.press(keyboard.Key.tab)
                controller.release(keyboard.Key.tab)
                time.sleep(delay)
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="Type clipboard contents into input boxes, Tab-separated."
    )
    parser.add_argument(
        "-t", "--tabs", type=int, default=2,
        help="number of Tab presses after each line (default: 2)",
    )
    parser.add_argument(
        "-d", "--delay", type=float, default=0.05,
        help="delay in seconds between key presses (default: 0.05)",
    )
    parser.add_argument(
        "-c", "--countdown", type=float, default=5.0,
        help="countdown in seconds before typing starts (default: 5)",
    )
    parser.add_argument(
        "-n", "--max-items", type=int, default=None,
        help="only type the first N lines",
    )
    args = parser.parse_args()

    lines = get_clipboard_lines(args.max_items)

    print(f"Read {len(lines)} lines from clipboard:")
    for i, line in enumerate(lines):
        preview = line if len(line) <= 60 else line[:57] + "..."
        print(f"  {i + 1:3d}. {preview}")
    print(f"\nEach line will be followed by {args.tabs} Tab press(es).")

    print(f"\nClick into the first input box. Typing starts in {args.countdown}s...")
    for remaining in range(int(args.countdown), 0, -1):
        print(f"  {remaining}...", flush=True)
        time.sleep(1)

    type_lines(lines, args.tabs, args.delay)
    print("\nDone.")


if __name__ == "__main__":
    main()
