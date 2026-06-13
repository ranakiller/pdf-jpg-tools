import sys, os, time, tempfile, uuid, glob
import fitz
from PIL import Image, ImageOps
import tkinter as tk
from tkinter import ttk

QUEUE_DIR = os.path.join(tempfile.gettempdir(), "cc_merge2pdf")
LOCK_FILE  = os.path.join(tempfile.gettempdir(), "cc_merge2pdf.lock")

def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"

def enqueue(path):
    os.makedirs(QUEUE_DIR, exist_ok=True)
    job = os.path.join(QUEUE_DIR, f"{uuid.uuid4().hex}.job")
    with open(job, "w") as f:
        f.write(path)

def try_become_master():
    try:
        if time.time() - os.path.getmtime(LOCK_FILE) > 60:
            os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False

def collect_jobs():
    files = []
    for jf in glob.glob(os.path.join(QUEUE_DIR, "*.job")):
        try:
            with open(jf) as f:
                p = f.read().strip()
            os.remove(jf)
            if p:
                files.append(p)
        except Exception:
            pass
    return sorted(files)

def load_as_pages(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        pages = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(img)
        doc.close()
        return pages
    else:
        return [ImageOps.exif_transpose(Image.open(path)).convert("RGB")]

def run_gui(files):
    total = len(files)
    root = tk.Tk()
    root.title("Merge to PDF")
    root.geometry("420x110")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    label = tk.Label(root, text="Starting...", font=("Segoe UI", 10), anchor="w")
    label.pack(fill="x", padx=20, pady=(15, 4))

    bar = ttk.Progressbar(root, length=380, mode="determinate", maximum=total)
    bar.pack(padx=20)

    errors = []

    def work():
        all_pages = []
        for i, path in enumerate(files):
            label.config(text=f"({i+1}/{total})  {os.path.basename(path)}")
            root.update()
            try:
                all_pages.extend(load_as_pages(path))
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")
            bar["value"] = i + 1
            root.update()

        if all_pages:
            label.config(text="Saving PDF...")
            root.update()
            base_name = os.path.splitext(os.path.basename(files[0]))[0]
            out = unique_path(os.path.join(os.path.dirname(files[0]), base_name + "_merged.pdf"))
            try:
                all_pages[0].save(out, save_all=True, append_images=all_pages[1:])
                msg = f"Done with {len(errors)} error(s)." if errors else f"Saved → {os.path.basename(out)}"
            except Exception as e:
                msg = f"Failed to save: {e}"
            label.config(text=msg)
        else:
            label.config(text="No pages could be loaded.")

        root.after(4000 if errors else 2000, root.destroy)

    root.after(50, work)
    root.mainloop()

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    enqueue(os.path.abspath(sys.argv[1]))

    if not try_become_master():
        return

    time.sleep(0.8)

    files = collect_jobs()
    if not files:
        files = [os.path.abspath(sys.argv[1])]

    try:
        run_gui(files)
    finally:
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass

if __name__ == "__main__":
    main()
