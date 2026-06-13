import sys, os, glob
from PIL import Image, ImageOps
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

def get_images(folder):
    imgs = []
    for ext in ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG", "*.bmp", "*.BMP"]:
        imgs.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    return sorted(imgs)

def run_gui(folder, images):
    total = len(images)
    root = tk.Tk()
    root.title("Merge Images to PDF")
    root.geometry("420x110")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    label = tk.Label(root, text="Starting...", font=("Segoe UI", 10), anchor="w")
    label.pack(fill="x", padx=20, pady=(15, 4))

    bar = ttk.Progressbar(root, length=380, mode="determinate", maximum=total)
    bar.pack(padx=20)

    errors = []

    def work():
        pages = []
        for i, path in enumerate(images):
            label.config(text=f"({i+1}/{total})  {os.path.basename(path)}")
            root.update()
            try:
                img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
                pages.append(img)
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")
            bar["value"] = i + 1
            root.update()

        if pages:
            folder_name = os.path.basename(folder.rstrip("\\/")) or "merged"
            out = unique_path(os.path.join(folder, folder_name + ".pdf"))
            label.config(text="Saving PDF...")
            root.update()
            try:
                pages[0].save(out, save_all=True, append_images=pages[1:])
                msg = f"Done with {len(errors)} error(s)." if errors else f"Saved {total} image(s) → {os.path.basename(out)}"
            except Exception as e:
                msg = f"Failed to save PDF: {e}"
            label.config(text=msg)
        else:
            label.config(text="No images could be loaded.")

        root.after(4000 if errors else 2000, root.destroy)

    root.after(50, work)
    root.mainloop()

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        sys.exit(1)

    images = get_images(folder)

    if not images:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Merge Images to PDF", "No images found in this folder.")
        root.destroy()
        return

    run_gui(folder, images)

if __name__ == "__main__":
    main()
