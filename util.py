import os

from config import ALLOWED_EXTENSIONS, PATH_TO_TESSERACT


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_filename_and_ext(file_path):
    filename, file_extension = os.path.splitext(file_path)
    filename = os.path.basename(filename)

    return {
        "filename": filename,
        "ext": file_extension
    }


def tesseract_available():
    return os.path.exists(PATH_TO_TESSERACT)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
