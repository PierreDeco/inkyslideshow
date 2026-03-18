import os
import time
import random
import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ExifTags
from inky.auto import auto
from gpiozero import Button
from signal import pause
import numpy as np

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


LOG_DIR = Path.home() / ".inky_slideshow"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "debug.log"),
        logging.StreamHandler(),
    ],
)
logging.info("Starting inkyslideshow...")


inky_display = auto()
inky_display.set_border(inky_display.WHITE)

SCREEN_WIDTH = inky_display.width
SCREEN_HEIGHT = inky_display.height

PHOTOS_FOLDER = Path.home() / "inky" / "inky" / "inkyslideshow" / "Photos"
DELAY_SECONDS = 60

BUTTON_A = Button(5)

ORIENTATION_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "Orientation"),
    None,
)


def get_image_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        logging.error(f"Photos folder not found: {folder}")
        return []
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp"}
    return [p for p in folder.iterdir() if p.suffix.lower() in valid_exts]


def auto_orient_image(image: Image.Image) -> Image.Image:
    try:
        exif = image._getexif()
        if not exif or ORIENTATION_TAG is None:
            return image

        orientation = exif.get(ORIENTATION_TAG)
        logging.debug(f"EXIF Orientation: {orientation}")

        transforms = {
            2: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),
            3: lambda img: img.rotate(180, expand=True),
            4: lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),
            5: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT).rotate(
                270, expand=True
            ),
            6: lambda img: img.rotate(270, expand=True),
            7: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True),
            8: lambda img: img.rotate(90, expand=True),
        }

        transform = transforms.get(orientation)
        if transform:
            image = transform(image)
            logging.debug(f"Applied EXIF rotation (orientation {orientation})")

    except Exception as e:
        logging.debug(f"EXIF error (image unchanged): {e}")

    return image


def seems_upright(image: Image.Image) -> bool:
    left_var = image.crop((0, 0, 10, image.height)).convert("L").var()
    right_var = (
        image.crop((image.width - 10, 0, image.width, image.height)).convert("L").var()
    )
    top_var = image.crop((0, 0, image.width, 10)).convert("L").var()
    bottom_var = (
        image.crop((0, image.height - 10, image.width, image.height)).convert("L").var()
    )

    if (left_var + right_var) > (top_var + bottom_var):
        return True

    if HAS_CV2:
        try:
            gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            faces = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            ).detectMultiScale(gray, 1.1, 4)
            for _, _, h, w in faces:
                if h > w:
                    return True
        except Exception:
            pass

    return False


def prepare_image(image_path: Path) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    image = auto_orient_image(image)

    if image.height > image.width and not seems_upright(image):
        logging.debug(
            f"Portrait image without valid EXIF — rotating 90° CCW: {image_path.name}"
        )
        image = image.rotate(90, expand=True)

    image.thumbnail((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
    background = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), (255, 255, 255))
    x = (SCREEN_WIDTH - image.width) // 2
    y = (SCREEN_HEIGHT - image.height) // 2
    background.paste(image, (x, y))
    return background


def display_image(image_path: Path) -> None:
    logging.info(f"Displaying: {image_path.name}")
    final_image = prepare_image(image_path)
    inky_display.set_image(final_image)
    inky_display.show()


def wait_with_skip(timeout: int) -> None:
    for _ in range(timeout * 10):
        if BUTTON_A.is_pressed:
            logging.info("Button A pressed — next image.")
            return
        time.sleep(0.1)


def slideshow() -> None:
    if not PHOTOS_FOLDER.is_dir():
        logging.error(f"Photos folder does not exist: {PHOTOS_FOLDER}")
        return

    previous_image: Optional[Path] = None

    while True:
        image_files = get_image_files(PHOTOS_FOLDER)
        if not image_files:
            logging.warning("No images found.")
            time.sleep(DELAY_SECONDS)
            continue

        if len(image_files) > 1:
            for _ in range(10):
                random.shuffle(image_files)
                if image_files[0] != previous_image:
                    break
        elif len(image_files) == 1:
            logging.info("Only one image available.")

        for image_path in image_files:
            if image_path == previous_image:
                continue

            display_image(image_path)
            previous_image = image_path
            wait_with_skip(DELAY_SECONDS)


if __name__ == "__main__":
    try:
        slideshow()
    except KeyboardInterrupt:
        logging.info("Shutdown requested.")
