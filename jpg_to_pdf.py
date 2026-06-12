import sys, os, time, tempfile, uuid, glob
from PIL import Image
import tkinter as tk
from tkinter import ttk

QUEUE_DIR = os.path.join(tempfile.gettempdir(), "cc_jpg2pdf")
LOCK_FILE  = os.path.join(tempfile.gettempdir(), "cc_jpg2pdf.lock")

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
    return files

def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"

def convert_jpg(jpg_path):
    out = unique_path(os.path.splitext(jpg_path)[0] + ".pdf")
    img = Image.open(jpg_path).convert("RGB")
    img.save(out)

def run_gui(files):
    root = tk.Tk()
    root.title("JPG → PDF")
    root.geometry("400x110")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    label = tk.Label(root, text="Starting...", font=("Segoe UI", 10), anchor="w")
    label.pack(fill="x", padx=20, pady=(15, 4))

    bar = ttk.Progressbar(root, length=360, mode="determinate", maximum=len(files))
    bar.pack(padx=20)

    errors = []

    def work():
        for i, path in enumerate(files):
            label.config(text=f"({i+1}/{len(files)})  {os.path.basename(path)}")
            root.update()
            try:
                convert_jpg(path)
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")
            bar["value"] = i + 1
            root.update()

        if errors:
            label.config(text=f"Done with {len(errors)} error(s). Check filenames.")
            root.after(4000, root.destroy)
        else:
            label.config(text=f"Done — {len(files)} file(s) converted.")
            root.after(1500, root.destroy)

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
