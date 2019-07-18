import unittest
import os
from flask_testing import TestCase
import numpy


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

    def test_getAveragePrediction(self):
        data = {"dataArray": [[5,6,7,78]]}
        #data = jsonify(data)
        response = self.client.post(
            '/getAveragePrediction',
            json=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'predictions' in response.data)

    def test_getDataGeneratorForData(self):
        array = getDataGeneratorForData([5,6,7,78])
        self.assertTrue(len(array) > 0)

    def test_createModel(self):
        model = createModel()
        self.assertTrue(model != None)

    def test_trainModel(self):
        model = createModel()
        data = [60, 65, 55, 60, 70, 75, 72, 67, 73, 76, 70, 59, 63, 54, 66, 70, 80, 71, 63, 65, 79, 84, 80, 81, 82, 75,
                69, 60, 70, 77, 79, 84]
        generator = getDataGeneratorForData(data)
        model = trainModel(model, generator)
        data = data[-3:]
        x_input = array(data).reshape((1, 3, 1))
        yhat = model.predict(x_input, verbose=0)
        self.assertEqual(type(yhat), numpy.ndarray)

    def test_getPrediction(self):
        model = createModel()
        data = [60, 65, 55, 60, 70, 75, 72, 67, 73, 76, 70, 59, 63, 54, 66, 70, 80, 71, 63, 65, 79, 84, 80, 81, 82, 75,
                69, 60, 70, 77, 79, 84]
        generator = getDataGeneratorForData(data)
        model = trainModel(model, generator)
        data = data[-3:]

        prediction = getPrediction(model, data)
        self.assertEqual(type(prediction), int)



if __name__ == '__main__':
    unittest.main()
