# app/preprocessing.py

import cv2
import numpy as np
from PIL import Image


def preprocess(pil_image):
    img = np.array(pil_image)

    # ✅ Correct colorspace — PIL/pdf2image gives RGB, not BGR
    if len(img.shape) == 3 and img.shape[2] == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    elif len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img  # already grayscale

    # ✅ SPEED: Only apply denoising on low-quality images
    # For most scanned docs adaptive threshold alone is sufficient and faster
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )

    return Image.fromarray(thresh)