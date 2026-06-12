import sys, os, glob
import fitz
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox

def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"

def get_files(folder):
    pdfs, imgs = [], []
    for ext in ["*.pdf", "*.PDF"]:
        pdfs.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    for ext in ["*.png", "*.PNG", "*.bmp", "*.BMP", "*.jpeg", "*.JPEG"]:
        imgs.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    return pdfs, imgs

def convert_pdf(path):
    base = os.path.splitext(path)[0]
    doc = fitz.open(path)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        out = unique_path(f"{base}.jpg" if len(doc) == 1 else f"{base}_page{i+1}.jpg")
        pix.save(out)
    doc.close()
    os.remove(path)

def convert_image(path):
    out = unique_path(os.path.splitext(path)[0] + ".jpg")
    Image.open(path).convert("RGB").save(out)
    os.remove(path)

def run_gui(pdfs, imgs):
    total = len(pdfs) + len(imgs)
    root = tk.Tk()
    root.title("Convert All to JPG")
    root.geometry("420x110")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    label = tk.Label(root, text="Starting...", font=("Segoe UI", 10), anchor="w")
    label.pack(fill="x", padx=20, pady=(15, 4))

    bar = ttk.Progressbar(root, length=380, mode="determinate", maximum=total)
    bar.pack(padx=20)

    errors = []
    done = [0]

    def step(fn, path):
        label.config(text=f"({done[0]+1}/{total})  {os.path.basename(path)}")
        root.update()
        try:
            fn(path)
        except Exception as e:
            errors.append(f"{os.path.basename(path)}: {e}")
        done[0] += 1
        bar["value"] = done[0]
        root.update()

    def work():
        for path in pdfs:
            step(convert_pdf, path)
        for path in imgs:
            step(convert_image, path)
        msg = f"Done with {len(errors)} error(s)." if errors else f"Done — {total} file(s) converted."
        label.config(text=msg)
        root.after(4000 if errors else 1500, root.destroy)

    root.after(50, work)
    root.mainloop()

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        sys.exit(1)

    pdfs, imgs = get_files(folder)

    if not pdfs and not imgs:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Convert All to JPG", "No convertible files found in this folder.")
        root.destroy()
        return

    run_gui(pdfs, imgs)

if __name__ == "__main__":
    main()
