import sys, os, glob
import fitz
from PIL import Image
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox


# ── Conversion ────────────────────────────────────────────────────────────────

def get_pdfs(folder):
    files = []
    for ext in ["*.pdf", "*.PDF"]:
        files.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    return files

def get_images(folder):
    files = []
    for ext in ["*.png", "*.PNG", "*.bmp", "*.BMP", "*.jpeg", "*.JPEG"]:
        files.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    return files

def get_jpgs(folder):
    files = []
    for ext in ["*.jpg", "*.JPG"]:
        files.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    return [f for f in files if "_cropped" not in os.path.basename(f)]

def convert_pdf(path):
    base = os.path.splitext(path)[0]
    doc = fitz.open(path)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        out = f"{base}.jpg" if len(doc) == 1 else f"{base}_page{i+1}.jpg"
        pix.save(out)
    doc.close()

def convert_image(path):
    out = os.path.splitext(path)[0] + ".jpg"
    Image.open(path).convert("RGB").save(out)


# ── Passport cropping ─────────────────────────────────────────────────────────

def order_points(pts):
    pts = pts.reshape(4, 2).astype("float32")
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def perspective_crop(img, pts):
    rect = order_points(pts)
    tl, tr, br, bl = rect
    w = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    h = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, M, (w, h))

def detect_passport_contour(img):
    h, w = img.shape[:2]
    min_area = w * h * 0.10
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    edged = cv2.Canny(blur, 20, 100)
    edged = cv2.dilate(edged, np.ones((5, 5), np.uint8), iterations=2)
    cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
    for epsilon in [0.02, 0.05]:
        for c in cnts:
            if cv2.contourArea(c) < min_area:
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon * peri, True)
            if len(approx) == 4:
                return approx
    return None

def crop_passport(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Cannot read image")
    h, w = img.shape[:2]
    contour = detect_passport_contour(img)
    if contour is not None:
        warped = perspective_crop(img, contour)
    else:
        m = int(min(w, h) * 0.02)
        warped = img[m:h - m, m:w - m]
    ch, cw = warped.shape[:2]
    if ch > cw:
        warped = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)
    out = os.path.splitext(path)[0] + "_cropped.jpg"
    Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)).save(out, quality=95)


# ── GUI ───────────────────────────────────────────────────────────────────────

def run_gui(folder):
    root = tk.Tk()
    root.title("Passport Master")
    root.geometry("440x130")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    phase_label = tk.Label(root, text="", font=("Segoe UI", 9, "bold"), anchor="w", fg="#555")
    phase_label.pack(fill="x", padx=20, pady=(12, 0))

    file_label = tk.Label(root, text="Scanning...", font=("Segoe UI", 10), anchor="w")
    file_label.pack(fill="x", padx=20)

    bar = ttk.Progressbar(root, length=400, mode="determinate")
    bar.pack(padx=20, pady=(4, 0))

    errors = []

    def set_phase(name, total):
        phase_label.config(text=name)
        bar["value"] = 0
        bar["maximum"] = max(total, 1)
        root.update()

    def step(label_text, fn, path, index, total):
        file_label.config(text=f"({index+1}/{total})  {os.path.basename(path)}")
        root.update()
        try:
            fn(path)
        except Exception as e:
            errors.append(f"{os.path.basename(path)}: {e}")
        bar["value"] = index + 1
        root.update()

    def work():
        # Phase 1: PDFs → JPG
        pdfs = get_pdfs(folder)
        set_phase(f"Phase 1/3 — Converting PDFs to JPG  ({len(pdfs)} files)", len(pdfs))
        for i, path in enumerate(pdfs):
            step("", convert_pdf, path, i, len(pdfs))

        # Phase 2: Images → JPG
        imgs = get_images(folder)
        set_phase(f"Phase 2/3 — Converting images to JPG  ({len(imgs)} files)", len(imgs))
        for i, path in enumerate(imgs):
            step("", convert_image, path, i, len(imgs))

        # Phase 3: Crop all JPGs (including freshly converted ones)
        jpgs = get_jpgs(folder)
        set_phase(f"Phase 3/3 — Cropping passport details  ({len(jpgs)} files)", len(jpgs))
        for i, path in enumerate(jpgs):
            step("", crop_passport, path, i, len(jpgs))

        msg = f"Done with {len(errors)} error(s)." if errors else "All done!"
        phase_label.config(text="")
        file_label.config(text=msg)
        root.after(4000 if errors else 1500, root.destroy)

    root.after(50, work)
    root.mainloop()


def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        sys.exit(1)

    # Quick check that there's anything to process
    if not get_pdfs(folder) and not get_images(folder) and not get_jpgs(folder):
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Passport Master", "No files found in this folder.")
        root.destroy()
        return

    run_gui(folder)


if __name__ == "__main__":
    main()
