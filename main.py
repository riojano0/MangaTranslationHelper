import os

from config import INPUT_DIR
from image.extraction import extract_image_and_clean
from text.extraction import create_translation_files

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output-format", help="Output format. Supported: xliff, text, json | Default xliff")
    parser.add_argument("-l", "--lang", help="Language from image. Supported: en, jpn | Default en")
    parser.add_argument("-pi", "--preserve_id", help="Preserve id: is the filename of the bubble image | Default True")
    parser.add_argument("-f", "--force",
                        help="Force to process each step of the image clean and text extraction | Default False")
    parser.add_argument("-i", "--input",
                        help="filename from image locate on _input, this work to allow to "
                             "process only one image instead of all inside the folder")

    output_format = "xliff"
    lang = "en"
    preserve_id = True
    file = None

    args = parser.parse_args()
    args_output_format = args.output_format
    if args_output_format is None or args_output_format in ["xliff", "text", "json"]:
        output_format = args_output_format
    elif len(args_output_format) > 0 and args_output_format not in ["xliff", "text", "json"]:
        parser.error('Invalid output format option. Use -h')

    args_lang = args.lang
    if args_lang is None or args_lang in ["en", "jpn"]:
        lang = args_lang
    elif len(args_lang) > 0 and lang not in ["en", "jpn"]:
        parser.error('Invalid language option. Use -h')

    args_input = args.input
    if args_input is not None and len(args_input):
        file_path = os.path.join(INPUT_DIR, args_input)
        if os.path.exists(file_path):
            file = args_input
        else:
            parser.error("File not found on _input folder")

    force = args.force is not None and args.force.lower() == "true"

    extract_image_and_clean(file=file, force=force)
    create_translation_files(output_format=output_format, lang=lang, preserve_id=preserve_id, file=file, force=force)
