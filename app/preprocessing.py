# app/preprocessing.py

import cv2
import numpy as np
from PIL import Image
from app.logger import get_logger

log = get_logger(__name__)


def preprocess(pil_image):
    img = np.array(pil_image)

    if len(img.shape) == 3 and img.shape[2] == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        log.debug("Colorspace: RGBA → GRAY")
    elif len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        log.debug("Colorspace: RGB → GRAY")
    else:
        gray = img
        log.debug("Image already grayscale")

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 2,
    )

    return Image.fromarray(thresh)