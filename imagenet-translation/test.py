
import get_translation
import unittest
import os
from flask_testing import TestCase
import numpy
import base64
import json
from mock import Mock, patch



from app import *

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


    def test_translateObject(self):
        #mock_translation.return_value = ["bonjour"] * 5
        image = open("static/testing/object.png", "rb")
        response = self.client.post(
            '/translateObject',
            data={'image1': image,
                  'language': 'fr'},
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'predictions' in response.data)


    def test_processImage(self):
        image = processImage("static/testing/object.png", (299,299))
        self.assertEqual(type(image), numpy.ndarray)

    def test_get_translation_free(self):
        language = "fr"
        predictionFromImagenet = [('n03085013', 'computer_keyboard', 0.4248808), ('n03793489', 'mouse', 0.39666334), ('n02786058', 'Band_Aid', 0.076514915), ('n03642806', 'laptop', 0.007727216), ('n04372370', 'switch', 0.0063362774)]
        translatedPrediction = get_translation(predictionFromImagenet, language)
        self.assertNotEqual(translatedPrediction, "")
        self.assertEqual(type(translatedPrediction), list)



if __name__ == '__main__':
    unittest.main()
