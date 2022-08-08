import os
import unittest

import util
from config import SCRIPT_DIR
from text import extraction


class TextExtractionTest(unittest.TestCase):
    def setUp(self):
        self.data_folder = os.path.join(SCRIPT_DIR, "test", "text_extraction_data")

    def validate_text(self, image_name, lang, text):
        image = os.path.join(self.data_folder, image_name)
        clean_image = extraction._remove_noise(image, force_clean=True)
        image_data = extraction._image_to_text(clean_image, lang=lang)

        self.assertEqual(image_data["id"], util.get_filename_and_ext(image)["filename"] + "__clean")
        self.assertEqual(image_data["text"], text)

    @unittest.skipIf(not util.tesseract_available(), "Tesseract not available")
    def test_english(self):
        self.validate_text("en_001.png", "en",
                           "AT 7 YEARS OLD, DURING MY BAPTISM CEREMONY, I FOUND THE GODS’ PARADISE. ..")
        self.validate_text("en_002.png", "en",
                           "WHILE MY DESIRE TO READ BOOKS WAS GOING NOWHERE, A LOT OF THINGS HAPPENED—...")
        self.validate_text("en_003.png", "en",
                           "*AHEM*, I MEAN THE LIBRARY IN THE TEMPLE.")

    def test_japanese_vertical(self):
        self.validate_text("jpn_001.png", "jpn", "冬の手伝いだけど．．．")
        self.validate_text("jpn_002.png", "jpn", "．．．まぁそんな気はしていたよ")
        self.validate_text("jpn_003.png", "jpn", "父さんと相談したんですけど")


def suite():
    """ Test Suite """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TextExtractionTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
