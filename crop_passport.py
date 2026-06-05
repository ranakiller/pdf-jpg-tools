import sys, os, glob
import cv2
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox


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

    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            return approx

    # Relax approximation and try again
    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.05 * peri, True)
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
        # Fallback: trim a small border and use full image
        m = int(min(w, h) * 0.02)
        warped = img[m:h - m, m:w - m]

    # Ensure landscape orientation (passport data page is always wider than tall)
    ch, cw = warped.shape[:2]
    if ch > cw:
        warped = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)

    out = os.path.splitext(path)[0] + "_cropped.jpg"
    Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)).save(out, quality=95)


def collect_images(target):
    if os.path.isfile(target):
        return [os.path.abspath(target)]
    files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp",
                "*.JPG", "*.JPEG", "*.PNG", "*.BMP"]:
        files.extend(glob.glob(os.path.join(target, "**", ext), recursive=True))
    return [f for f in files if "_cropped" not in os.path.basename(f)]


def run_gui(files):
    root = tk.Tk()
    root.title("Crop Passports")
    root.geometry("420x110")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    label = tk.Label(root, text="Starting...", font=("Segoe UI", 10), anchor="w")
    label.pack(fill="x", padx=20, pady=(15, 4))

    bar = ttk.Progressbar(root, length=380, mode="determinate", maximum=len(files))
    bar.pack(padx=20)

    errors = []

    def work():
        for i, path in enumerate(files):
            label.config(text=f"({i+1}/{len(files)})  {os.path.basename(path)}")
            root.update()
            try:
                crop_passport(path)
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")
            bar["value"] = i + 1
            root.update()

        msg = f"Done with {len(errors)} error(s)." if errors else f"Done — {len(files)} file(s) cropped."
        label.config(text=msg)
        root.after(4000 if errors else 1500, root.destroy)

    root.after(50, work)
    root.mainloop()


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    files = collect_images(sys.argv[1])

    if not files:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Crop Passports", "No image files found.")
        root.destroy()
        return

    run_gui(files)


if __name__ == "__main__":
    main()
