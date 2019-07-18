from mock import Mock
from models import loadModels
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf

# class MockEmnistModel(object):
#     def predict(image):
#         return [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.9]]
#
# class MockMnistModel(object):
#     def predict(image):
#         return [[0,0,0,0,0,0,0,0,0,1]]
#
#
#
# loadModels.initMNISTModel = Mock(return_value= (MockEmnistModel, tf.Graph()))
# loadModels.initEMNISTModel = Mock(return_value= (MockMnistModel, tf.Graph()))
from app import *
import unittest
from unittest import mock


from flask_testing import TestCase
import numpy
import base64
import json
import base64








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

    #@mock.patch('app.emnistGraph.as_default')
    #@mock.patch('app.emnistModel.predict')
    def test_predictCharacter(self):
        #mock_graph.return_value = True
        print("here")
        #mock_model.return_value = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.9]
        with open("static/testing/emnist.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        #print(image)
        response = self.client.post(
            '/predictCharacter',
            data=encoded_string,
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        #self.assertTrue(b'football' in response.data)

    def test_predictNumber(self):
        with open("static/testing/emnist.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        response = self.client.post(
            '/predictNumber',
            data=encoded_string,
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        #self.assertTrue(b'football' in response.data)

    # def test_processImage(self):
    #     image = processImage("static/testing/output.png", (299,299))
    #     self.assertEqual(type(image), numpy.ndarray)


if __name__ == '__main__':
    unittest.main()
