import os
import cv2
import json
import re
import numpy as np
import xml.etree.ElementTree as ET

import util
from config import PATH_TO_TESSERACT, OUTPUT_DIR, BUBBLE_SUFFIX_FOLDER
from PIL import Image
from pytesseract import pytesseract
from xml.dom import minidom

from manga_ocr import MangaOcr

from util import get_filename_and_ext, allowed_file, Singleton


class MangaOcrInstance(metaclass=Singleton):

    def __init__(self):
        self.m_ocr = MangaOcr()

    def get_ocr(self):
        return self.m_ocr


def _image_to_text(image_path, lang="en"):
    """ Image to Text

    :param image_path: Image location
    :param lang: language on image [en|jpn]
    :return: Text from image
    """
    text = ''
    if lang is None or lang == "en":
        image_buffer = Image.open(image_path)
        pytesseract.tesseract_cmd = PATH_TO_TESSERACT
        text = pytesseract.image_to_string(image_buffer, lang='eng', config='--psm 3')
    elif lang == "jpn":
        m_ocr = MangaOcrInstance().get_ocr()
        text = m_ocr(image_path)

    file_name = get_filename_and_ext(image_path)["filename"]

    image_data = {"id": file_name}
    if text is not None and len(text) > 0:
        replace = text.replace("\n", " ")
        image_data["text"] = " ".join(replace.split())

    print("Processed file " + file_name)
    return image_data


def _remove_noise(image_path, force_clean=False):
    if re.match('.+__clean\\.', image_path):
        return image_path

    file_data = get_filename_and_ext(image_path)
    file_parts = os.path.splitext(image_path)
    image_path_clean = file_parts[0] + "__clean" + file_data["ext"]

    if not os.path.exists(image_path_clean) or force_clean:
        np_img_buff = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(np_img_buff, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (0, 0), fx=1.75, fy=1.75)
        clean = cv2.fastNlMeansDenoising(img, None, 30, 7, 40)
        retval, buffer_img = cv2.imencode(file_data["ext"], clean)

        with open(image_path_clean, "wb") as image_download:
            image_download.write(buffer_img)

    return image_path_clean


def _folder_image_to_text_file(image_path_folder, output_format="text", preserve_id=True, lang="en", force=False):
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
    image_text_data_obj = {"texts": image_to_text_data}
    for image_path in files:
        clean_image_path = _remove_noise(image_path, force_clean=force)
        image_text_data = _image_to_text(clean_image_path, lang=lang)
        image_to_text_data.append(image_text_data)

    if output_format == "text":
        with open(output_file_name, "w", encoding="UTF-8") as data_file:
            for image_data in image_to_text_data:
                if preserve_id:
                    id_prefix = image_data["id"] + "__ "
                    data_file.write(id_prefix + image_data["texts"] + "\n")
                else:
                    data_file.write(image_data["texts"] + "\n")
    elif output_format == "json":
        with open(output_file_name, "w") as data_file:
            if preserve_id:
                json.dump(image_text_data_obj, data_file)
            else:
                obj_without_id = {"texts": [x["text"] for x in image_text_data_obj["texts"]]}
                json.dump(obj_without_id, data_file)
    elif output_format == "xliff":
        with open(output_file_name, "w", encoding='UTF-8') as data_file:
            xliff_str = _create_xliff_str(image_text_data_obj, lang=lang)
            data_file.write(xliff_str)

    print("Created " + output_file_name)


def _create_xliff_str(image_text_data_obj, lang="en", preverse_id=True):
    ET.register_namespace("xmlns", "urn:oasis:names:tc:xliff:document:1.2")
    root = ET.Element("xliff", {
        "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
        "version": "1.2"
    })

    if lang == "en":
        _create_xliff_file_section(root, "en-US", "es", image_text_data_obj, preverse_id)
    else:
        # Default for spanish
        _create_xliff_file_section(root, lang, "es", image_text_data_obj, preverse_id)
        # Default for English
        _create_xliff_file_section(root, lang, "en-US", image_text_data_obj, preverse_id)

    return minidom.parseString(
        ET.tostring(root, encoding='UTF-8', method='xml', short_empty_elements=False)) \
        .toprettyxml(indent="   ", )


def _create_xliff_file_section(root, source_lang, target_lang, image_text_data_obj, preverse_id):
    file = ET.Element("file")
    file.set("original", "global_" + source_lang + "-" + target_lang)
    source_language = source_lang
    file.set("source-language", source_lang)
    file.set("target-language", target_lang)
    root.append(file)
    _create_xliff_file_body(file, source_language, image_text_data_obj, preverse_id)


def _create_xliff_file_body(file, source_language, image_text_data_obj, preverse_id):
    body = ET.Element("body")
    file.append(body)
    for image_text_data in image_text_data_obj["texts"]:
        attrs = {}
        if preverse_id:
            attrs = {"id": image_text_data["id"]}

        trans_unit = ET.Element("trans-unit", attrs)
        source = ET.Element("source", {"xml:xlang": source_language})
        source.text = image_text_data["text"]
        trans_unit.append(source)
        body.append(trans_unit)


def create_translation_files(output_format="text", lang="en", preserve_id=True, file=None, force=False):
    if file is None:
        text_folders = [x[0] for x in os.walk(OUTPUT_DIR) if re.match(".+" + BUBBLE_SUFFIX_FOLDER, x[0])]
    else:
        file_name_without_extension = util.get_filename_and_ext(file)["filename"]
        text_folders = [x[0] for x in os.walk(OUTPUT_DIR)
                        if re.match(".+" + file_name_without_extension + BUBBLE_SUFFIX_FOLDER, x[0])]

    for text_folder in text_folders:
        _folder_image_to_text_file(image_path_folder=text_folder, output_format=output_format,
                                   preserve_id=preserve_id, lang=lang, force=force)
