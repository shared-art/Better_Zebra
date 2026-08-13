CSV LABEL PRINTER  -  Zebra ZD220
=================================

What it does
------------
Reads a CSV and prints ONE label for every non-blank value in column B
(the "sample_container_label" column). Header row and blank rows are
skipped automatically. Text is printed exactly as written.

Label size : 2.00 x 0.25 in
Printer    : "Zebra ZD220 1"

Files
-----
  Feed the Zebra.bat   <- what you use (double-click to launch the GUI)
  zebra_core.py       <- shared CSV/ZPL/printing logic
  gui/server.py        <- local web server for the GUI
  gui/static/           <- the GUI's page, styles, and animation
  print_labels.py     <- command-line version (for scripting/automation)
  README.txt          <- this file
Keep the folder structure intact.

One-time setup
--------------
1. Install Python (if not already): https://www.python.org/downloads/
   During install, CHECK the box "Add python.exe to PATH".
2. Confirm the printer name is exactly "Zebra ZD220 1":
   Windows Settings > Bluetooth & devices > Printers & scanners.
   If it differs, open zebra_core.py in Notepad and edit the
   PRINTER_NAME line near the top.

How to use (GUI, primary workflow)
-----------------------------------
* Double-click "Feed the Zebra.bat". It opens a browser tab with a
  zebra standing on screen.
* Drag your CSV file onto the zebra and drop it near its mouth.
* Its stomach rumbles while the file is read and printed, then it
  turns to face you and smiles, and a sponge sidekick pops up on its
  back to celebrate for a few seconds.
* Check "Test mode" beneath the zebra to preview a CSV (parse and
  show the label count) without sending anything to the printer.
* Closing the console window that opened alongside the browser tab
  stops the GUI's local server.

Command line (secondary, for scripting)
----------------------------------------
* Drag a .csv file onto print_labels.py, or run:
    python print_labels.py yourfile.csv
* Preview without printing:
    python print_labels.py yourfile.csv --preview
It lists the labels and shows the ZPL, but sends nothing to the printer.

Tuning
------
Open zebra_core.py in Notepad to change any of these (top of file):
  PRINTER_NAME       exact Windows printer name
  COLUMN_INDEX       0=col A, 1=col B (default), 2=col C ...
  FONT_HEIGHT_DOTS   text size; lower it if long values get cut off
  COPIES             copies of each label

Troubleshooting
---------------
* "Could not open printer" -> the PRINTER_NAME doesn't match Windows.
  Copy the exact name from Printers & scanners.
* Nothing prints but no error -> make sure the printer is set to the
  right media (2x0.25 label, gap sensing) and is online.
* Text cut off -> lower FONT_HEIGHT_DOTS (e.g. 24 or 20).
