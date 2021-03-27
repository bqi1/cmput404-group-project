'''

Note: this test assumes that a picture exists

'''

import unittest
import requests
import json
import sqlite3
import os
FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class LikeTests(unittest.TestCase):

    # Initialize some variables
    def setUp(self):
        self.image_url = "http://localhost:8000/media/images/%s"
    def test_GET_image(self):
        """
        Assume an image already exists, called 'what.jfif'
        """
        r = requests.get(self.image_url % "what.jfif")
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
if __name__ == "__main__":
    # Run tests
    unittest.main()

