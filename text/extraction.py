import os
import cv2
import json
import re
import numpy as np
import xml.etree.ElementTree as ET

from config import PATH_TO_TESSERACT, OUTPUT_DIR, BUBBLE_SUFFIX_FOLDER
from PIL import Image
from pytesseract import pytesseract
from xml.dom import minidom

from util import get_filename_and_ext, allowed_file


def _image_to_text(image_path):
    pytesseract.tesseract_cmd = PATH_TO_TESSERACT
    image_buffer = Image.open(image_path)
    text = pytesseract.image_to_string(image_buffer, lang='eng', config='--psm 3')

    file_name = get_filename_and_ext(image_path)["filename"]

    image_data = {"id": file_name}
    if text is not None:
        image_data["text"] = text.replace("\n", " ").strip()

    print("Processed file " + file_name)
    return image_data


def _remove_noise(image_path):
    if re.match('.+__clean\\.', image_path):
        return image_path

    file_data = get_filename_and_ext(image_path)
    file_parts = os.path.splitext(image_path)
    image_path_clean = file_parts[0] + "__clean" + file_data["ext"]

    if not os.path.exists(image_path_clean):
        np_img_buff = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(np_img_buff, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (0, 0), fx=1.75, fy=1.75)
        clean = cv2.fastNlMeansDenoising(img, None, 30, 7, 40)
        retval, buffer_img = cv2.imencode(file_data["ext"], clean)

        with open(image_path_clean, "wb") as image_download:
            image_download.write(buffer_img)

    return image_path_clean


def _folder_image_to_text_file(image_path_folder, output_format="text", preserve_id=True):
    walks = os.walk(image_path_folder)

    output_file_name = {
        "text": image_path_folder + "_data.txt",
        "json": image_path_folder + "_data.json",
        "xliff": image_path_folder + "_data.xliff",
    }[output_format]

    if os.path.exists(output_file_name):
        print("Translation file already exists " + output_file_name)
        return

    files = []
    for (path, sub_dirs, walkFile) in walks:
        for name in walkFile:
            if not re.match('.+__clean\\.', name) and allowed_file(name):
                files.append(os.path.join(path, name))

    image_to_text_data = []
    image_text_data_obj = {"data": image_to_text_data}
    for image_path in files:
        clean_image_path = _remove_noise(image_path)
        image_text_data = _image_to_text(clean_image_path)
        image_to_text_data.append(image_text_data)

    if output_format == "text":
        with open(output_file_name, "w", encoding="UTF-8") as data_file:
            for image_data in image_to_text_data:
                if preserve_id:
                    id_prefix = image_data["id"] + "__ "
                    data_file.write(id_prefix + image_data["text"] + "\n")
                else:
                    data_file.write(image_data["text"] + "\n")
    elif output_format == "json":
        with open(output_file_name, "w") as data_file:
            if preserve_id:
                json.dump(image_text_data_obj, data_file)
            else:
                obj_without_id = {"data": [x["text"] for x in image_text_data_obj["data"]]}
                json.dump(obj_without_id, data_file)
    elif output_format == "xliff":
        with open(output_file_name, "w", encoding='UTF-8') as data_file:
            xliff_str = _create_xliff_str(image_text_data_obj)
            data_file.write(xliff_str)

    print("Created " + output_file_name)


def _create_xliff_str(image_text_data_obj, preverse_id=True):
    ET.register_namespace("xmlns", "urn:oasis:names:tc:xliff:document:1.2")
    root = ET.Element("xliff", {
        "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
        "version": "1.2"
    })

    file = ET.Element("file")
    file.set("original", "global")
    file.set("source-language", "en-US")
    file.set("target-language", "es")
    body = ET.Element("body")
    file.append(body)
    root.append(file)

    for image_data in image_text_data_obj["data"]:
        attrs = {}
        if preverse_id:
            attrs = {"id": image_data["id"]}

        trans_unit = ET.Element("trans-unit", attrs)

        source = ET.Element("source", {"xml:xlang": "en-US"})
        source.text = image_data["text"]
        target = ET.Element("target", {"xml:xlang": "es"})
        target.text = " "
        trans_unit.append(source)
        trans_unit.append(target)
        body.append(trans_unit)

    return minidom.parseString(
        ET.tostring(root, encoding='UTF-8', method='xml', short_empty_elements=False)) \
        .toprettyxml(indent="   ", )


def create_translation_files(output_format="text", preserve_id=True):
    text_folders = [x[0] for x in os.walk(OUTPUT_DIR) if re.match(".+" + BUBBLE_SUFFIX_FOLDER, x[0])]

    for text_folder in text_folders:
        _folder_image_to_text_file(text_folder, output_format, preserve_id)
