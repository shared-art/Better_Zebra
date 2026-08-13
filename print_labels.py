#!/usr/bin/env python3
"""
print_labels.py
Reads a CSV and prints one text label per non-blank value in column B
to a Zebra label printer on Windows.

Column B  = the 2nd column ("sample_container_label" in the sample file).
Label     = 2.00 x 0.25 inches, TEXT ONLY, printed literally.
Printer   = raw ZPL sent to the Windows printer named below.

Usage (Windows):
  - Drag a .csv file onto "Print Labels.bat"  (easiest)
  - or double-click "Print Labels.bat" and pick a file
  - or:  python print_labels.py yourfile.csv
  - preview without printing:  python print_labels.py yourfile.csv --preview
"""

import csv
import os
import sys

# ----------------------------------------------------------------------
# SETTINGS -- edit these if anything changes
# ----------------------------------------------------------------------
PRINTER_NAME = "Zebra ZD220 1"   # exact Windows printer name
COLUMN_INDEX = 1                 # 0 = column A, 1 = column B, ...
SKIP_HEADER  = True              # first row is a header row
DPI          = 203               # ZD220 is a 203 dpi printer
LABEL_WIDTH_IN  = 2.00
LABEL_HEIGHT_IN = 0.25
FONT_HEIGHT_DOTS = 30            # text height in dots (~0.15"); lower to fit long text
COPIES = 1                       # copies of each label
# ----------------------------------------------------------------------

WIDTH_DOTS  = int(LABEL_WIDTH_IN  * DPI)   # 406
HEIGHT_DOTS = int(LABEL_HEIGHT_IN * DPI)   # ~50


def read_labels(csv_path):
    """Return the list of non-blank values from the chosen column."""
    labels = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if SKIP_HEADER and i == 0:
                continue
            if len(row) <= COLUMN_INDEX:
                continue
            value = row[COLUMN_INDEX].strip()
            if value:
                labels.append(value)
    return labels


def make_zpl(text):
    """Build a ZPL string for one text-only label."""
    # ZPL control chars must not appear in the data
    safe = text.replace("^", " ").replace("~", " ")
    y = max(0, (HEIGHT_DOTS - FONT_HEIGHT_DOTS) // 2)  # vertical centering
    return (
        "^XA"
        "^CI28"                       # UTF-8
        f"^PW{WIDTH_DOTS}"            # print width
        f"^LL{HEIGHT_DOTS}"          # label length
        f"^FO0,{y}"
        f"^A0N,{FONT_HEIGHT_DOTS},{FONT_HEIGHT_DOTS}"
        f"^FB{WIDTH_DOTS},1,0,C,0"   # 1 line, centered in full width
        f"^FD{safe}^FS"
        f"^PQ{COPIES}"               # quantity
        "^XZ"
    )


def send_raw_to_printer(printer_name, data_bytes):
    """Send raw bytes to a Windows printer via the winspool API (no pip installs)."""
    if os.name != "nt":
        raise RuntimeError("Raw printing only works on Windows.")

    import ctypes
    from ctypes import wintypes

    winspool = ctypes.WinDLL("winspool.drv")

    class DOC_INFO_1(ctypes.Structure):
        _fields_ = [
            ("pDocName", wintypes.LPWSTR),
            ("pOutputFile", wintypes.LPWSTR),
            ("pDatatype", wintypes.LPWSTR),
        ]

    hPrinter = wintypes.HANDLE()
    if not winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
        raise RuntimeError(
            f'Could not open printer "{printer_name}". '
            "Check the exact name in Windows > Settings > Printers."
        )
    try:
        doc = DOC_INFO_1("CSV Labels", None, "RAW")
        job = winspool.StartDocPrinterW(hPrinter, 1, ctypes.byref(doc))
        if not job:
            raise RuntimeError("StartDocPrinter failed.")
        try:
            winspool.StartPagePrinter(hPrinter)
            written = wintypes.DWORD(0)
            winspool.WritePrinter(
                hPrinter, data_bytes, len(data_bytes), ctypes.byref(written)
            )
            winspool.EndPagePrinter(hPrinter)
        finally:
            winspool.EndDocPrinter(hPrinter)
    finally:
        winspool.ClosePrinter(hPrinter)


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

    payload = "".join(make_zpl(lab) for lab in labels).encode("utf-8")
    try:
        send_raw_to_printer(PRINTER_NAME, payload)
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

    print(f'\nSent {len(labels)} label(s) to "{PRINTER_NAME}".')
    return 0


if __name__ == "__main__":
    sys.exit(main())
