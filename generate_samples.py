"""
generate_samples.py — Creates synthetic placeholder medical images for demo.
Run once: python generate_samples.py
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

Path("samples").mkdir(exist_ok=True)
random.seed(42)


def noise_layer(draw, width, height, intensity=30, count=2000):
    for _ in range(count):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        v = random.randint(0, intensity)
        draw.point((x, y), fill=v)


def chest_xray(filename, anomaly="none"):
    w, h = 512, 512
    img = Image.new("L", (w, h), color=10)
    draw = ImageDraw.Draw(img)

    # Ribs
    for i in range(6):
        y = 100 + i * 50
        draw.arc([60, y, 450, y + 80], start=0, end=180, fill=80, width=4)

    # Lung fields
    draw.ellipse([70, 80, 230, 420], fill=40)
    draw.ellipse([280, 80, 440, 420], fill=40)

    # Mediastinum / heart shadow
    draw.ellipse([200, 200, 320, 380], fill=120)

    if anomaly == "suspicious":
        draw.ellipse([80, 300, 220, 420], fill=130)   # opacity lower-left
        draw.ellipse([85, 305, 215, 415], fill=150)
    elif anomaly == "critical":
        draw.ellipse([300, 80, 440, 250], fill=160)   # large white-out
        draw.ellipse([310, 90, 430, 240], fill=180)
        draw.line([256, 80, 300, 420], fill=100, width=3)  # tracheal shift

    noise_layer(draw, w, h, intensity=20)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img.save(filename, "JPEG", quality=85)
    print(f"  Created: {filename}")


def brain_scan(filename, anomaly="none"):
    w, h = 512, 512
    img = Image.new("L", (w, h), color=5)
    draw = ImageDraw.Draw(img)

    # Skull
    draw.ellipse([40, 40, 470, 470], outline=200, width=8)
    # Brain tissue
    draw.ellipse([60, 60, 450, 450], fill=60)
    # Ventricles
    draw.ellipse([215, 200, 260, 300], fill=20)
    draw.ellipse([250, 200, 295, 300], fill=20)
    # Midline
    draw.line([256, 60, 256, 450], fill=50, width=2)
    # Gyri suggestion
    for angle in range(0, 360, 30):
        import math
        cx, cy = 256, 256
        r1, r2 = 130, 155
        a = math.radians(angle)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
        draw.line([x1, y1, x2, y2], fill=75, width=2)

    if anomaly == "suspicious":
        draw.ellipse([150, 140, 270, 250], fill=160)   # bright mass
        draw.ellipse([160, 150, 260, 240], fill=180)
    elif anomaly == "critical":
        draw.ellipse([120, 120, 300, 290], fill=190)   # large hemorrhage
        draw.line([256, 60, 280, 450], fill=50, width=2)  # midline shift

    noise_layer(draw, w, h, intensity=15)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img.save(filename, "JPEG", quality=85)
    print(f"  Created: {filename}")


def body_ct(filename, anomaly="none"):
    w, h = 512, 512
    img = Image.new("L", (w, h), color=5)
    draw = ImageDraw.Draw(img)

    # Body outline
    draw.ellipse([80, 60, 430, 450], fill=40)
    # Spine
    draw.ellipse([228, 80, 282, 440], fill=200)
    # Liver
    draw.ellipse([200, 150, 390, 280], fill=80)
    # Spleen
    draw.ellipse([120, 150, 210, 240], fill=75)
    # Kidneys
    draw.ellipse([160, 260, 220, 340], fill=85)
    draw.ellipse([290, 260, 350, 340], fill=85)

    if anomaly == "trauma":
        # Splenic laceration + free fluid
        draw.ellipse([90, 130, 230, 260], fill=30)   # dark free fluid
        draw.line([130, 180, 200, 240], fill=20, width=4)  # laceration
        draw.ellipse([100, 300, 240, 420], fill=25)   # pelvic pooling

    noise_layer(draw, w, h, intensity=18)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img.save(filename, "JPEG", quality=85)
    print(f"  Created: {filename}")


if __name__ == "__main__":
    print("NeuroForensic AI — Generating synthetic demo samples\n")
    chest_xray("samples/chest_normal.jpg",     anomaly="none")
    chest_xray("samples/chest_suspicious.jpg", anomaly="suspicious")
    chest_xray("samples/chest_critical.jpg",   anomaly="critical")
    brain_scan("samples/brain_normal.jpg",     anomaly="none")
    brain_scan("samples/brain_suspicious.jpg", anomaly="suspicious")
    body_ct("samples/body_normal.jpg",         anomaly="none")
    body_ct("samples/body_trauma.jpg",         anomaly="trauma")
    print("\nAll samples ready. Run: streamlit run app.py")
