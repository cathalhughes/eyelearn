from app import *
import unittest
import os
from flask_testing import TestCase
import numpy
import base64
import json
from audio_processing import *
import io


class BaseTestCase(TestCase):
    """A base test case."""

    def create_app(self):
        app.config.from_object('config.TestConfig')
        return app

    def setUp(self):
        pass

    def tearDown(self):
        pass

class FlaskTestCase(BaseTestCase):

    def test_predictWord(self):
        audio = open("static/testing/jackhammer.wav", "rb")
        response = self.client.post(
            '/predictWord',
            data={'audio_data': audio},
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)

    def test_predictWord2(self):
        #lang = io.StringIO("fr")
        #recg = io.StringIO("en-EN")
        audio = open("static/testing/jackhammer.wav", "rb")
        response = self.client.post(
            '/predictWord',
            content_type='multipart/form-data',
            data={'audio_data': audio, 'lang': b"fr", 'recognition_language': b"en-EN"},
            #content_type='multipart/form-data',
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
