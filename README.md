# pdf-jpg-tools

Two lightweight Python scripts to convert between PDF and JPG on Windows, with a progress bar GUI and right-click context menu integration.

## Scripts

| Script | What it does |
|---|---|
| `pdf_to_jpg.py` | Converts each page of a PDF to a JPG image |
| `jpg_to_pdf.py` | Converts a JPG image to a PDF file |

Output files are saved in the same folder as the input file.

## Requirements

Python 3.7+ and the following packages:

```
pip install pymupdf pillow
```

## Usage

### From the command line

```
python pdf_to_jpg.py "path\to\file.pdf"
python jpg_to_pdf.py "path\to\file.jpg"
```

### From the right-click context menu (Windows)

1. Run `install_context_menus.reg` (double-click and accept the prompt)
2. Right-click any `.pdf` or `.jpg` file in Explorer
3. Select **Convert to JPG** or **Convert to PDF**

A small progress window will appear and close automatically when done. If you select multiple files at once, they are all processed in a single batch.
