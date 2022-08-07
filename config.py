import os
from rimuto import detect

# General
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "_input")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'jpg', 'png'}
BUBBLE_SUFFIX_FOLDER = "_bubbles"

# Tesseract
TESSERACT_HOME = os.getenv('TESSERACT_HOME')
if len(TESSERACT_HOME) > 0:
    PATH_TO_TESSERACT = os.path.join(TESSERACT_HOME, 'tesseract.exe')
else:
    PATH_TO_TESSERACT = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# YOLOv4
LABELS_PATH = os.path.join(SCRIPT_DIR, "resources", "YOLOv4", "obj.names")
YOLOv4_CFG = os.path.join(SCRIPT_DIR, "resources", "YOLOv4", "yolov4-obj.cfg")
WEIGHTS = os.path.join(SCRIPT_DIR, "resources", "YOLOv4", "yolov4-obj_final.weights")

NET_FROM_DARKNET = detect.load_model(YOLOv4_CFG, WEIGHTS)
