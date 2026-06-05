# pdf-jpg-tools

Python scripts to convert between PDF and JPG, batch-convert entire folders, and crop passport images — all from the Windows right-click context menu.

## Scripts

| Script | What it does |
|---|---|
| `pdf_to_jpg.py` | Converts each page of a PDF to a JPG image |
| `jpg_to_pdf.py` | Converts a JPG image to a PDF file |
| `folder_to_jpg.py` | Converts all PDFs and images (PNG, BMP, JPEG) in a folder and its subfolders to JPG |
| `crop_passport.py` | Detects the passport data page in an image and crops it out (perspective-corrected); scans subfolders when given a folder |

Output files are saved in the same folder as the input file.

## Requirements

Python 3.7+ and the following packages:

```
pip install pymupdf pillow opencv-python
```

## Usage

### From the right-click context menu (Windows)

1. Run `install_context_menus.reg` (double-click and accept the prompt)
2. Use the new right-click options:

| Where you right-click | Menu option |
|---|---|
| A `.pdf` file | **Convert to JPG** |
| A `.jpg` / `.jpeg` file | **Convert to PDF** |
| A `.jpg` / `.jpeg` / `.png` / `.bmp` file | **Crop Passport to Details** |
| A folder | **Convert All to JPG** |
| A folder | **Crop Passports to Details** |
| Inside a folder (on empty space) | **Convert All to JPG** |
| Inside a folder (on empty space) | **Crop Passports to Details** |

A progress window appears and closes automatically when done.

### From the command line

```
python pdf_to_jpg.py "path\to\file.pdf"
python jpg_to_pdf.py "path\to\file.jpg"
python folder_to_jpg.py "path\to\folder"
python crop_passport.py "path\to\image.jpg"
python crop_passport.py "path\to\folder"
```

## Notes

- **Batch selection**: selecting multiple files at once and right-clicking will process them all in a single progress window.
- **Folder conversion**: `folder_to_jpg.py` scans all subfolders recursively.
- **Passport cropping**: uses edge detection to find the passport rectangle and applies a perspective correction to straighten tilted photos. Output is saved as `filename_cropped.jpg`. Already-cropped files are skipped automatically. Scans all subfolders recursively when given a folder.
- **Context menu not visible?** On Windows 11, right-click and choose **Show more options** — the entries appear there. To make them show in the main menu, run this in PowerShell (once):
  ```
  reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve
  ```
  Then restart Explorer.
