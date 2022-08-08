import os
import cv2
import numpy as np
import rimuto.clean
import rimuto.detect

from config import INPUT_DIR, OUTPUT_DIR, NET_FROM_DARKNET, BUBBLE_SUFFIX_FOLDER
from util import get_filename_and_ext, allowed_file


def _image_extraction_data(file_input=None, force=False):
    data = {}
    files = []
    walks = os.walk(INPUT_DIR)

    for (path, sub_dirs, walkFile) in walks:
        for name in walkFile:
            if file_input is not None and len(file_input):
                if name == file_input:
                    files.append(os.path.join(path, name))
            else:
                files.append(os.path.join(path, name))

    for i, file in enumerate(files):
        file_info = get_filename_and_ext(file)

        pre = os.path.split(file)[0]
        sub_folder = ""
        if not pre.endswith("input"):
            sub_folder = os.path.split(os.path.split(file)[0])[1]

        image_name = file_info["filename"] + file_info["ext"]

        already_processed = os.path.join(OUTPUT_DIR, sub_folder, image_name)
        if os.path.exists(already_processed) and not force:
            continue

        if file and allowed_file(file):
            np_img_buff = np.fromfile(file, np.uint8)
            img = cv2.imdecode(np_img_buff, cv2.IMREAD_COLOR)
            res, bboxes = rimuto.detect.detect(NET_FROM_DARKNET, img.copy())
            cleaned_bubbles = []
            # Sort not comprehensive only to bring a little help
            bboxes_sorted = sorted(bboxes, key=lambda array: [array[1], -array[0]])
            margin_extra = 2
            for j in bboxes_sorted:
                x = j[0]
                y = j[1]
                w = j[2] + margin_extra  # Reduce Bubble Size, can cause problem user carefully
                h = j[3] + margin_extra  # Reduce Bubble Size, can cause problem user carefully
                cropped = img[y:y + h, x:x + w]
                ret, buffer = cv2.imencode(file_info["ext"], cropped)
                cleaned_bubbles.append([x, y, buffer])
                cleaned = rimuto.clean.remove(cropped)
                img[y: y + h, x: x + w] = cleaned

            retval, buffer_img = cv2.imencode(file_info["ext"], img)

            data[i] = {
                "pack": {
                    "cleaned_bubbles": cleaned_bubbles,
                    "img": buffer_img,
                    "ext": file_info["ext"],
                    "filename": file_info["filename"],
                    "image_name": image_name,
                    "sub_folder": sub_folder
                }
            }

    return data


def _serialize_image_data(data):
    for key, img_clean_data in data.items():
        image_folder = _serialize_image_page(img_clean_data)
        _serialize_image_bubbles(image_folder, img_clean_data)


def _serialize_image_bubbles(image_folder, img_clean_data):
    image_bubbles = img_clean_data["pack"]["cleaned_bubbles"]
    image_bubbles_dir = os.path.join(image_folder, img_clean_data["pack"]["filename"] + BUBBLE_SUFFIX_FOLDER)
    os.makedirs(image_bubbles_dir, exist_ok=True)
    bubble_x_position = 0
    bubble_y_position = 1
    buffer_position = 2
    for i, bubble in enumerate(image_bubbles):
        x = str(bubble[bubble_x_position])
        y = str(bubble[bubble_y_position])
        position_name = x + "x" + y
        image_bubble_output_name = os.path.join(image_bubbles_dir, str(i) + "_" + position_name + ".png")
        with open(image_bubble_output_name, "wb") as image_download:
            image_download.write(bubble[buffer_position])


def _serialize_image_page(img_clean):
    image_data = img_clean["pack"]["img"]
    image_name = img_clean["pack"]["image_name"]
    image_folder = os.path.join(OUTPUT_DIR, img_clean["pack"]["sub_folder"])
    os.makedirs(image_folder, exist_ok=True)
    with open(os.path.join(image_folder, image_name), "wb") as image_download:
        image_download.write(image_data)

    return image_folder


def extract_image_and_clean(file=None, force=False):
    data = _image_extraction_data(file_input=file, force=force)
    _serialize_image_data(data)
    print("Complete extract_image_and_clean")
