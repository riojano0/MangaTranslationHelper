import os

from config import ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_filename_and_ext(file_path):
    filename, file_extension = os.path.splitext(file_path)
    filename = os.path.basename(filename)

    return {
        "filename": filename,
        "ext": file_extension
    }