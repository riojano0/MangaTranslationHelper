from image.extraction import extract_image_and_clean
from text.extraction import create_translation_files

if __name__ == '__main__':
    extract_image_and_clean()
    create_translation_files(output_format="xliff")
