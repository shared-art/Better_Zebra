#!/usr/bin/env python3
"""
print_labels.py
Command-line label printer. Reads a CSV and prints one text label per
non-blank value in column B to a Zebra label printer on Windows.

Column B  = the 2nd column ("sample_container_label" in the sample file).
Label     = 2.00 x 0.25 inches, TEXT ONLY, printed literally.
Printer   = raw ZPL sent to the Windows printer named in zebra_core.py.

For everyday use, prefer the GUI: double-click "Feed the Zebra.bat".

Usage (Windows):
  python print_labels.py yourfile.csv
  python print_labels.py yourfile.csv --preview   (preview without printing)
"""

import os
import sys

from zebra_core import (
    PRINTER_NAME,
    make_zpl,
    print_labels as send_labels,
    read_labels,
)


def pick_file_dialog():
    """Open a file picker when no file is given (double-click case)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Select a CSV to print labels from",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        root.destroy()
        return path
    except Exception:
        return ""


def main():
    args = [a for a in sys.argv[1:]]
    preview = "--preview" in args
    args = [a for a in args if not a.startswith("--")]

    csv_path = args[0] if args else pick_file_dialog()
    if not csv_path:
        print("No file selected.")
        return 1
    if not os.path.isfile(csv_path):
        print(f"File not found: {csv_path}")
        return 1

    labels = read_labels(csv_path)
    if not labels:
        print("No values found in column B.")
        return 1

    print(f"Found {len(labels)} label(s) in column B:")
    for n, lab in enumerate(labels, 1):
        print(f"  {n:>3}. {lab}")

    if preview:
        print("\n--- ZPL preview (first label) ---")
        print(make_zpl(labels[0]))
        print("\nPreview mode: nothing was sent to the printer.")
        return 0

    try:
        send_labels(labels, PRINTER_NAME)
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

    print(f'\nSent {len(labels)} label(s) to "{PRINTER_NAME}".')
    return 0


if __name__ == "__main__":
    sys.exit(main())
