#!/usr/bin/env python3
"""
zebra_core.py
Shared printing logic used by both the CLI (print_labels.py) and the GUI
(gui/server.py): CSV parsing, ZPL generation, and raw Windows printing.
"""

import csv
import os

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

# Default centered text sat a bit high visually; nudge it down ~1/8 of the
# label's height. Bounded by MAX_FONT_HEIGHT_DOTS below so text never runs
# off the label -- there's only HEIGHT_DOTS - FONT_HEIGHT_DOTS of headroom.
DEFAULT_DOWN_NUDGE_DOTS = round(HEIGHT_DOTS / 8)

MIN_FONT_HEIGHT_DOTS = 10
MAX_FONT_HEIGHT_DOTS = HEIGHT_DOTS
H_ALIGNMENTS = {"L", "C", "R"}
V_ALIGNMENTS = {"T", "C", "B"}


def _split_row(line):
    """Split one line on whichever delimiter it actually uses. Some exporters
    write a comma-separated header but tab- or semicolon-separated data rows,
    so the delimiter is picked per line rather than once for the whole file."""
    if "," in line:
        return next(csv.reader([line]))
    if "\t" in line:
        return line.split("\t")
    if ";" in line:
        return line.split(";")
    return [line]


def read_labels_from_rows(lines):
    """Return the list of non-blank values from the chosen column, given an
    iterable of raw text lines (header included)."""
    labels = []
    for i, line in enumerate(lines):
        if SKIP_HEADER and i == 0:
            continue
        row = _split_row(line)
        if len(row) <= COLUMN_INDEX:
            continue
        value = row[COLUMN_INDEX].strip()
        if value:
            labels.append(value)
    return labels


def read_labels(csv_path):
    """Return the list of non-blank values from the chosen column of a CSV file."""
    with open(csv_path, encoding="utf-8-sig") as f:
        return read_labels_from_rows(f.read().splitlines())


def read_labels_from_text(csv_text):
    """Same as read_labels, but from an in-memory CSV string (used by the GUI)."""
    if csv_text.startswith("﻿"):
        csv_text = csv_text[1:]
    return read_labels_from_rows(csv_text.splitlines())


def make_zpl(text, font_height_dots=None, h_align="C", v_align="C"):
    """Build a ZPL string for one text-only label.

    font_height_dots -- override the text size (defaults to FONT_HEIGHT_DOTS).
    h_align -- "L", "C", or "R": horizontal justification within the label width.
    v_align -- "T", "C", or "B": vertical position within the label height.
               "C" (the default) includes a small built-in downward nudge,
               since dead-center reads as slightly high on this label stock.
    """
    # ZPL control chars must not appear in the data
    safe = text.replace("^", " ").replace("~", " ")

    fh = font_height_dots if font_height_dots else FONT_HEIGHT_DOTS
    fh = max(MIN_FONT_HEIGHT_DOTS, min(fh, MAX_FONT_HEIGHT_DOTS))
    headroom = max(0, HEIGHT_DOTS - fh)

    v_align = v_align if v_align in V_ALIGNMENTS else "C"
    if v_align == "T":
        y = 0
    elif v_align == "B":
        y = headroom
    else:
        y = min(headroom, headroom // 2 + DEFAULT_DOWN_NUDGE_DOTS)

    h_align = h_align if h_align in H_ALIGNMENTS else "C"

    return (
        "^XA"
        "^CI28"                       # UTF-8
        f"^PW{WIDTH_DOTS}"            # print width
        f"^LL{HEIGHT_DOTS}"          # label length
        f"^FO0,{y}"
        f"^A0N,{fh},{fh}"
        f"^FB{WIDTH_DOTS},1,0,{h_align},0"   # 1 line, justified in full width
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


def print_labels(labels, printer_name=PRINTER_NAME, font_height_dots=None, h_align="C", v_align="C"):
    """Build ZPL for every label and send it as one job to the printer."""
    payload = "".join(
        make_zpl(lab, font_height_dots=font_height_dots, h_align=h_align, v_align=v_align)
        for lab in labels
    ).encode("utf-8")
    send_raw_to_printer(printer_name, payload)
