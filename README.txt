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
  Print Labels.bat   <- what you use (drag a CSV onto it)
  print_labels.py    <- the program
  README.txt         <- this file
Keep all three in the same folder.

One-time setup
--------------
1. Install Python (if not already): https://www.python.org/downloads/
   During install, CHECK the box "Add python.exe to PATH".
2. Confirm the printer name is exactly "Zebra ZD220 1":
   Windows Settings > Bluetooth & devices > Printers & scanners.
   If it differs, open print_labels.py in Notepad and edit the
   PRINTER_NAME line near the top.

How to use
----------
* Drag a .csv file onto "Print Labels.bat"  -> it prints immediately.
* Or double-click "Print Labels.bat" and pick a file.
A window shows the list of labels it sent, then waits for a key press.

Try it first without printing
------------------------------
Open Command Prompt in this folder and run:
    python print_labels.py yourfile.csv --preview
It lists the labels and shows the ZPL, but sends nothing to the printer.

Tuning
------
Open print_labels.py in Notepad to change any of these (top of file):
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
