from app import create_app, db
from app.models import User, Activity, Model, Class_Model, Doodles, Task, User_Task, Class_Doodles, Student_Doodles, Student_Class, Teacher_Class, Class_Prediction, Student_Predicted_Average, Class_Predicted_Average, Find_Me_Configurations, Student_Class_Level, Activity_Results, Student_Activity, Class, Predicted_Class_Average, Predicted_Average, Student_Vocab, Class_Configs
import unittest
from unittest import mock
from flask_testing import TestCase
from requests.models import Response
from flask_login import current_user
import datetime
from app.main.routes import getVoice
from app.image_classification.routes import getEndpoint, getDictForGame
from app.speech_recognition.routes import getRecognitionLangauge
from app.doodle.routes import findWordForDoodle, getWordForDoodle
from app.everyday_object_classification.routes import findWord, getWord
from app.user_analytics.routes import hasAccessToClass, hasAccess, getLevelCSS
from app.user_management.routes import get_translation
from app.doodle.routes import convertDoodleImage
from app.everyday_object_classification.routes import findWord, getWord, getCustomWord, createTextFiles, findCustomWord
from app.create_classifier.routes import getCustomGameWord, findCustomGameWord
import base64
import json

app = create_app('app.config.TestConfig')

class BaseTestCase(TestCase):
    """A base test case."""

    def create_app(self):
        # app = create_app('config.TestConfig')
        app.config.from_object("app.config.TestConfig")
        return app

    def setUp(self):
        app.config['LOGIN_DISABLED'] = True
        app.login_manager.init_app(app)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['SECRET_KEY'] = "you-will-never-guess"
        db.drop_all()
        db.create_all()

    def tearDown(self):
        pass

def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def create_user(username, email, password, role="Student", current_class="test"):
    user = User(username=username, email=email, role=role, current_class=current_class)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user.user_id

class FlaskTestCase(BaseTestCase):



    def test_login_logout(self):
        """Make sure login and logout works."""

        rv = login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
        self.assertTrue(b'Play' in rv.data)

        rv = logout(self.client)
        self.assertTrue(b'Sign In' in rv.data)

        rv = login(self.client, app.config['USERNAME'] + 'x', app.config['PASSWORD'])
        self.assertTrue(b'Invalid username or password' in rv.data)

        rv = login(self.client, app.config['USERNAME'], app.config['PASSWORD'] + 'x')
        self.assertTrue(b'Invalid username or password' in rv.data)

    # Ensure that flask was set up correctly
    def test_index(self):
        # app.config['LOGIN_DISABLED'] = True
        # app.login_manager.init_app(app)

        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class=None)
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            print(current_user.username)
            response = self.client.get('/', content_type='html/text', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_register(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            response = self.client.get('/register', content_type='html/text', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'As a Teacher' in response.data)

    def test_user(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/user/' + current_user.username, content_type='html/text', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'Change Current Active Class or Practice Area' in response.data)

    def test_user2(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], "Teacher")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/user/' + current_user.username, content_type='html/text', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'Change Current Active Practice Area' in response.data)

    def test_edit_profile(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], "Teacher")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/edit_profile', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'About me' in response.data)

    def test_createPracticeArea(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], "Teacher")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/createpracticearea', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'Create a Practice Area' in response.data)

    def test_createClass(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], "Teacher")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/createclass', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'Create a Class' in response.data)

    def test_joinClass(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/joinclass', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'Enter Class Code' in response.data)

    def test_changeClass(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/changeclass', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'EyeLearn' in response.data)

    def test_updateCurrentClass(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/updateCurrentClass/testclass1', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'User: student' in response.data)

    def test_classStats(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        current_time = datetime.datetime.utcnow()
        tomorrow = current_time + datetime.timedelta(days=1)
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "testclass1")
        u.current_class = "testclass1"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id,
                                            student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        predicted_class_average = Predicted_Class_Average(prediction=75, time_frame="Daily", date=tomorrow)
        db.session.add(predicted_class_average)
        db.session.commit()
        class_prediction = Class_Prediction(class_id="testclass1", average_id=predicted_class_average.average_id)
        db.session.add(class_prediction)
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/class/testclass1', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'access' in response.data)

    def test_userStats(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id,
                                            student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        current_time = datetime.datetime.utcnow()
        tomorrow = current_time + datetime.timedelta(days=1)
        predicted_average = Predicted_Average(prediction=79, time_frame="Daily", date=tomorrow)
        db.session.add(predicted_average)
        db.session.commit()
        student_predicted_average = Student_Predicted_Average(user_id=u.user_id,
                                                              average_id=predicted_average.average_id)
        class_predicted_average = Class_Predicted_Average(class_id="test",
                                                          average_id=predicted_average.average_id)
        db.session.add_all([student_predicted_average, class_predicted_average])
        db.session.commit()
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/class/test/teststudent', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'access' in response.data)

    def test_endGame(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class=None)
        self.client.set_cookie('localhost', 'numGames', "4")
        self.client.set_cookie('localhost', 'correct', "4")
        self.client.set_cookie('localhost', 'activity_id', "1")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get('/endgame', content_type='html/text',
                                       follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'EyeLearn' in response.data)

    def test_playAgain(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "dog")
        self.client.set_cookie('localhost', 'activity_id', "7")
        response = self.client.post(
            '/playAgain',
            data={"status":"correct",
                  "path": "/tts"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

    def test_getVoice(self):
        voice = getVoice(0)
        self.assertEqual(voice, "French Female")

    def test_getRecognitionLanguage(self):
        recognitionLanguage = getRecognitionLangauge(0)
        self.assertEqual(recognitionLanguage, "fr-FR")

    def test_getEndpoint(self):
        endpoint = getEndpoint("sports")
        self.assertEqual(endpoint, "predictSport")

    def test_selfie(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "dog")
        self.client.set_cookie('localhost', 'activity_id', "3")
        response = self.client.post(
            '/selfie/sports'
        )
        self.assertTrue(b'Your word is....' in response.data)
        self.assertEqual(response.status_code, 200)

    def test_getDictForGame(self):
        wordDict = getDictForGame("sports")
        self.assertTrue("golf" in wordDict)

    def test_getDictForGame2(self):
        wordDict = getDictForGame(None)
        self.assertTrue(len(wordDict) > 0)


    def test_diff(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/difficulty'
            )

            self.assertEqual(response.status_code, 200)

    def test_diff2(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get(
                '/difficulty'
            )

            self.assertEqual(response.status_code, 200)

    def test_chooseGame(self):


        response = self.client.get(
            '/chooseGame'
        )
        self.assertEqual(response.status_code, 200)

    def test_chooseGame2(self):


        response = self.client.post(
            '/chooseGame'
        )
        self.assertEqual(response.status_code, 200)


    def test_numberOrSpelling(self):
        newClass = Class(class_id="test", class_name="test", language="French", year=2019, role="Class")
        db.session.add(newClass)
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "dog")
        self.client.set_cookie('localhost', 'activity_id', "1")
        #print(self.client.cookies.items())
        response = self.client.post(
            '/numbersOrSpelling'
        )

        self.assertEqual(response.status_code, 200)

    def test_numberOrSpelling2(self):
        newClass = Class(class_id="test", class_name="test", language="French", year=2019, role="Class")
        db.session.add(newClass)
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', " ")
        self.client.set_cookie('localhost', 'activity_id', "1")
        #print(self.client.cookies.get('word'))
        # print(self.client.cookies.items())
        response = self.client.post(
            '/numbersOrSpelling'
        )

        self.assertEqual(response.status_code, 200)

    def test_numbers(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', " ")
        self.client.set_cookie('localhost', 'activity_id', "2")
        response = self.client.post(
            '/numbers'
        )

        self.assertEqual(response.status_code, 200)

    def test_numbers2(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "11")
        self.client.set_cookie('localhost', 'activity_id', "2")
        response = self.client.post(
            '/numbers'
        )

        self.assertEqual(response.status_code, 200)

    def test_category(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "car")
        self.client.set_cookie('localhost', 'activity_id', "10")
        response = self.client.post(
            '/selfie/vehicles'
        )

        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.post')
    def test_sendTextImage(self, mock_post):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'[]'
        mock_post.return_value = the_response
        image = open("app/static/testing/object.png", "rb")
        self.client.set_cookie('localhost', 'word', "onze")
        response = self.client.post(
            '/sendTextImage',
            data={'image': image}
        )
        image.close()
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.post')
    def test_sendSelfie(self, mock_post):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'car'
        mock_post.return_value = the_response
        image = open("app/static/testing/object.png", "rb")
        self.client.set_cookie('localhost', 'word', "car")
        self.client.set_cookie('localhost', 'numGames', "0")
        self.client.set_cookie('localhost', 'correct', "0")
        response = self.client.post(
            '/sendSelfie/vehicles',
            data={'image': image}
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.post')
    def test_sendSpeech(self, mock_post):
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"transcription" : "car"}'
        mock_post.return_value = the_response
        audio = open("app/static/testing/jackhammer.wav", "rb")
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "car")
        self.client.set_cookie('localhost', 'numGames', "0")
        self.client.set_cookie('localhost', 'correct', "0")
        response = self.client.post(
            '/sendSpeech',
            data={'audio_data': audio}
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.post')
    def test_getSpeechTranslation(self, mock_post):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            the_response = Response()
            the_response.status_code = 200
            the_response._content = b'{"transcription" : "car",' \
                                    b'"translation": "voiture"}'
            mock_post.return_value = the_response
            audio = open("app/static/testing/jackhammer.wav", "rb")
            self.client.set_cookie('localhost', 'word', "car")
            response = self.client.post(
                '/getSpeechTranslation',
                data={'audio_data': audio}
            )
            self.assertEqual(response.status_code, 200)

    def test_speechTranslation(self):
        response = self.client.get(
            '/speechTranslation'
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.post')
    def test_sendImage(self, mock_post):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            the_response = Response()
            the_response.status_code = 200
            the_response._content = b'{"predictions" : ["car","bus","truck"]}'
            mock_post.return_value = the_response
            image = open("app/static/testing/object.png", "rb")
            self.client.set_cookie('localhost', 'word', "car")
            response = self.client.post(
                '/sendImage',
                data={'image': image}
            )
            self.assertEqual(response.status_code, 200)

    def test_scramble(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "car")
        self.client.set_cookie('localhost', 'activity_id', "6")
        response = self.client.post(
            '/scramble'
        )
        self.assertEqual(response.status_code, 200)

    def test_scramble2(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', " ")
        self.client.set_cookie('localhost', 'activity_id', "6")
        response = self.client.post(
            '/scramble'
        )
        self.assertEqual(response.status_code, 200)

    def test_speech(self):
        newClass = Class(class_id="test", class_name="test", language="French", year=2019, role="Class")
        db.session.add(newClass)
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', "car")
            self.client.set_cookie('localhost', 'activity_id', "8")
            response = self.client.post(
                '/speech'
            )
            self.assertEqual(response.status_code, 200)

    def test_speech2(self):
        newClass = Class(class_id="test", class_name="test", language="French", year=2019, role="Class")
        db.session.add(newClass)
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', " ")
            self.client.set_cookie('localhost', 'activity_id', "8")
            response = self.client.post(
                '/speech'
            )
            self.assertEqual(response.status_code, 200)

    def test_tts(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "car")
        self.client.set_cookie('localhost', 'activity_id', "7")
        response = self.client.post(
            '/tts'
        )
        self.assertEqual(response.status_code, 200)

    def test_tts2(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', " ")
        self.client.set_cookie('localhost', 'activity_id', "7")
        response = self.client.post(
            '/tts'
        )
        self.assertEqual(response.status_code, 200)

    def test_getMorePictures(self):
        # response = self.client.post(
        #     '/getMorePictures/vehicles'
        # )
        # self.assertEqual(response.status_code, 200)
        pass

    def test_getMorePictures2(self):
        # response = self.client.post(
        #     '/getMorePictures/animals'
        # )
        # self.assertEqual(response.status_code, 200)
        pass

    def test_image(self):
        response = self.client.get(
            '/image'
        )
        self.assertEqual(response.status_code, 200)

    # #@mock.patch("request.referrer")
    # def test_check(self):
    #     self.client.set_cookie('localhost', 'languageIndex', "0")
    #     #mocked_url.return_value = "http://localhost:5000/tts"
    #     self.client.set_cookie('localhost', 'word', "car")
    #     self.client.set_cookie('localhost', 'numGames', "0")
    #     self.client.set_cookie('localhost', 'correct', "0")
    #     response = self.client.post(
    #         '/checkguess',
    #         data={"guess": "car"}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #
    # def test_check2(self):
    #     create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
    #     with self.client:
    #         login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
    #         self.client.set_cookie('localhost', 'languageIndex', "0")
    #         self.client.set_cookie('localhost', 'word', "dog")
    #         self.client.set_cookie('localhost', 'numGames', "0")
    #         self.client.set_cookie('localhost', 'correct', "0")
    #         response = self.client.post(
    #             '/checkguess',
    #             data={"guess": "car"},
    #         )
    #         self.assertEqual(response.status_code, 200)

    def test_checkWord(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', "dog")
            response = self.client.post(
                '/checkWord',
                data={"guess": "car"}
            )
            self.assertEqual(response.status_code, 200)

    def test_checkWord2(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', "dog")
            response = self.client.post(
                '/checkWord',
                data={"guess": "dog"}
            )
            self.assertEqual(response.status_code, 200)

    def test_checkNumber(self):
        self.client.set_cookie('localhost', 'word', "one")
        response = self.client.post(
            '/checkNumber',
            data={"jsonval": "1"}
        )
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get(
            '/about'
        )
        self.assertEqual(response.status_code, 200)

    def test_answer(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', "car")
            response = self.client.post(
                '/answer',
                data={"path": "/tts"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.status_code, 200)

    def test_imagenet(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "backpack")
        self.client.set_cookie('localhost', 'activity_id', "5")
        response = self.client.post(
            '/imagenet/classroom'
        )
        self.assertEqual(response.status_code, 200)

    def test_imagenet2(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', " ")
        self.client.set_cookie('localhost', 'activity_id', "5")
        response = self.client.post(
            '/imagenet/classroom'
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch('requests.post')
    def test_sendImagenet(self, mock_post):
        self.client.set_cookie('localhost', 'word', "monitor")
        self.client.set_cookie('localhost', 'numGames', "0")
        self.client.set_cookie('localhost', 'correct', "0")
        the_response = Response()
        the_response.status_code = 200
        the_response._content = b'{"predictions" : [["monitor","moniteur", "car"]]}'
        mock_post.return_value = the_response
        image = open("app/static/testing/object.png", "rb")
        response = self.client.post(
            '/sendImagenet/classroom',
            data={'image': image}
        )
        self.assertEqual(response.status_code, 200)

    def test_getWords(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "to go")
        self.client.set_cookie('localhost', 'activity_id', "16")
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get(
                'getWords/to_go'
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("data" in data)
            self.assertTrue("aller" in data['data'])

    def test_phraseTranslator(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        response = self.client.post(
            '/phraseTranslator'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Tagger" in response.data)

    def test_doodle(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "helmet")
        self.client.set_cookie('localhost', 'activity_id', "15")
        response = self.client.post(
            '/doodle'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"casque" in response.data)

    def test_getWord(self):
        word, foreignWord = getWordForDoodle(0, 2)
        self.assertTrue(word != None)
        self.assertTrue(foreignWord != None)

    def test_findWord(self):
        word, model = findWordForDoodle("helmet", 0)
        self.assertEqual(word, "casque")

    def test_tiles(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/tiles'
            )
            self.assertEqual(response.status_code, 302) ##Redirect as the student does not have any vocab

    def test_tilesGame(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "chien")
        self.client.set_cookie('localhost', 'activity_id', "14")
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            newVocab = Student_Vocab(english="dog", translation="chien", user_id=current_user.user_id,
                                     class_id=current_user.current_class, activity_id=14)
            db.session.add(newVocab)
            db.session.commit()
            response = self.client.post(
                '/tilesGame'
            )
            self.assertEqual(response.status_code, 200)

    def test_getWordsForTiles(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            newVocab = Student_Vocab(english="dog", translation="chien", user_id=current_user.user_id,
                                     class_id=current_user.current_class, activity_id=14)
            db.session.add(newVocab)
            db.session.commit()
            response = self.client.get(
                '/getWordsForTiles'
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("english" in data)

    def test_find(self):
        self.client.set_cookie('localhost', 'languageIndex', "0")
        self.client.set_cookie('localhost', 'word', "hand")
        self.client.set_cookie('localhost', 'activity_id', "15")
        response = self.client.post(
            '/find'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"main" in response.data)

    def test_getWord_find(self):
        word, foreignWord = getWord(0)
        self.assertTrue(word != None)
        self.assertTrue(foreignWord != None)

    def test_findWord_find(self):
        word = findWord("hand", 0)
        self.assertEqual(word, "main")

    def test_swipeWords(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', " ")
            self.client.set_cookie('localhost', 'activity_id', "16")
            response = self.client.post(
                '/swipeWords'
            )
            self.assertEqual(response.status_code, 200)

    def test_swipeWords2(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', "to go")
            self.client.set_cookie('localhost', 'activity_id', "16")
            response = self.client.post(
                '/swipeWords'
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b'to go' in response.data)


    def test_info(self):
        response = self.client.post(
            '/info'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Access" in response.data)

    def test_getLevelCSS(self):
        css = getLevelCSS(1)
        self.assertEqual(len(css), 4)

    def test_processConfiguration(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        config = {'layout': {
            '2': ['Scramble', 'Spelling', 'Classroom Items', 'Listen Up!', 'Numbers', 'Sports', 'Speak Up!',
                  'Swipe Sports',
                  'Vehicles', 'Swipe Vehicles'],
            '3': ['Swipe Emojis', 'Swipe Animals', 'Doodle', 'New Words', 'Find Me'],
            '4': ['Doing What?', 'Speech Translator', 'Object Translator', 'Phrase Translator & Tagger',
                  'Your New Words']},
            'data': {'Listen Up!': ['a', 'b'], 'Speak Up!': ['a', 'b'], 'Scramble': ['a', 'b'],
                     'Doing What?': ['a', 'b'], 'Spelling': ['a', 'b'], 'New Words': ['a', 'b']},
            'unlock_data': {'1': '3', '2': '3', '3': '3'}}
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/processConfiguration/test',
                data = {'config':json.dumps(config)}
            )
            self.assertEqual(response.status_code, 302)


    def test_processConfiguration2(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        data = {'layout': {
            '2': ['Scramble', 'Spelling', 'Classroom Items', 'Listen Up!', 'Numbers', 'Sports', 'Speak Up!',
                  'Swipe Sports',
                  'Vehicles', 'Swipe Vehicles'],
            '3': ['Swipe Emojis', 'Swipe Animals', 'Doodle', 'New Words', 'Find Me'],
            '4': ['Doing What?', 'Speech Translator', 'Object Translator', 'Phrase Translator & Tagger',
                  'Your New Words']},
            'data': {'Listen Up!': ['a', 'b'], 'Speak Up!': ['a', 'b'], 'Scramble': ['a', 'b'],
                     'Doing What?': ['a', 'b'], 'Spelling': ['a', 'b'], 'New Words': ['a', 'b']},
            'unlock_data': {'1': '3', '2': '3', '3': '3'}}
        classConfig = Class_Configs(class_id="test", layout_data=json.dumps(data['layout']),
                                    vocab_data=json.dumps(data['data']), unlock_data=json.dumps(data['unlock_data']))
        db.session.add_all([newClass, classConfig])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/processConfiguration/test',
                data = {'config':json.dumps(data)}
            )
            self.assertEqual(response.status_code, 302)

    def test_get_translation(self):
        data =  {'Listen Up!': ['a', 'b'], 'Speak Up!': ['a', 'b'], 'Scramble': ['a', 'b'],
                 'Doing What?': ['a', 'b'], 'Spelling': ['a', 'b'], 'New Words': ['a', 'b']}
        d = get_translation(data, "French")
        self.assertTrue("Scramble" in d.keys())

    def test_cert(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        user_id = create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        print(user_id)
        with self.client:
            scl = Student_Class_Level(user_id=user_id, class_id='test', level=4)
            db.session.add(scl)
            db.session.commit()
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
        response = self.client.post(
            '/cert/test/' + app.config['USERNAME']
        )
        self.assertEqual(response.status_code, 302)

    #TODO test_cert2

    def test_createClassConfiguration(self):
        response = self.client.post(
            '/classconfig/test'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Activities" in response.data)

    def test_createClassConfiguration2(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        data = {'layout': {
            '2': ['Scramble', 'Spelling', 'Classroom Items', 'Listen Up!', 'Numbers', 'Sports', 'Speak Up!',
                  'Swipe Sports',
                  'Vehicles', 'Swipe Vehicles'],
            '3': ['Swipe Emojis', 'Swipe Animals', 'Doodle', 'New Words', 'Find Me'],
            '4': ['Doing What?', 'Speech Translator', 'Object Translator', 'Phrase Translator & Tagger',
                  'Your New Words']},
            'data': {'Listen Up!': ['a', 'b'], 'Speak Up!': ['a', 'b'], 'Scramble': ['a', 'b'],
                     'Doing What?': ['a', 'b'], 'Spelling': ['a', 'b'], 'New Words': ['a', 'b']},
            'unlock_data': {'1': '3', '2': '3', '3': '3'}}
        classConfig = Class_Configs(class_id="test", layout_data=json.dumps(data['layout']),
                                    vocab_data=json.dumps(data['data']), unlock_data=json.dumps(data['unlock_data']))
        db.session.add_all([newClass, classConfig])
        db.session.commit()
        response = self.client.post(
            '/classconfig/test'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Activities" in response.data)

    def test_hasAccess(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.assertTrue(hasAccess("test", app.config["USERNAME"]))

    def test_hasAccessToClass(self):
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'])
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            self.assertFalse(hasAccessToClass("test"))

    def test_saveDoodle(self):
        data = {'doodle': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACgAAAAQcCAYAAABZf8JlAAAgAElEQVR4XuzdX6iX1bYG4C81KlFJDQ0FM4IVJqVFFlakQoVYkVIhBv0xMhLMQsyKzOValZVlpEWGUaKIhFkUmQgKKShYeiFYhoKJSYkUZiKamnr4TQ7sm8NxstP5/YY+wqZ9MZbz9Rnj8uVbF5w6depU5Q8BAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECAQSuACBcBQ+xKWAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgkAQVAh0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBB95u90AACAASURBVAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgACB80xg+/bt1fr166tt27ZVu3fvrjp37lxdffXV1dChQ6sbb7yx6tat23km4p9LgAABAgQIECBAgAABAgQIECBAIKaAAmDMvUlNgAABAgQIECBAgAABAgQIECBA4L8S+Prrr6t58+ZVO3bsqA4ePFgdOXKk6tixY9W1a9eqe/fu1ciRI6sJEyZU11xzzX/19/shAgQIECBAgAABAgQIECBAgAABAgTKCSgAlrP2EgECBAgQIECAAAECBAgQIECAAIFaBdauXVvNmjWrWrduXXXs2LH/M0uPHj2qp59+upo8eXLV+P/+ECBAgAABAgQIECBAgAABAgQIECDQvAIKgM27G8kIECBAgAABAgQIECBAgAABAgQInDGBnTt3VrNnz66WLFlSHT58+P/9exu/Bri1tbW65557ztj7/iICBAgQIECAAAECBAgQIECAAAECBM68gALgmTf1NxIgQIAAAQIECBAgQIAAAQIECBBoOoGVK1dWM2fOrDZt2nTabJdcckn6CuDzzz/vK4Cn1TJAgAABAgQIECBAgAABAgQIECBAoD4BBcD67L1MgAABAgQIECBAgAABAgQIECBAoJjAggULUgFw7969WW+OHTs2fQVwwIABWfOGCBAgQIAAAQIECBAgQIAAAQIECBAoL6AAWN7ciwQIECBAgAABAgQIECBAgAABAgSKC7z22mupAPjPP/9kvX3HHXekAuBtt92WNW+IAAECBAgQIECAAAECBAgQIECAAIHyAgqA5c29SIAAAQIECBAgQIAAAQIECBAgQKC4QFtbWyoA5v4ZPnx4KgA2/usPAQIECBAgQIAAAQIECBAgQIAAAQLNKaAA2Jx7kYoAAQIECBAgQIAAAQIECBAgQIDAGRVQADyjnP4yAgQIECBAgAABAgQIECBAgAABAk0hoADYFGsQggABAgQIECBAgAABAgQIECBAgMDZFZg1a1b6AuDx48ezHho6dGiav+uuu7LmDREgQIAAAQIECBAgQIAAAQIECBAgUF5AAbC8uRcJECBAgAABAgQIECBAgAABAgQIFBd45513qsZXAA8ePJj19nXXXZcKgGPGjMmaN0SAAAECBAgQIECAAAECBAgQIECAQHkBBcDy5l4kQIAAAQIECBAgQIAAAQIECBAgUFxg/vz5qQC4b9++rLevuuqqqrW1tXr44Yez5g0RIECAAAECBAgQIECAAAECBAgQIFBeQAGwvLkXCRAgQIAAAQIECBAgQIAAAQIECBQXWLRoUSoA7tq1K+vtPn36pALgk08+mTVviAABAgQIECBAgAABAgQIECBAgACB8gIKgOXNvUiAAAECBAgQIECAAAECBAgQIECguMAXX3yRfqXv1q1bs97u0aNHKgBOnjw5a94QAQIECBAgQIAAAQIECBAgQIAAAQLlBRQAy5t7kQABAgQIECBAgAABAgQIECBAgEBxgdWrV6cvAG7YsCHr7c6dO6cC4LRp07LmDREgQIAAAQIECBAgQIAAAQIECBAgUF5AAbC8uRcJECBAgAABAgQIECBAgAABAgQIFBf47rvv0hcAV61alfV2hw4dUgFwxowZWfOGCBAgQIAAAQIECBAgQIAAAQIECBAoL6AAWN7ciwQIECBAgAABAgQIECBAgAABAgSKC2zbti19AXDZsmXZb0+ZMiWVBrt27Zr9MwYJECBAgAABAgQIECBAgAABAgQIECgnoABYztpLBAgQIECAAAECBAgQIECAAAECBGoT2LNnTyoAfvzxx9kZxo8fn74CeMUVV2T/jEECBAgQIECAAAECBAgQIECAAAECBMoJKACWs/YSAQIECBAgQIAAAQIECBAgQIAAgdoE/vzzz/Q1v3nz5mVnGD16dCoADh48OPtnDBIgQIAAAQIECBAgQIAAAQIECBAgUE5AAbCctZcIECBAgAABAgQIECBAgAABAgQI1CZw7Nix9AXAWbNmZWe4/fbbU2lwxIgR2T9jkAABAgQIECBAgAABAgQIECBAgACBcgIKgOWsvUSAAAECBAgQIECAAAECBAgQIECgNoFTp05Vr7/+etXe3l4dPXo0K8e1116bvgB4//33Z80bIkCAAAECBAgQIECAAAECBAgQIECgrIACYFlvrxEgQIAAAQIECBAgQIAAAQIECBCoTaDx638bXwHcv39/VoZ+/fqlLwCOHz8+a94QAQIECBAgQIAAAQIECBAgQIAAAQJlBRQAy3p7jQABAgQIECBAgAABAgQIECBAgEBtAp988kkq9O3ZsycrQ8+ePdP8pEmTsuYNESBAgAABAgQIECBAgAABAgQIECBQVkABsKy31wgQIECAAAECBAgQIECAAAECBAjUJrB8+fL0BcAffvghK0Pnzp3TrwCeNm1a1rwhAgQIECBAgAABAgQIECBAgAABAgTKCigAlvX2GgECBAgQIECAAAECBAgQIECAAIHaBFavXp0KgBs2bMjK0KFDh+rll1+uZsyYUTX+vz8ECBAgQIAAAQIECBAgQIAAAQIECDSXgAJgc+1DGgIECBAgQIAAAQIECBAgQIAAAQJnTWDTpk3pV/quXLky+43G1/8aXwFsfA3QHwIECBAgQIAAAQIECBAgQIAAAQIEmktAAbC59iENAQIECBAgQIAAAQIECBAgQIAAgbMmsGPHjvQFwKVLl2a/MWnSpFQAvOyyy7J/xiABAgQIECBAgAABAgQIECBAgAABAmUEFADLOHuFAAECBAgQIECAAAECBAgQIECAQO0C+/btSwXA+fPnZ2d5/PHHUwGwX79+2T9jkAABAgQIECBAgAABAgQIECBAgACBMgIKgGWcvUKAAAECBAgQIECAAAECBAgQIECgdoG///47FQDfeOON7Czjxo1Lvza4paUl+2cMEiBAgAABAgQIECBAgAABAgQIECBQRkABsIyzVwgQIECAAAECBAgQIECAAAECBAjULnDq1KnqlVdeqdrb26sTJ05k5RkzZkz6AuCgQYOy5g0RIECAAAECBAgQIECAAAECBAgQIFBOQAGwnLWXCBAgQIAAAQIECBAgQIAAAQIECNQu0Pj6X+OLfkePHs3KMnLkyDR/8803Z80bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXeDtt99Ovwb40KFDWVmGDx+evgDY+K8/BAgQIECAAAECBAgQIECAAAECBAg0l4ACYHPtQxoCBAgQIECAAAECBAgQIECAAAECZ1Vg7ty56Yt+Bw4cyHqn8eW/xnzjS4D+ECBAgAABAgQIECBAgAABAgQIECDQXAIKgM21D2kIECBAgAABAgQIECBAgAABAgQInFWBDz74IBX6fv/996x3Bg0alL4AOGbMmKx5QwQIECBAgAABAgQIECBAgAABAgQIlBNQACxn7SUCBAgQIECAAAECBAgQIECAAAECtQssWLAg/Qrg3377LStLS0tLKgyOGzcua94QAQIECBAgQIAAAQIECBAgQIAAAQLlBBQAy1l7iQABAgQIECBAgAABAgQIECBAgEDtAgsXLkwFwN27d2dl6d+/f/oC4GOPPZY1b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaBJUuWpC/67dy5MytL3759UwFwwoQJWfOGCBAgQIAAAQIECBAgQIAAAQIECBAoJ6AAWM7aSwQIECBAgAABAgQIECBAgAABAgRqF/j0009TAXD79u1ZWXr37p0KgBMnTsyaN0SAAAECBAgQIECAAAECBAgQIECAQDkBBcBy1l4iQIAAAQIECBAgQIAAAQIECBAgULvA8uXLUwHwxx9/zMrSs2fPND9p0qSseUMECBAgQIAAAQIECBAgQIAAAQIECJQTUAAsZ+0lAgQIECBAgAABAgQIECBAgAABArULfPnll1VbW1u1ZcuWrCyXXnpp+gLgs88+mzVviAABAgQIECBAFkNdPwAAIABJREFUgAABAgQIECBAgACBcgIKgOWsvUSAAAECBAgQIECAAAECBAgQIECgdoEVK1akAuDmzZuzsnTp0iUVAKdOnZo1b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaBVatWpQLgxo0bs7JcfPHFqQD4wgsvZM0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXWDNmjWpALh+/fqsLJ06dUoFwOnTp2fNGyJAgAABAgQIECBAgAABAgQIECBAoJyAAmA5ay8RIECAAAECBAgQIECAAAECBAgQqF1g7dq11cyZM6t169ZlZbngggtSAbDxP38IECBAgAABAgQIECBAgAABAgQIEGguAQXA5tqHNAQIECBAgAABAgQIECBAgAABAgTOqkCjANj4AmDjv7l/GoVBBcBcLXMECBAgQIAAAQIECBAgQIAAAQIEygkoAJaz9hIBAgQIECBAgAABAgQIECBAgACB2gUUAGtfgQAECBAgQIAAAQIECBAgQIAAAQIEzpiAAuAZo/QXESBAgAABAgQIECBAgAABAgQIEGh+AQXA5t+RhAQIECBAgAABAgQIECBAgAABAgRyBRQAc6XMESBAgAABAgQIECBAgAABAgQIEDgHBBQAz4El+icQIECAAAECBAgQIECAAAECBAgQ+F8BBUCnQIAAAQIECBAgQIAAAQIECBAgQOA8ElAAPI+W7Z9KgAABAgQIECBAgAABAgQIECBwzgsoAJ7zK/YPJECAAAECBAgQIECAAAECBAgQIPAfAQVA10CAAAECBAgQIECAAAECBAgQIEDg3BFQADx3dulfQoAAAQIECBAgQIAAAQIECBAgQOC0AgqApyUyQIAAAQIECBAgQIAAAQIECBAgQCCMgAJgmFUJSoAAAQIECBAgQIAAAQIECBAgQODfCygA/ntDfwMBAgQIECBAgAABAgQIECBAgACBZhFQAGyWTchBgAABAgQIECBAgAABAgQIECBAoICAAmABZE8QIECAAAECBAgQIECAAAECBAgQKCSgAFgI2jMECBAgQIAAAQIECBAgQIAAAQIEmkFAAbAZtiADAQIECBAgQIAAAQIECBAgQIAAgTMjoAB4Zhz9LQQIECBAgAABAgQIECBAgAABAgRCCCgAhliTkAQIECBAgAABAgQIECBAgAABAgSyBBQAs5gMESBAgAABAgQIECBAgAABAgQIEDg3BBQAz409+lcQIECAAAECBAgQIECAAAECBAgQaAgoALoDAgQIECBAgAABAgQIECBAgAABAueRgALgebRs/1QCBAgQIECAAAECBAgQIECAAIFzXkAB8JxfsX8gAQIECBAgQIAAAQIECBAgQIAAgf8IKAC6BgIECBAgQIAAAQIECBAgQIAAAQLnjoAC4LmzS/8SAgQIECBAgAABAgQIECBAgAABAqcVUAA8LZEBAgQIECBAgAABAgQIECBAgAABAmEEFADDrEpQAgQIECBAgAABAgQIECBAgAABAv9eQAHw3xv6GwgQIECAAAECBAgQIECAAAECBAg0i4ACYLNsQg4CBAgQIECAAAECBAgQIECAAAECBQS+/fbbqq2trVq3bl3Wax06dKhaW1urGTNmZM0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXWDNmjXVzJkzqw0bNmRlueiii1IB8MUXX8yaN0SAAAECBAgQIECAAAECBAgQIECAQDkBBcBy1l4iQIAAAQIECBAgQIAAAQIECBAgULvAqlWr0hcAN27cmJWlS5cuqQA4derUrHlDBAgQIECAAAECBAgQIECAAAECBAiUE1AALGftJQIECBAgQIAAAQIECBAgQIAAAQK1C6xYsSIVADdv3pyVpXv37qkA+Mwzz2TNGyJAgAABAgQIECBAgAABAgQIECBAoJyAAmA5ay8RIECAAAECBAgQIECAAAECBAgQqF3gq6++Sr8CeMuWLVlZevXqleYnTpyYNW+IAAECBAgQIECAAAECBAgQIECAAIFyAgqA5ay9RIAAAQIECBAgQIAAAQIECBAgQKB2gc8//zx9AXDr1q1ZWfr27ZsKgE888UTWvCECBAgQIECAAAECBAgQIECAAAECBMoJKACWs/YSAQIECBAgQIAAAQIECBAgQIAAgdoFli1blgp9P/30U1aW/v37p/lHH300a94QAQIECBAgQIAAAQIECBAgQIAAAQLlBBQAy1l7iQABAgQIECBAgAABAgQIECBAgEDtAkuXLk1fANyxY0dWlpaWlqq1tbV66KGHsuYNESBAgAABAgQIECBAgAABAgQIECBQTkABsJy1lwgQIECAAAECBAgQIECAAAECBAjULrB48eJUAPz555+zsgwcODAVAB988MGseUMECBAgQIAAAQIECBAgQIAAAQIECJQTUAAsZ+0lAgQIECBAgAABAgQIECBAgAABArULLFy4MP1K319++SUry+DBg1MBcPTo0VnzhggQIECAAAECBAgQIECAAAECBAgQKCegAFjO2ksECBAgQIAAAQIECBAgQIAAAQIEahf46KOP0hcAf/3116wsQ4YMSYXBUaNGZc0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXeDDDz9Mhb59+/ZlZbnlllvS/J133pk1b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaB999/P30B8I8//sjKMmzYsFQAHD58eNa8IQIECBAgQIAAAQIECBAgQIAAAQIEygkoAJaz9hIBAgQIECBAgAABAgQIECBAgACB2gXmzp2bCn0HDhzIytL48l9ra2t16623Zs0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXWDOnDmpAHjo0KGsLKNGjUoFwJtuuilr3hABAgQIECBAgAABAgQIECBAgAABAuUEFADLWXuJAAECBAgQIECAAAECBAgQIECAQO0Cb775ZvoVwEeOHMnKct9996UC4PXXX581b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaBWbNmpS8AHj9+PCvLAw88kOYHDhyYNW+IAAECBAgQIECAAAECBAgQIECAAIFyAgqA5ay9RIAAAQIECBAgQIAAAQIECBAgQKB2gfb29vQFwJMnT2ZlGTduXCoAtrS0ZM0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoVaDxa38bZb7Zs2dn53jkkUfSz1x55ZXZP2OQAAECBAgQIECAAAECBAgQIECAAIEyAgqAZZy9QoAAAQIECBAgQIAAAQIECBAgQKB2gb1796Yy34IFC7KzTJw4Mf1Mr169sn/GIAECBAgQIECAAAECBAgQIECAAAECZQQUAMs4e4UAAQIECBAgQIAAAQIECBAgQIBA7QLbtm1LZb7PPvssO8tzzz2XfqZz587ZP2OQAAECBAgQIECAAAECBAgQIECAAIEyAgqAZZy9QoAAAQIECBAgQIAAAQIECBAgQKB2gQ0bNlRtbW3V6tWrs7J07NixmjFjRjV9+vSqQ4cOWT9jiAABAgQIECBAgAABAgQIECBAgACBcgIKgOWsvUSAAAECBAgQIECAAAECBAgQIECgVoFvvvkmfc1v8+bNWTm6detWtba2VlOmTMmaN0SAAAECBAgQIECAAAECBAgQIECAQFkBBcCy3l4jQIAAAQIECBAgQIAAAQIECBAgUJvAkiVLUgFw586dWRn69OmT5idMmJA1b4gAAQIECBAgQIAAAQIECBAgQIAAgbICCoBlvb1GgAABAgQIECBAgAABAgQIECBAoDaB9957LxX69u/fn5WhpaUlzY8bNy5r3hABAgQIECBAgAABAgQIECBAgAABAmUFFADLenuNAAECBAgQIECAAAECBAgQIECAQC0CJ0+erF599dWqvb29OnHiRFaGG264IRUA77333qx5QwQIECBAgAABAgQIECBAgAABAgQIlBVQACzr7TUCBAgQIECAAAECBAgQIECAAAECtQj89ddfqcz37rvvZr8/bNiwqrW1tRoxYkT2zxgkQIAAAQIECBAgQIAAAQIECBAgQKCcgAJgOWsvESBAgAABAgQIECBAgAABAgQIEKhNYNeuXVVbW1u1aNGi7Ax33313KgAOGTIk+2cMEiBAgAABAgQIECBAgAABAgQIECBQTkABsJy1lwgQIECAAAECBAgQIECAAAECBAjUJrBp06b0BcCVK1dmZxg7dmwqAA4YMCD7ZwwSIECAAAECBAgQIECAAAECBAgQIFBOQAGwnLWXCBAgQIAAAQIECBAgQIAAAQIECNQm0Cj+Nb4A+P3332dneOqpp1IB8PLLL8/+GYMECBAgQIAAAQIECBAgQIAAAQIECJQTUAAsZ+0lAgQIECBAgAABAgQIECBAgAABArUJLF68OH0BsPGrgHP+dOrUqXrppZfS/y688MKcHzFDgAABAgQIECBAgAABAgQIECBAgEBhAQXAwuCeI0CAAAECBAgQIECAAAECBAgQIFCHwJw5c1IB8NChQ1nP9+7dO803vgLoDwECBAgQIECAAAECBAgQIECAAAECzSmgANice5GKAAECBAgQIECAAAECBAgQIECAwBkTOHz4cNXe3l699dZb1cmTJ7P+3sGDB6df/zt69OiseUMECBAgQIAAAQIECBAgQIAAAQIE/oe9Ow3yujrzhn+xNAjuEhUFIypu4z4uEDfEDbdo0DFEcRcBFdwDNNC2TTebigoIanRwiqgZxXIB4xIzrhkXNOAS0IkLFdRRAVFBpVm6eap/99xPzXM/k9vTTS//5dNVli+4rnOu8zn/l9/6HQLNLyAA2PzmdiRAgAABAgQIECBAgAABAgQIECDQrAKffPJJ9jW/GTNmJO97wgknZD09evRI7lFIgAABAgQIECBAgAABAgQIECBAgEDzCggANq+33QgQIECAAAECBAgQIECAAAECBAg0u8C8efOyMN+cOXOS977wwguzLwDuuOOOyT0KCRAgQIAAAQIECBAgQIAAAQIECBBoXgEBwOb1thsBAgQIECBAgAABAgQIECBAgACBZhd45plnoqKiIl599dXkvUtLS7PQYLt27ZJ7FBIgQIAAAQIECBAgQIAAAQIECBAg0LwCAoDN6203AgQIECBAgAABAgQIECBAgAABAs0ucP/992dhvg8//DBp76222iqrHzp0aFK9IgIECBAgQIAAAQIECBAgQIAAAQIEWkZAALBl3O1KgAABAgQIECBAgAABAgQIECBAoNkEbrvttizQ9+233ybt+Q//8A9Z/ZlnnplUr4gAAQIECBAgQIAAAQIECBAgQIAAgZYREABsGXe7EiBAgAABAgQIECBAgAABAgQIEGgWgZUrV0ZlZWVMmjQpamtrk/Y85phjory8PI444oikekUECBAgQIAAAQIECBAgQIAAAQIECLSMgABgy7jblQABAgQIECBAgAABAgQIECBAgECzCPzlL3+JioqKePjhh5P369+/f/YFwO7duyf3KCRAgAABAgQIECBAgAABAgQIECBAoPkFBACb39yOBAgQIECAAAECBAgQIECAAAECBJpN4PHHH88CgPPnz0/e87rrrsu+ALjJJpsk9ygkQIAAAQIECBAgQIAAAQIECBAgQKD5BQQAm9/cjgQIECBAgAABAgQIECBAgAABAgSaRWDdunVx6623RlVVVaxYsSJpzy233DIL/11xxRXRqlWrpB5FBAgQIECAAAECBAgQIECAAAECBAi0jIAAYMu425UAAQIECBAgQIAAAQIECBAgQIBAkwv87W9/izFjxsS9994b69evT9pv3333zZ7/7du3b1K9IgIECBAgQIAAAQIECBAgQIAAAQIEWk5AALDl7O1MgAABAgQIECBAgAABAgQIECBAoEkFXnjhhez537r/p/6dfPLJ2RcADz744NQWdQQIECBAgAABAgQIECBAgAABAgQItJCAAGALwduWAAECBAgQIECAAAECBAgQIECAQFMLzJw5M/ua36JFi5K3GjBgQNbTpUuX5B6FBAgQIECAAAECBAgQIECAAAECBAi0jIAAYMu425UAAQIECBAgQIAAAQIECBAgQIBAkwp8++23MX78+Lj11ltjzZo1SXttuummMXLkyLj22mujpKQkqUcRAQIECBAgQIAAAQIECBAgQIAAAQItJyAA2HL2diZAgAABAgQIECBAgAABAgQIECDQZAILFy7MvuQ3a9as5D123XXXrOfss89O7lFIgAABAgQIECBAgAABAgQIECBAgEDLCQgAtpy9nQkQIECAAAECBAgQIECAAAECBAg0mcBTTz0VFRUV8frrryfvcdxxx2UBwEMPPTS5RyEBAgQIECBAgAABAgQIECBAgAABAi0nIADYcvZ2JkCAAAECBAgQIECAAAECBAgQINBkAnfddVcWAPz888+T9xg4cGAWANxuu+2SexQSIECAAAECBAgQIECAAAECBAgQINByAgKALWdvZwIECBAgQIAAAQIECBAgQIAAAQJNIrB06dKoqqqK6dOnx7p165L26Ny5c4wePToGDRoUbdu2TepRRIAAAQIECBAgQIAAAQIECBAgQIBAywoIALasv90JECBAgAABAgQIECBAgAABAgQINLrA3Llzsy/51T0DnPr3s5/9LOs5/vjjU1vUESBAgAABAgQIECBAgAABAgQIECDQwgICgC18AbYnQIAAAQIECBAgQIAAAQIECBAg0NgCDzzwQBbm++CDD5KXPvvss6O8vDx222235B6FBAgQIECAAAECBAgQIECAAAECBAi0rIAAYMv6250AAQIECBAgQIAAAQIECBAgQIBAowosX748xo8fH1OnTo3Vq1cnrb355pvHiBEj4uqrr4727dsn9SgiQIAAAQIECBAgQIAAAQIECBAgQKDlBQQAW/4OTECAAAECBAgQIECAAAECBAgQIECg0QT+/Oc/Z1//e+KJJ5LX3GeffbKe008/PblHIQECBAgQIECAAAECBAgQIECAAAECLS8gANjyd2ACAgQIECBAgAABAgQIECBAgAABAo0m8NBDD2Vhvvfeey95zV/84hfZ87/7779/co9CAgQIECBAgAABAgQIECBAgAABAgRaXkAAsOXvwAQECBAgQIAAAQIECBAgQIAAAQIEGkXgm2++iYkTJ8Ztt90W1dXVSWt26NAhrrnmmhg+fHhsuummST2KCBAgQIAAAQIECBAgQIAAAQIECBDIDQEBwNy4B1MQIECAAAECBAgQIECAAAECBAgQ2GCBt99+O/v632OPPZa81m677ZZ9/e+ss86KVq1aJfcpJECAAAECBAgQIECAAAECBAgQIECg5QUEAFv+DkxAgAABAgQIECBAgAABAgQIECBAoFEEHnnkkSwA+O677yavd+KJJ2YBwB49eiT3KCRAgAABAgQIECBAgAABAgQIECBAIDcEBABz4x5MQYAAAQIECBAgQIAAAQIECBAgQGCDBFasWBE33nhj3HLLLbFq1aqktdq2bRuXX355jB49On7yk58k9SgiQIAAAQIECBAgQIAAAQIECBAgQCB3BAQAc+cuTEKAAAECBAgQIECAAAECBAgQIECgwQLvvPNOVFRURN1XAFP/dtxxxygrK4sLLrgg2rRpk9qmjgABAgQIECBAgAABAgQIECBAgACBHBEQAMyRizAGAQIECBAgQIAAAQIECBAgQIAAgQ0RaMjzv0cffXT2/O+RRx65IVvrJUCAAAECBAgQIECAAAECBAgQIECghQQEAFsI3rYECBAgQIAAAQIECBAgQIAAAQIEGkugIc//1u19ySWXZAHALl26NNYo1iFAgAABAgQIECBAgAABAgQIECBAoBkFBACbEdtWBAgQIECAAAECBAgQIECAAAECBJpCoCHP/9aF/kaNGpWFANu2bdsUY1mTAAECBAgQIECAAAECBAgQIECAAIEmFhAAbGJgyxMgQIAAAQIECBAgQIAAAQIECBBoaoGGPP9b9+zvDTfcEL17927q8axPgAABAgQIECBAgAABAgQIECBAgEATCQgANhGsZQkQIECAAAECBAgQIECAAAECBAg0h0BDn/+98MILswDgT3/60+YY0x4ECBAgQIAAAQIECBAgQIAAAQIECDSBgABgE6BakgABAgQIECBAgAABAgQIECBAgEBzCTTk+d/OnTtnz/8OGjQoSkpKmmtU+xAgQIAAAQIECBAgQIAAAQIECBAg0MgCAoCNDGo5AgQIECBAgAABAgQIECBAgAABAs0p0JDnfw877LDs63/HHntsc45qLwIECBAgQIAAAQIECBAgQIAAAQIEGllAALCRQS1HgAABAgQIECBAgAABAgQIECBAoLkE6p7/nThxYtx6662xatWq5G3PO++8LAC40047JfcoJECAAAECBAgQIECAAAECBAgQIEAg9wQEAHPvTkxEgAABAgQIECBAgAABAgQIECBAIEng7bffzoJ8jz32WFJ9XdE222wTI0eOjEsvvTTatWuX3KeQAAECBAgQIECAAAECBAgQIECAAIHcExAAzL07MREBAgQIECBAgAABAgQIECBAgACBJIGHH344CwAuWLAgqb6uqGfPnllPnz59knsUEiBAgAABAgQIECBAgAABAgQIECCQmwICgLl5L6YiQIAAAQIECBAgQIAAAQIECBAg8H8V+Prrr7PnfydPnhzV1dXJWuecc04WANxll12SexQSIECAAAECBAgQIECAAAECBAgQIJCbAgKAuXkvpiJAgAABAgQIECBAgAABAgQIECDwfxWYN29eFuSbM2dOstR2220XpaWlMWjQIM//JqspJECAAAECBAgQIECAAAECBAgQIJC7AgKAuXs3JiNAgAABAgQIECBAgAABAgQIECDwdwUefPDBLAD4/vvvJyv16tUr6znqqKOSexQSIECAAAECBAgQIECAAAECBAgQIJC7AgKAuXs3JiNAgAABAgQIECBAgAABAgQIECDwPwp89dVXMWHChJg6dWqsXr06Salt27YxePDgGDVqVHTu3DmpRxEBAgQIECBAgAABAgQIECBAgAABArktIACY2/djOgIECBAgQIAAAQIECBAgQIAAAQL/P4E33ngj+5Lfk08+mazTvXv3GD16dJxzzjnRpk2b5D6FBAgQIECAAAECBAgQIECAAAECBAjkroAAYO7ejckIECBAgAABAgQIECBAgAABAgQI/I8CDzzwQBYA/OCDD5KFTjnllKznwAMPTO5RSIAAAQIECBAgQIAAAQIECBAgQIBAbgsIAOb2/ZiOAAECBAgQIECAAAECBAgQIECAwP9HYNmyZTF+/PiYNm1a8vO/m222WVx33XVxzTXXxMYbb0yUAAECBAgQIECAAAECBAgQIECAAIECERAALJCLdAwCBAgQIECAAAECBAgQIECAAIHiEHjllVeyL/k9++yzyQfef//9s57TTjstuUchAQIECBAgQIAAAQIECBAgQIAAAQK5LyAAmPt3ZEICBAgQIECAAAECBAgQIECAAAECmUBNTU3cc889UVlZGZ999lmyyq9+9assALj77rsn9ygkQIAAAQIECBAgQIAAAQIECBAgQCD3BQQAc/+OTEiAAAECBAgQIECAAAECBAgQIEAgE/joo4+iqqoq7rvvvli3bl2SyrbbbhulpaUxePDgaN++fVKPIgIECBAgQIAAAQIECBAgQIAAAQIE8kNAADA/7smUBAgQIECAAAECBAgQIECAAAECBGLOnDnZl/zmzZuXrHHEEUdkPUcffXRyj0ICBAgQIECAAAECBAgQIECAAAECBPJDQAAwP+7JlAQIECBAgAABAgQIECBAgAABAkUu8PXXX8eNN94YkydPjlWrViVptG7dOi655JK4/vrrY/vtt0/qUUSAAAECBAgQIECAAAECBAgQIECAQP4ICADmz12ZlAABAgQIECBAgAABAgQIECBAoIgF5s6dm33J76mnnkpW6NatW4wePTrOP//8aNu2bXKfQgIECBAgQIAAAQIECBAgQIAAAQIE8kNAADA/7smUBAgQIECAAAECBAgQIECAAAECRS7wL//yL1kA8G9/+1uyxAknnJD19OjRI7lHIQECBAgQIECAAAECBAgQIECAAAEC+SMgAJg/d2VSAgQIECBAgAABAgQIECBAgACBIhWoC/2NHTs26kKAa9euTVLo2LFjXHnllTFs2LDYYostknoUESBAgAABAgQIECBAgAABAgQIECCQXwICgPl1X6YlQIAAAQIECBAgQIAAAQIECBAoQoG6Z3/rvuRX9wxw6t9ee+0V119/fZx55pnRqlWr1DZ1BAgQIECAAAECBAgQIECAAAECBAjkkYAAYB5dllEJECBAgAABAgQIECBAgAABAgSKT2DFihUxadKkuOWWW+K7775LBjj99NOz0OA+++yT3KOQAAECBAgQIECAAAECBAgQIECAAIH8EhAAzK/7Mi0BAgQIECBAgAABAgQIECBAgECRCcybNy8qKipizpw5sX79+qTTb7XVVjF8+PC44oorYqONNkrqUUSAAAECBAgQIECAAAECBAgQIECAQP4JCADm352ZmAABAgQIECBAgAABAgQIECBAoIgE7rvvvuxLfh999FHyqQ8++OCs56STTkruUUiAAAECBAgQIECAAAECBAgQIECAQP4JCADm352ZmAABAgQIECBAgAABAgQIECBAoEgEPv300xg/fnx2QnBHAAAgAElEQVTcc889sWbNmuRTn3POOVkAcJdddknuUUiAAAECBAgQIECAAAECBAgQIECAQP4JCADm352ZmAABAgQIECBAgAABAgQIECBAoEgEnnvuuSzI9/LLLyefeLvttouRI0fGwIEDo127dsl9CgkQIECAAAECBAgQIECAAAECBAgQyD8BAcD8uzMTEyBAgAABAgQIECBAgAABAgQIFIHA2rVrY/r06TFu3LhYsmRJ8ol79eqVhQaPOuqo5B6FBAgQIECAAAECBAgQIECAAAECBAjkp4AAYH7em6kJECBAgAABAgQIECBAgAABAgQKXOCDDz6IqqqquP/++6OmpibptG3atIlBgwZFWVlZdO7cOalHEQECBAgQIECAAAECBAgQIECAAAEC+SsgAJi/d2dyAgQIECBAgAABAgQIECBAgACBAhZ44oknoqKiIt58883kU+68885Z+O/cc8+NujCgPwIECBAgQIAAAQIECBAgQIAAAQIECltAALCw79fpCBAgQIAAAQIECBAgQIAAAQIE8lDgu+++i0mTJmX/rVy5MvkEJ598cvb870EHHZTco5AAAQIECBAgQIAAAQIECBAgQIAAgfwVEADM37szOQECBAgQIECAAAECBAgQIECAQIEKvPPOO9nX/x599NFYv3590ik322yzuPbaa+Oaa66JTTbZJKlHEQECBAgQIECAAAECBAgQIECAAAEC+S0gAJjf92d6AgQIECBAgAABAgQIECBAgACBAhSYNWtWFgBcsGBB8ukOOOCAKC8vj1NPPTVatWqV3KeQAAECBAgQIECAAAECBAgQIECAAIH8FRAAzN+7MzkBAgQIECBAgAABAgQIECBAgEABCnz11VcxYcKEuP3226O6ujr5hGeffXb2/O+uu+6a3KOQAAECBAgQIECAAAECBAgQIECAAIH8FhAAzO/7Mz0BAgQIECBAgAABAgQIECBAgECBCbz++utZkO/pp59OPtn2228fpaWlMXDgwGjXrl1yn0ICBAgQIECAAAECBAgQIECAAAECBPJbQAAwv+/P9AQIECBAgAABAgQIECBAgAABAgUmMHPmzCwAuGjRouST9e7dO+s58sgjk3sUEiBAgAABAgQIECBAgAABAgQIECCQ/wICgPl/h05AgAABAgQIECBAgAABAgQIECBQIAL/+Z//GePGjYu777471qxZk3Sq9u3bx2WXXZZ9AXDrrbdO6lFEgAABAgQIECBAgAABAgQIECBAgEBhCAgAFsY9OgUBAgQIECBAgAABAgQIECBAgEABCDz//PPZl/xeeuml5NPsscceUVZWFv369Ys2bdok9ykkQIAAAQIECBAgQIAAAQIECBAgQCD/BQQA8/8OnYAAAQIECBAgQIAAAQIECBAgQKAABKqrq2PatGkxYcKEWLZsWfKJ+vbtm4UG99133+QehQQIECBAgAABAgQIECBAgAABAgQIFIaAAGBh3KNTECBAgAABAgQIECBAgAABAgQI5LnAggULorKyMmbNmhW1tbVJp+nUqVMMHz48hgwZEh06dEjqUUSAAAECBAgQIECAAAECBAgQIECAQOEICAAWzl06CQECBAgQIECAAAECBAgQIECAQB4L1AX/6r7kt3DhwuRT9OzZM+vp06dPco9CAgQIECBAgAABAgQIECBAgAABAgQKR0AAsHDu0kkIECBAgAABAgQIECBAgAABAgTyVOCLL77Inv696667ou4p4NS/Cy+8MAsA/vSnP01tUUeAAAECBAgQIECAAAECBAgQIECAQAEJCAAW0GU6CgECBAgQIECAAAECBAgQIECAQH4KvPDCC1mQ78UXX0w+QLdu3WLkyJFxwQUXRElJSXKfQgIECBAgQIAAAQIECBAgQIAAAQIECkdAALBw7tJJCBAgQIAAAQIECBAgQIAAAQIE8lCg7ot/06ZNy74AuGzZsuQTnHjiiVlo8JBDDknuUUiAAAECBAgQIECAAAECBAgQIECAQGEJCAAW1n06DQECBAgQIECAAAECBAgQIECAQJ4JLFiwICorK2PWrFlRW1ubNP1mm20W1157bVxzzTWxySabJPUoIkCAAAECBAgQIECAAAECBAgQIECg8AQEAAvvTp2IAAECBAgQIECAAAECBAgQIEAgjwTqgn91X/JbuHBh8tT/+I//GOXl5fHzn/88WrVqldynkAABAgQIECBAgAABAgQIECBAgACBwhIQACys+3QaAgQIECBAgAABAgQIECBAgACBPBL44osvsqd/77rrrqh7Cjj1r3///llosHv37qkt6ggQIECAAAECBAgQIECAAAECBAgQKEABAcACvFRHIkCAAAECBAgQIECAAAECBAgQyA+B559/PioqKuLFF19MHrhr165RWloaAwYMiHbt2iX3KSRAgAABAgQIECBAgAABAgQIECBAoPAEBAAL706diAABAgQIECBAgAABAgQIECBAIA8Evv/++5gyZUrcfPPNsXz58uSJjz322Ozrf4cddlhyj0ICBAgQIECAAAECBAgQIECAAAECBApTQACwMO/VqQgQIECAAAECBAgQIECAAAECBHJcYP78+TFmzJiYPXt21NbWJk3bsWPHGDp0aAwbNiy22mqrpB5FBAgQIECAAAECBAgQIECAAAECBAgUroAAYOHerZMRIECAAAECBAgQIECAAAECBAjksMDMmTOzL/ktWrQoecq99947rr/++jjjjDOidevWyX0KCRAgQIAAAQIECBAgQIAAAQIECBAoTAEBwMK8V6ciQIAAAQIECBAgQIAAAQIECBDIYYGPP/44xo0bF3UhwLVr1yZP+stf/jILDe65557JPQoJECBAgAABAgQIECBAgAABAgQIEChcAQHAwr1bJyNAgAABAgQIECBAgAABAgQIEMhRgccffzwL8r311lvJE3bu3DlGjBgRgwcPjvbt2yf3KSRAgAABAgQIECBAgAABAgQIECBAoHAFBAAL926djAABAgQIECBAgAABAgQIECBAIAcFvvzyy7jxxhvjjjvuiFWrViVP2KtXrygvL4/evXsn9ygkQIAAAQIECBAgQIAAAQIECBAgQKCwBQQAC/t+nY4AAQIECBAgQIAAAQIECBAgQCDHBF544YXs638vvvhi8mTt2rXLvvw3cuTI2HbbbZP7FBIgQIAAAQIECBAgQIAAAQIECBAgUNgCAoCFfb9OR4AAAQIECBAgQIAAAQIECBAgkEMC33//fUyZMiVuvvnmWL58efJku+++e5SVlcWvfvWraNOmTXKfQgIECBAgQIAAAQIECBAgQIAAAQIECltAALCw79fpCBAgQIAAAQIECBAgQIAAAQIEckhg/vz5MWbMmJg9e3bU1tYmT/aLX/wi+2rgfvvtl9yjkAABAgQIECBAgAABAgQIECBAgACBwhcQACz8O3ZCAgQIECBAgAABAgQIECBAgACBHBH47W9/mwX5Pv744+SJOnXqFMOHD48hQ4ZEhw4dkvsUEiBAgAABAgQIECBAgAABAgQIECBQ+AICgIV/x05IgAABAgQIECBAgAABAgQIECCQAwKLFi2KcePGxcyZM2PNmjXJE/Xs2TMLDfbp0ye5RyEBAgQIECBAgAABAgQIECBAgAABAsUhIABYHPfslAQIECBAgAABAgQIECBAgAABAi0sMGfOnCzIN2/evORJWrVqFRdddFGUl5fHDjvskNynkAABAgQIECBAgAABAgQIECBAgACB4hAQACyOe3ZKAgQIECBAgAABAgQIECBAgACBFhRYunRp3HjjjTFt2rRYtWpV8iQ77bRTjBo1Ks4777woKSlJ7lNIgAABAgQIECBAgAABAgQIECBAgEBxCAgAFsc9OyUBAgQIECBAgAABAgQIECBAgEALCrz88svZ1/+ee+65ek1xyimnZF//O+igg+rVp5gAAQIECBAgQIAAAQIECBAgQIAAgeIQEAAsjnt2SgIECBAgQIAAAQIECBAgQIAAgRYSqK6ujunTp8eECROi7kuAqX+dOnWKYcOGxZAhQ6Jjx46pbeoIECBAgAABAgQIECBAgAABAgQIECgiAQHAIrpsRyVAgAABAgQIECBAgAABAgQIEGh+gXfffTcqKyvjkUceiZqamuQBDjvssOyrgccee2xyj0ICBAgQIECAAAECBAgQIECAAAECBIpLQACwuO7baQkQIECAAAECBAgQIECAAAECBJpZ4He/+10W5PvrX/+avHP79u1j8ODBUVpaGttuu21yn0ICBAgQIECAAAECBAgQIECAAAECBIpLQACwuO7baQkQIECAAAECBAgQIECAAAECBJpRYPHixTF+/PiYMWNGrFmzJnnnvfbaK0aPHh1nnnlmtGnTJrlPIQECBAgQIECAAAECBAgQIECAAAECxSUgAFhc9+20BAgQIECAAAECBAgQIECAAAECzSjw1FNPZV//mzt3br127devX9a3xx571KtPMQECBAgQIECAAAECBAgQIECAAAECxSUgAFhc9+20BAgQIECAAAECBAgQIECAAAECzSSwfPnyuOmmm2LKlCnxww8/JO/atWvX7Onfiy++OOqeAvZHgAABAgQIECBAgAABAgQIECBAgACBvycgAOi3QYAAAQIECBAgQIAAAQIECBAgQKAJBF599dXsK35/+MMf6rV6nz59sr6ePXvWq08xAQIECBAgQIAAAQIECBAgQIAAAQLFJyAAWHx37sQECBAgQIAAAQIECBAgQIAAAQJNLLB27dr4zW9+E2PHjo3PP/88ebctttgirrvuurjqqqti4403Tu5TSIAAAQIECBAgQIAAAQIECBAgQIBAcQoIABbnvTs1AQIECBAgQIAAAQIECBAgQIBAEwq89957UVVVFQ899FCsW7cueacePXpkX/874YQTknsUEiBAgAABAgQIECBAgAABAgQIECBQvAICgMV7905OgAABAgQIECBAgAABAgQIECDQRAKzZs3KgnwLFy5M3qFt27YxYMCAGD16dHTp0iW5TyEBAgQIECBAgAABAgQIECBAgAABAsUrIABYvHfv5AQIECBAgAABAgQIECBAgAABAk0g8Nlnn8WECRPi7rvvjtWrVyfvsPvuu8eoUaPirLPOirowoD8CBAgQIECAAAECBAgQIECAAAECBAj8mIAA4I8J+XcCBAgQIECAAAECBAgQIECAAAEC9RB49tlns6//vfLKK/XoijjjjDOyvr333rtefYoJECBAgAABAgQIECBAgAABAgQIECheAQHA4r17JydAgAABAgQIECBAgAABAgQIEGhkgRUrVsQtt9yS/bdy5crk1bfbbrsYMWJEDBw4MDbaaKPkPoUECBAgQIAAAQIECBAgQIAAAQIECBS3gABgcd+/0xMgQIAAAQIECBAgQIAAAQIECDSiwBtvvBEVFRXx5JNPxvr165NXPuaYY7Kv/x1++OHJPQoJECBAgAABAgQIECBAgAABAgQIECAgAOg3QIAAAQIECBAgQIAAAQIECBAgQKARBGpra2PGjBlRWVkZixcvTl5x0003jauuuiquvfba2HzzzZP7FBIgQIAAAQIECBAgQIAAAQIECBAgQEAA0G+AAAECBAgQIECAAAECBAgQIECAQCMIfPDBBzF27Ni4//77Y926dckrHnjggXH99dfHz3/+82jVqlVyn0ICBAgQIECAAAECBAgQIECAAAECBAgIAPoNECBAgAABAgQIECBAgAABAgQIEGgEgUcffTR7xvedd95JXq0u8Hf++edHeXl5dOvWLblPIQECBAgQIECAAAECBAgQIECAAAECBOoEBAD9DggQIECAAAECBAgQIECAAAECBAhsoMAXX3wREydOjDvvvDOqq6uTV9tll11i1KhRcc4550RJSUlyn0ICBAgQIECAAAECBAgQIECAAAECBAjUCQgA+h0QIECAAAECBAgQIECAAAECBAgQ2ECB559/Pvv630svvVSvlU477bSsb//9969Xn2ICBAgQIECAAAECBAgQIECAAAECBAjUCQgA+h0QIECAAAECBAgQIECAAAECBAgQ2ACB77//PqZMmRI33XRTfP3118krbbPNNjF8+PC49NJLo0OHDsl9CgkQIECAAAECBAgQIECAAAECBAgQIPC/BQQA/RYIECBAgAABAgQIECBAgAABAgQIbIDA/PnzY8yYMTF79uyora1NXqlXr17Z1/+OOuqo5B6FBAgQIECAAAECBAgQIECAAAECBAgQ+O8CAoB+DwQIECBAgAABAgQIECBAgAABAgQ2QOC3v/1tFuT7+OOPk1fp2LFjDBkyJIYNGxadOnVK7lNIgAABAgQIECBAgAABAgQIECBAgACB/y4gAOj3QIAAAQIECBAgQIAAAQIECBAgQKCBAosWLYpx48bFzJkzY82aNcmr7LffflFWVhZ9+/aN1q1bJ/cpJECAAAECBAgQIECAAAECBAgQIECAwH8XEAD0eyBAgAABAgQIECBAgAABAgQIECDQQIE5c+ZkX/+bN29evVbo379/1te9e/d69SkmQIAAAQIECBAgQIAAAQIECBAgQIDAfxcQAPR7IECAAAECBAgQIECAAAECBAgQINAAgaVLl8aNN94Y06ZNi1WrViWv0K1btygtLY0LLrgg2rVrl9ynkAABAgQIECBAgAABAgQIECBAgAABAv+ngACg3wQBAgQIECBAgAABAgQIECBAgACBBgi8/PLL2Vf8nnvuuXp1n3zyyVnfQQcdVK8+xQQIECBAgAABAgQIECBAgAABAgQIEPg/BQQA/SYIECBAgAABAgQIECBAgAABAgQI1FOguro67rjjjhg/fnzUfQkw9a9Tp04xbNiwGDJkSHTs2DG1TR0BAgQIECBAgAABAgQIECBAgAABAgT+RwEBQD8MAgQIECBAgAABAgQIECBAgAABAvUUeP/996OysjIefPDBqKmpSe4+7LDDsq//HXvssck9CgkQIECAAAECBAgQIECAAAECBAgQIPD3BAQA/TYIECBAgAABAgQIECBAgAABAgQI1FPg8ccfj4qKipg/f35yZ/v27WPw4MFRWloa2267bXKfQgIECBAgQIAAAQIECBAgQIAAAQIECPw9AQFAvw0CBAgQIECAAAECBAgQIECAAAEC9RBYsWJF3HjjjXHrrbfGDz/8kNy51157xejRo+PMM8+MNm3aJPcpJECAAAECBAgQIECAAAECBAgQIECAwN8TEAD02yBAgAABAgQIECBAgAABAgQIECBQD4G6r/7VPeM7e/bsenRF9OvXL+vbY4896tWnmAABAgQIECBAgAABAgQIECBAgAABAn9PQADQb4MAAQIECBAgQIAAAQIECBAgQIBAPQT+9V//NQvy/cd//EdyV9euXbOnfy+++OKoewrYHwECBAgQIECAAAECBAgQIECAAAECBBpDQACwMRStQYAAAQIECBAgQIAAAQIECBAgUBQCS5YsiQkTJsT06dNj9erVyWc+5phjstDg4YcfntyjkAABAgQIECBAgAABAgQIECBAgAABAj8mIAD4Y0L+nQABAgQIECBAgAABAgQIECBAgMB/CbzyyitZkO/ZZ59NNtloo43i8ssvz74A2KlTp+Q+hQQIECBAgAABAgQIECBAgAABAgQIEPgxAQHAHxPy7wQIECBAgAABAgQIECBAgAABAgT+S+Dee+/NAoCLFy9ONtlzzz2jrKws+vXrF61bt07uU0iAAAECBAgQIECAAAECBAgQIECAAIEfExAA/DEh/06AAAECBAgQIECAAAECBAgQIEAgIj755JMYO3ZszJgxI9auXZts0rdv3yw0uO+++yb3KCRAgAABAgQIECBAgAABAgQIECBAgECKgABgipIaAgQIECBAgAABAgQIECBAgACBohf44x//GBUVFfGnP/0p2WKrrbaK4cOHx9ChQ6NDhw7JfQoJECBAgAABAgQIECBAgAABAgQIECCQIiAAmKKkhgABAgQIECBAgAABAgQIECBAoKgF1qxZE9OmTYvx48fH0qVLky0OOeSQ7Ot/J554YnKPQgIECBAgQIAAAQIECBAgQIAAAQIECKQKCACmSqkjQIAAAQIECBAgQIAAAQIECBAoWoG//vWvUVlZGb/73e+ipqYm2eG8887LAoA77bRTco9CAgQIECBAgAABAgQIECBAgAABAgQIpAoIAKZKqSNAgAABAgQIECBAgAABAgQIEChagTlz5mRBvnnz5iUbdO3aNUaOHBkDBgyIkpKS5D6FBAgQIECAAAECBAgQIECAAAECBAgQSBUQAEyVUkeAAAECBAgQIECAAAECBAgQIFCUAitXroybb745Jk2aFN9//32ywTHHHJOFBg8//PDkHoUECBAgQIAAAQIECBAgQIAAAQIECBCoj4AAYH201BIgQIAAAQIECBAgQIAAAQIECBSdwNtvvx0VFRXx6KOPJp99o402issvvzxKS0ujU6dOyX0KCRAgQIAAAQIECBAgQIAAAQIECBAgUB8BAcD6aKklQIAAAQIECBAgQIAAAQIECBAoOoGHHnoo+5Lfe++9l3z2PffcM8rKyqJfv37RunXr5D6FBAgQIECAAAECBAgQIECAAAECBAgQqI+AAGB9tNQSIECAAAECBAgQIECAAAECBAgUlcCyZcti/PjxMW3atFi9enXy2fv27ZuFBvfdd9/kHoUECBAgQIAAAQIECBAgQIAAAQIECBCor4AAYH3F1BMgQIAAAQIECBAgQIAAAQIECBSNwPz587Mg3+zZs5PPvNVWW8Xw4cNj6NCh0aFDh+Q+hQQIECBAgAABAgQIECBAgAABAgQIEKivgABgfcXUEyBAgAABAgQIECBAgAABAgQIFI1AXfCvLgBYFwRM/TvkkEOynhNPPDG1RR0BAgQIECBAgAABAgQIECBAgAABAgQaJCAA2CA2TQQIECBAgAABAgQIECBAgAABAsUgUPf0b0VFRSxdujT5uOedd14WANxpp52SexQSIECAAAECBAgQIECAAAECBAgQIECgIQICgA1R00OAAAECBAgQIECAAAECBAgQIFDwAkuWLImqqqqYPn161NTUJJ23S5cuMXLkyLjkkkuipKQkqUcRAQIECBAgQIAAAQIECBAgQIAAAQIEGiogANhQOX0ECBAgQIAAAQIECBAgQIAAAQIFLTBv3rzs6391zwCn/h166KFRXl4exx9/fGqLOgIECBAgQIAAAQIECBAgQIAAAQIECDRYQACwwXQaCRAgQIAAAQIECBAgQIAAAQIEClmgLvhX95Tv/Pnzk4/Zr1+/LAC45557JvcoJECAAAECBAgQIECAAAECBAgQIECAQEMFBAAbKqePAAECBAgQIECAAAECBAgQIECgoAWmTZuWfQFw6dKlSeds3759/PrXv47S0tLo2LFjUo8iAgQIECBAgAABAgQIECBAgAABAgQIbIiAAOCG6OklQIAAAQIECBAgQIAAAQIECBAoSIGvvvoqqqqqYurUqVFTU5N0xm7dumVf/zv//POjVatWST2KCBAgQIAAAQIECBAgQIAAAQIECBAgsCECAoAboqeXAAECBAgQIECAAAECBAgQIECgIAXeeuut7Pnfxx9/PPl8RxxxRNZz9NFHJ/coJECAAAECBAgQIECAAAECBAgQIECAwIYICABuiJ5eAgQIECBAgAABAgQIECBAgACBghSYPXt2FuabP39+8vn69++f9XTv3j25RyEBAgQIECBAgAABAgQIECBAgAABAgQ2REAAcEP09BIgQIAAAQIECBAgQIAAAQIECBSkwLRp06KioiKWLl2adL6OHTvGiBEjYtiwYdG+ffukHkUECBAgQIAAAQIECBAgQIAAAQIECBDYUAEBwA0V1E+AAAECBAgQIECAAAECBAgQIFBQAt98801UVlbG5MmTo6amJulsu+yyS/b1v3POOSepXhEBAgQIECBAgAABAgQIECBAgAABAgQaQ0AAsDEUrUGAAAECBAgQIECAAAECBAgQIFAwAu+++24W5nvkkUeSz9S7d+8oLy+PXr16JfcoJECAAAECBAgQIECAAAECBAgQIECAwIYKCABuqKB+AgQIECBAgAABAgQIECBAgACBghJ44oknsgDgn//85+RzXXTRRVnPDjvskNyjkAABAgQIECBAgAABAgQIECBAgAABAhsqIAC4oYL6CRAgQIAAAQIECBAgQIAAAQIECkpg+vTpWZhv6dKlSefaZJNNYtSoUXHttddGSUlJUo8iAgQIECBAgAABAgQIECBAgAABAgQINIaAAGBjKFqDAAECBAgQIECAAAECBAgQIECgIARWrFgRVVVVccstt0RNTU3SmXbffffs+d+zzjorqV4RAQIECBAgQIAAAQIECBAgQIAAAQIEGktAALCxJK1DgAABAgQIECBAgAABAgQIECCQ9wLvvfde9vW/hx56KPksffr0yXp69uyZ3KOQAAECBAgQIECAAAECBAgQIECAAAECjSEgANgYitYgQIAAAQIECBAgQIAAAQIECBAoCIGnn346C/O9/vrryee59NJLs55tttkmuUchAQIECBAgQIAAAQIECBAgQIAAAQIEGkNAALAxFK1BgAABAgQIECBAgAABAgQIECBQEAJ33nlnFub78ssvk86z+eabx+jRo+Pqq6+ONm3aJPUoIkCAAAECBAgQIECAAAECBAgQIECAQGMJCAA2lqR1CBAgQIAAAQIECBAgQIAAAQIE8lrgu+++i6qqqpg0aVKsW7cu6Sz77LNPFhg8/fTTk+oVESBAgAABAgQIECBAgAABAgQIECBAoDEFBAAbU9NaBAgQIECAAAECBAgQIECAAAECeSvw3nvvZWG+hx56KPkMp512Wtaz//77J/coJECAAAECBAgQIECAAAECBAgQIECAQGMJCAA2lqR1CBAgQIAAAQIECBAgQIAAAQIE8lrgqfAbc2sAACAASURBVKeeysJ8c+fOTT7HlVdeGeXl5bHlllsm9ygkQIAAAQIECBAgQIAAAQIECBAgQIBAYwkIADaWpHUIECBAgAABAgQIECBAgAABAgTyWmD69OlRUVERS5YsSTrHFltsEWVlZXHVVVdF69atk3oUESBAgAABAgQIECBAgAABAgQIECBAoDEFBAAbU9NaBAgQIECAAAECBAgQIECAAAECeSnwzTffRFVVVdx2221RU1OTdIa99947+2LgGWeckVSviAABAgQIECBAgAABAgQIECBAgAABAo0tIADY2KLWI0CAAAECBAgQIECAAAECBAgQyDuBBQsWZGG+hx9+OHn2k046Kes5+OCDk3sUEiBAgAABAgQIECBAgAABAgQIECBAoDEFBAAbU9NaBAgQIECAAAECBAgQIECAAAECeSnw+9//Pgvzvfnmm8nzDxo0KMrLy2O77bZL7lFIgAABAgQIECBAgAABAgQIECBAgACBxhQQAGxMTWsRIECAAAECBAgQIECAAAECBAjkpcDtt98eFRUVsWzZsqT5O3bsGKNGjYphw4ZF27Ztk3oUESBAgAABAgQIECBAgAABAgQIECBAoLEFBAAbW9R6BAgQIECAAAECBAgQIECAAAECeSXw1VdfRWVlZdSFAGtqapJm33XXXbOv//Xv3z+pXhEBAgQIECBAgAABAgQIECBAgAABAgSaQkAAsClUrUmAAAECBAgQIECAAAECBAgQIJA3Am+99Vb2/O/jjz+ePPMxxxyTBQCPOOKI5B6FBAgQIECAAAECBAgQIECAAAECBAgQaGwBAcDGFrUeAQIECBAgQIAAAQIECBAgQIBAXgnMnj07e/533rx5yXOfd955WQBw5513Tu5RSIAAAQIECBAgQIAAAQIECBAgQIAAgcYWEABsbFHrESBAgAABAgQIECBAgAABAgQI5I3A+vXrY+rUqVkAcPny5Ulzl5SUxIgRI2LUqFHRvn37pB5FBAgQIECAAAECBAgQIECAAAECBAgQaAoBAcCmULUmAQIECBAgQIAAAQIECBAgQIBAXgh8+eWXMWbMmLjzzjujtrY2aeaf/vSn2df/LrrooqR6RQQIECBAgAABAgQIECBAgAABAgQIEGgqAQHAppK1LgECBAgQIECAAAECBAgQIECAQM4LvPHGG3HDDTfEk08+mTzroYcemvUcd9xxyT0KCRAgQIAAAQIECBAgQIAAAQIECBAg0BQCAoBNoWpNAgQIECBAgAABAgQIECBAgACBvBB45JFHsjDfu+++mzzvmWeemX0BcK+99kruUUiAAAECBAgQIECAAAECBAgQIECAAIGmEBAAbApVaxIgQIAAAQIECBAgQIAAAQIECOS8wNq1a2Py5MlRVVUV3377bfK8V155ZRYA3HLLLZN7FBIgQIAAAQIECBAgQIAAAQIECBAgQKApBAQAm0LVmgQIECBAgAABAgQIECBAgAABAjkv8Mknn0RlZWX88z//c9TW1ibNu80220RZWVlcdtll0bp166QeRQQIECBAgAABAgQIECBAgAABAgQIEGgqAQHAppK1LgECBAgQIECAAAECBAgQIECAQE4LvPTSS9nzv88//3zynAcccEDWc+qppyb3KCRAgAABAgQIECBAgAABAgQIECBAgEBTCQgANpWsdQkQIECAAAECBAgQIECAAAECBHJa4N57783CfIsXL06e8+STT856DjrooOQehQQIECBAgAABAgQIECBAgAABAgQIEGgqAQHAppK1LgECBAgQIECAAAECBAgQIECAQM4KLFmyJMaOHRt33HFHrF27NnnOgQMHRnl5eWy//fbJPQoJECBAgAABAgQIECBAgAABAgQIECDQVAICgE0la10CBAgQIECAAAECBAgQIECAAIGcFXjttdeioqIinn766eQZt9566xg1alRcdtllUVJSktynkAABAgQIECBAgAABAgQIECBAgAABAk0lIADYVLLWJUCAAAECBAgQIECAAAECBAgQyFmBBx54IHvK94MPPkiesWfPnllPnz59knsUEiBAgAABAgQIECBAgAABAgQIECBAoCkFBACbUtfaBAgQIECAAAECBAgQIECAAAECOSfw9ddfx/jx42PKlCmxevXq5PnOO++87PnfnXfeOblHIQECBAgQIECAAAECBAgQIECAAAECBJpSQACwKXWtTYAAAQIECBAgQIAAAQIECBAgkHMC8+fPz77kN3v27OTZOnfuHKWlpTF48OBo165dcp9CAgQIECBAgAABAgQIECBAgAABAgQINKWAAGBT6lqbAAECBAgQIECAAAECBAgQIEAg5wQefvjhqKioiL/85S/Jsx122GFZaPDYY49N7lFIgAABAgQIECBAgAABAgQIECBAgACBphYQAGxqYesTIECAAAECBAgQIECAAAECBAjkjMB3330XEydOjEmTJsWqVauS57rwwguz53933HHH5B6FBAgQIECAAAECBAgQIECAAAECBAgQaGoBAcCmFrY+AQIECBAgQIAAAQIECBAgQIBAzggsWLAg+/rfrFmzkmfafvvtY+TIkTFw4MAoKSlJ7lNIgAABAgQIECBAgAABAgQIECBAgACBphYQAGxqYesTIECAAAECBAgQIECAAAECBAjkjMCcOXOyp3znzZuXPNORRx6Z9fTu3Tu5RyEBAgQIECBAgAABAgQIECBAgAABAgSaQ0AAsDmU7UGAAAECBAgQIECAAAECBAgQINDiAtXV1TF58uSYMGFCfPPNN8nzDBgwIAsAdunSJblHIQECBAgQIECAAAECBAgQIECAAAECBJpDQACwOZTtQYAAAQIECBAgQIAAAQIECBAg0OICH374YYwZMybuv//+qK2tTZqna9euMXr06Lj44oujbdu2ST2KCBAgQIAAAQIECBAgQIAAAQIECBAg0FwCAoDNJW0fAgQIECBAgAABAgQIECBAgACBFhV45plnoqKiIl599dXkOY4++ugoLy+PumeA/REgQIAAAQIECBAgQIAAAQIECBAgQCDXBAQAc+1GzEOAAAECBAgQIECAAAECBAgQINDoAjU1NXHHHXdEZWVlLFmyJGn91q1bx6BBg+L666+Pzp07J/UoIkCAAAECBAgQIECAAAECBAgQIECAQHMKCAA2p7a9CBAgQIAAAQIECBAgQIAAAQIEWkRg8eLFUVVVFTNmzIi6MGDK34477hhlZWVx/vnne/43BUwNAQIECBAgQIAAAQIECBAgQIAAAQLNLiAA2OzkNiRAgAABAgQIECBAgAABAgQIEGhugeeffz5uuOGGeOmll5K3Pu6447KeQw89NLlHIQECBAgQIECAAAECBAgQIECAAAECBJpTQACwObXtRYAAAQIECBAgQIAAAQIECBAg0OwC69atizvvvDPGjh0bX3zxRdL+JSUlcdlll8WoUaNi6623TupRRIAAAQIECBAgQIAAAQIECBAgQIAAgeYWEABsbnH7ESBAgAABAgQIECBAgAABAgQINKvARx99FJWVlXHfffclP/+78847Z8//nnvuudGmTZtmnddmBAgQIECAAAECBAgQIECAAAECBAgQSBUQAEyVUkeAAAECBAgQIECAAAECBAgQIJCXAr///e+zp3zffPPN5PlPOOGErKdHjx7JPQoJECBAgAABAgQIECBAgAABAgQIECDQ3AICgM0tbj8CBAgQIECAAAECBAgQIECAAIFmE/juu+9i0qRJ2X8rV65M2rd9+/YxdOjQKC0tja222iqpRxEBAgQIECBAgAABAgQIECBAgAABAgRaQkAAsCXU7UmAAAECBAgQIECAAAECBAgQINAsAu+8805UVFTEo48+GuvXr0/ac9ddd82e/+3fv3+0bt06qUcRAQIECBAgQIAAAQIECBAgQIAAAQIEWkJAALAl1O1JgAABAgQIECBAgAABAgQIECDQLAKzZs3KnvJduHBh8n4nnnhi1nPIIYck9ygkQIAAAQIECBAgQIAAAQIECBAgQIBASwgIALaEuj0JECBAgAABAgQIECBAgAABAgSaXGDZsmUxYcKEmDZtWlRXVyftV/f87xVXXBEjRozw/G+SmCICBAgQIECAAAECBAgQIECAAAECBFpSQACwJfXtTYAAAQIECBAgQIAAAQIECBAg0GQCr776avYlvz/84Q/Je3j+N5lKIQECBAgQIECAAAECBAgQIECAAAECOSAgAJgDl2AEAgQIECBAgAABAgQIECBAgACBxhe49957swDg4sWLkxf3/G8ylUICBAgQIECAAAECBAgQIECAAAECBHJAQAAwBy7BCAQIECBAgAABAgQIECBAgAABAo0rUBf6GzduXMyYMSPWrl2btLjnf5OYFBEgQIAAAQIECBAgQIAAAQIECBAgkEMCAoA5dBlGIUCAAAECBAgQIECAAAECBAgQaByBZ599Nvv63yuvvJK8oOd/k6kUEiBAgAABAgQIECBAgAABAgQIECCQIwICgDlyEcYgQIAAAQIECBAgQIAAAQIECBBoHIFVq1bF1KlTY+LEibF8+fLkRU8++eQsNHjQQQcl9ygkQIAAAQIECBAgQIAAAQIECBAgQIBASwoIALakvr0JECBAgAABAgQIECBAgAABAgQaXWDhwoUxZsyYmDVrVtTW1iatv9lmm8W1114b11xzTWyyySZJPYoIECBAgAABAgQIECBAgAABAgQIECDQ0gICgC19A/YnQIAAAQIECBAgQIAAAQIECBBoVIFHHnkk+5Lfu+++m7zuAQccEOXl5XHqqadGq1atkvsUEiBAgAABAgQIECBAgAABAgQIECBAoCUFBABbUt/eBAgQIECAAAECBAgQIECAAAECjSpQ9+Rv3dO/U6ZMierq6uS1zz777Cw0uOuuuyb3KCRAgAABAgQIECBAgAABAgQIECBAgEBLCwgAtvQN2J8AAQIECBAgQIAAAQIECBAgQKDRBObOnZsF+Z566qnkNbfffvsoLS2NgQMHRrt27ZL7FBIgQIAAAQIECBAgQIAAAQIECBAgQKClBQQAW/oG7E+AAAECBAgQIECAAAECBAgQINBoAvfdd18WAPzoo4+S1+zdu3fWc+SRRyb3KCRAgAABAgQIECBAgAABAgQIECBAgEAuCAgA5sItmIEAAQIECBAgQIAAAQIECBAgQGCDBb788ssYN25c3HnnnbFmzZqk9eq++HfZZZfFyJEjY+utt07qUUSAAAECBAgQIECAAAECBAgQIECAAIFcERAAzJWbMAcBAgQIECBAgAABAgQIECBAgMAGCfzpT3/KvuT3b//2b8nr7LHHHlFWVhb9+vWLNm3aJPcpJECAAAECBAgQIECAAAECBAgQIECAQC4ICADmwi2YgQABAgQIECBAgAABAgQIECBAYIMFZsyYkQUAP/nkk+S1+vbtG+Xl5bHffvsl9ygkQIAAAQIECBAgQIAAAQIECBAgQIBArggIAObKTZiDAAECBAgQIECAAAECBAgQIECgwQKffvpp9vzvPffcE2vXrk1aZ4sttohhw4bFVVddFR06dEjqUUSAAAECBAgQIECAAAECBAgQIECAAIFcEhAAzKXbMAsBAgQIECBAgAABAgQIECBAgECDBJ5//vns638vvfRScv8BBxyQ9Zx66qnJPQoJECBAgAABAgQIECBAgAABAgQIECCQSwICgLl0G2YhQIAAAQIECBAgQIAAAQIECBCot0BNTU3cddddUVlZGV988UVyf79+/bIA4B577JHco5AAAQIECBAgQIAAAQIECBAgQIAAAQK5JCAAmEu3YRYCBAgQIECAAAECBAgQIECAAIF6CyxatCiqqqpi5syZsW7duqT+n/zkJzFixIgYMmRItG/fPqlHEQECBAgQIECAAAECBAgQIECAAAECBHJNQAAw127EPAQIECBAgAABAgQIECBAgAABAvUSeOaZZ7Iv+b322mvJfT169Mh6TjjhhOQehQQIECBAgAABAgQIECBAgAABAgQIEMg1AQHAXLsR8xAgQIAAAQIECBAgQIAAAQIECCQLrF69OqZOnRrjx4+P5cuXJ/ede+65WQBw5513Tu5RSIAAAQIECBAgQIAAAQIECBAgQIAAgVwTEADMtRsxDwECBAgQIECAAAECBAgQIECAQLLABx98EJWVlXH//fdHbW1tUl/nzp2jtLQ0Bg8eHO3atUvqUUSAAAECBAgQIECAAAECBAgQIECAAIFcFBAAzMVbMRMBAgQIECBAgAABAgQIECBAgECSwFNPPZV9yW/u3LlJ9XVFhx9+eNZzzDHHJPcoJECAAAECBAgQIECAAAECBAgQIECAQC4KCADm4q2YiQABAgQIECBAgAABAgQIECBA4EcF6p7/nTJlSkyYMKFez/9edNFFWQBwhx12+NE9FBAgQIAAAQIECBAgQIAAAQIECBAgQCCXBQQAc/l2zEaAAAECBAgQIECAAAECBAgQIPB3BRry/G/Xrl1j1KhRcfHFF0dJSQldAgQIECBAgAABAgQIECBAgAABAgQI5LWAAGBeX5/hCRAgQIAAAQIECBAgQIAAAQLFK9CQ53+POuqo7Ot/vXr1Kl44JydAgAABAgQIECBAgAABAgQIECBAoGAEBAAL5iodhAABAgQIECBAgAABAgQIECBQPAINff73kksuifLy8ujSpUvxYDkpAQIECBAgQIAAAQIECBAgQIAAAQIFKyAAWLBX62AECBAgQIAAAQIECBAgQIAAgcIV2JDnfwcMGBBt27YtXBwnI0CAAAECBAgQIECAAAECBAgQIECgaAQEAIvmqh2UAAECBAgQIECAAAECBAgQIFA4Ap7/LZy7dBICBAgQIECAAAECBAgQIECAAAECBBouIADYcDudBAgQIECAAAECBAgQIECAAAECLSDg+d8WQLclAQIECBAgQIAAAQIECBAgQIAAAQI5KSAAmJPXYigCBAgQIECAAAECBAgQIECAAIG/J+D5X78NAgQIECBAgAABAgQIECBAgAABAgQI/C8BAUC/BAIECBAgQIAAAQIECBAgQIAAgbwS8PxvXl2XYQkQIECAAAECBAgQIECAAAECBAgQaEIBAcAmxLU0AQIECBAgQIAAAQIECBAgQIBA4wpUV1fH5MmTY+LEifH1118nL37JJZdEeXl5dOnSJblHIQECBAgQIECAAAECBAgQIECAAAECBHJdQAAw12/IfAQIECBAgAABAgQIECBAgAABAv+vwPvvvx9jxoyJBx98MGpra5NkunbtGqNGjYoBAwZE27Ztk3oUESBAgAABAgQIECBAgAABAgQIECBAIB8EBADz4ZbMSIAAAQIECBAgQIAAAQIECBAgkAnMnj07brjhhpg/f36yyFFHHZX19OrVK7lHIQECBAgQIECAAAECBAgQIECAAAECBPJBQAAwH27JjAQIECBAgAABAgQIECBAgAABArFy5cq46aab4pZbbonvv/8+WcTzv8lUCgkQIECAAAECBAgQIECAAAECBAgQyDMBAcA8uzDjEiBAgAABAgQIECBAgAABAgSKVeDtt9+OioqKePTRR5MJPP+bTKWQAAECBAgQIECAAAECBAgQIECAAIE8FBAAzMNLMzIBAgQIECBAgAABAgQIECBAoBgFZs2alT3lu3DhwuTje/43mUohAQIECBAgQIAAAQIECBAgQIAAAQJ5KCAAmIeXZmQCBAgQIECAAAECBAgQIECAQLEJLF++PCZMmBBTp06N6urq5ON7/jeZSiEBAgQIECBAgAABAgQIECBAgAABAnkoIACYh5dmZAIECBAgQIAAAQIECBAgQIBAsQm88cYb2df/nnzyyeSje/43mUohAQIECBAgQIAAAQIECBAgQIAAAQJ5KiAAmKcXZ2wCBAgQIECAAAECBAgQIECAQDEJ3H///VkA8MMPP0w+tud/k6kUEiBAgAABAgQIECBAgAABAgQIECCQpwICgHl6ccYmQIAAAQIECBAgQIAAAQIECBSLwJdffhnjx4+PO+64I9asWZN8bM//JlMpJECAAAECBAgQIECAAAECBAgQIEAgTwUEAPP04oxNgAABAgQIECBAgAABAgQIECgWgX//93/Pvv73xz/+MfnInv9NplJIgAABAgQIECBAgAABAgQIECBAgEAeCwgA5vHlGZ0AAQIECBAgQIAAAQIECBAgUAwCM2bMiIqKili8eHHycT3/m0ylkAABAgQIECBAgAABAgQIECBAgACBPBYQAMzjyzM6AQIECBAgQIAAAQIECBAgQKDQBT799NMYN25c3HPPPbF27drk43r+N5lKIQECBAgQIECAAAECBAgQIECAAAECeSwgAJjHl2d0AgQIECBAgAABAgQIECBAgEChC7zwwgvZ878vvvhi8lE9/5tMpZAAAQIECBAgQIAAAQIECBAgQIAAgTwXEADM8ws0PgECBAgQIECAAAECBAgQIECgkAXuvvvu7Pnfzz77LPmYnv9NplJIgAABAgQIECBAgAABAgQIECBAgECeCwgA5vkFGp8AAQIECBAgQIAAAQIECBAgUKgCdc//jh07Nnv+d926dcnH9PxvMpVCAgQIECBAgAABAgQIECBAgAABAgTyXEAAMM8v0PgECBAgQIAAAQIECBAgQIAAgUIV8Pxvod6scxEgQIAAAQIECBAgQIAAAQIECBAg0FgCAoCNJWkdAgQIECBAgAABAgQIECBAgACBRhVoyPO/vXv3jhtuuCGOPPLIRp3FYgQIECBAgAABAgQIECBAgAABAgQIEMhFAQHAXLwVMxEgQIAAAQIECBAgQIAAAQIEilygIc//tmnTJgYNGhRlZWXRuXPnIhd0fAIECBAgQIAAAQIECBAgQIAAAQIEikFAALAYbtkZCRAgQIAAAQIECBAgQIAAAQJ5JtCQ53932mmnGD16dJx//vlRFwb0R4AAAQIECBAgQIAAAQIECBAgQIAAgUIXEAAs9Bt2PgIECBAgQIAAAQIECBAgQIBAHgo05Pnf448/Pnv+92c/+1kentjIBAgQIECAAAECBAgQIECAAAECBAgQqL+AAGD9zXQQIECAAAECBAgQIECAAAECBAg0oUBDnv9t3759DBkyJEpLS6NTp05NOJ2lCRAgQIAAAQIECBAgQIAAAQIECBAgkDsCAoC5cxcmIUCAAAECBAgQIECAAAECBAgQiIiGPP+72267RVlZWZx99tnRunVrjgQIECBAgAABAgQIECBAgAABAgQIECgKAQHAorhmhyRAgAABAgQIECBAgAABAgQI5I9AQ57/PeWUU7Lnfw888MD8OahJCRAgQIAAAQIECBAgQIAAAQIECBAgsIECAoAbCKidAAECBAgQIECAAAECBAgQIECg8QQa8vzvxhtvHNdcc038+te/jk033bTxhrESAQIECBAgQIAAAQIECBAgQIAAAQIEclxAADDHL8h4BAgQIECAAAECBAgQIECAAIFiEmjI87977bVXlJeXxz/90z9Fq1ationLWQkQIECAAAECBAgQIECAAAECBAgQKHIBAcAi/wE4PgECBAgQIECAAAECBAgQIEAglwQa8vxv3759s+d/991331w6ilkIECBAgAABAgQIECBAgAABAgQIECDQ5AICgE1ObAMCBAgQIECAAAECBAgQIECAAIEUgYY8/7v55pvHsGHD4uqrr44OHTqkbKOGAAECBAgQIECAAAECBAgQIECAAAECBSMgAFgwV+kgBAgQIECAAAECBAgQIECAAIH8FmjI87/7779/9vW/0047Lb8Pb3oCBAgQIECAAAECBAgQIECAAAECBAg0QEAAsAFoWggQIECAAAECBAgQIECAAAECBBpXoKamJn7zm99EZWVlfP7558mL//KXv8wCgHvuuWdyj0ICBAgQIECAAAECBAgQIECAAAECBAgUioAAYKHcpHMQIECAAAECBAgQIECAAAECBPJYYNGiRVFVVRUzZ86MdevWJZ2kU6dOMXz48Bg6dGhstNFGST2KCBAgQIAAAQIECBAgQIAAAQIECBAgUEgCAoCFdJvOQoAAAQIECBAgQIAAAQIECBDIU4Fnnnkm+5Lfa6+9lnyCgw8+OOs56aSTknsUEiBAgAABAgQIECBAgAABAgQIECBAoJAEBAAL6TadhQABAgQIECBAgAABAgQIECCQhwLV1dUxZcqUmDhxYixfvjz5BP37988CgN27d0/uUUiAAAECBAgQIECAAAECBAgQIECAAIFCEhAALKTbdBYCBAgQIECAAAECBAgQIECAQB4KvP/++zFmzJh48MEHo7a2NukEW2+9dZSWlsbll18e7dq1S+pRRIAAAQIECBAgQIAAAQIECBAgQIAAgUITEAAstBt1HgIECBAgQIAAAQIECBAgQIBAngk8/vjjUVFREfPnz0+evGfPntnX//r06ZPco5AAAQIECBAgQIAAAQIECBAgQIAAAQKFJiAAWGg36jwECBAgQIAAAQIECBAgQIAAgTwSWLFiRdx0001xyy23xA8//JA8+bnnnpsFAHfeeefkHoUECBAgQIAAAQIECBAgQIAAAQIECBAoNAEBwEK7UechQIAAAQIECBAgQIAAAQIECOSRwFtvvZV9/e+xxx5LnnrbbbfNnv+99NJLPf+brKaQAAECBAgQIECAAAECBAgQIECAAIFCFBAALMRbdSYCBAgQIECAAAECBAgQIECAQJ4IPPTQQ9mX/N57773kiQ899NCs57jjjkvuUUiAAAECBAgQIECAAAECBAgQIECAAIFCFBAALMRbdSYCBAgQIECAAAECBAgQIECAQB4IfPXVVzFhwoS4/fbbo7q6Onni888/PwsAduvWLbnn/2Hv7mO1rOs/gH/wCAiEWGIqIhpKKk1gzaSJko+FugXaJAolUHxEmygiHkE4oiCoiSbMlNaDaT60pVuNVgpJloNy02o+4cwmYpqkmHDsnQq5ogAAIABJREFUDPC3+2r9ylly3ff5nq/n3Pfr/oez8Xm4vq/r+vO961JIgAABAgQIECBAgAABAgQIECBAgACBehQQAKzHu+pMBAgQIECAAAECBAgQIECAAIEuILBmzZri878rVqwofbV77bVXNDc3x3nnnRfdu3cv3aeQAAECBAgQIECAAAECBAgQIECAAAEC9SggAFiPd9WZCBAgQIAAAQIECBAgQIAAAQJdQODOO+8s3uT3wgsvlL7aI488sug57rjjSvcoJECAAAECBAgQIECAAAECBAgQIECAQL0KCADW6511LgIECBAgQIAAAQIECBAgQIBAJxZ45ZVXYsGCBXH77bdHW1tb6SudMmVKEQAcNGhQ6R6FBAgQIECAAAECBAgQIECAAAECBAgQqFcBAcB6vbPORYAAAQIECBAgQIAAAQIECBDoxAKrV68ugnyrVq0qfZV77713XHnllXHOOef4/G9pNYUECBAgQIAAAQIECBAgQIAAAQIECNSzgABgPd9dZyNAgAABAgQIECBAgAABAgQIdFKB5cuXFwHAl19+ufQVjh49OubOnRvHHnts6R6FBAgQIECAAAECBAgQIECAAAECBAgQqGcBAcB6vrvORoAAAQIECBAgQIAAAQIECBDohALr16+Pa6+9NiohwK1bt5a+wrPOOqsIAO67776lexQSIECAAAECBAgQIECAAAECBAgQIECgngUEAOv57jobAQIECBAgQIAAAQIECBAgQKATCvzyl78s3v73yCOPlL66ffbZp/j879SpU33+t7SaQgIECBAgQIAAAQIECBAgQIAAAQIE6l1AALDe77DzESBAgAABAgQIECBAgAABAgQ6mcAdd9wRLS0tVX3+9+ijjy7e/lf5148AAQIECBAgQIAAAQIECBAgQIAAAQIE/ikgAOhJIECAAAECBAgQIECAAAECBAgQyCZQy+d/u3XrFmeffXYRABwwYEC2a7WIAAECBAgQIECAAAECBAgQIECAAAECnV1AALCz3yHXR4AAAQIECBAgQIAAAQIECBCoI4FaPv87aNCgmD17dkyZMiV23nnnOtJwFAIECBAgQIAAAQIECBAgQIAAAQIECLRPQACwfX66CRAgQIAAAQIECBAgQIAAAQIEqhCo5fO/J5xwQvH2v1GjRlWxSSkBAgQIECBAgAABAgQIECBAgAABAgTqX0AAsP7vsRMSIECAAAECBAgQIECAAAECBDqFQC2f/+3Ro0dMmzYtmpubo3///p3iHC6CAAECBAgQIECAAAECBAgQIECAAAECnUVAALCz3AnXQYAAAQIECBAgQIAAAQIECBCoc4FaPv974IEHxpw5c2LixInR1NRU50KOR4AAAQIECBAgQIAAAQIECBAgQIAAgeoEBACr81JNgAABAgQIECBAgAABAgQIECBQo0Atn/89+eSTY968eXHYYYfVuFUbAQIECBAgQIAAAQIECBAgQIAAAQIE6ldAALB+762TESBAgAABAgQIECBAgAABAgQ6jUAtn//t3bt3TJ8+PWbOnBm77rprpzmLCyFAgAABAgQIECBAgAABAgQIECBAgEBnERAA7Cx3wnUQIECAAAECBAgQIECAAAECBOpYoJbP/w4dOjTmzp0bp512WnTr1q2OdRyNAAECBAgQIECAAAECBAgQIECAAAECtQkIANbmposAAQIECBAgQIAAAQIECBAgQKAKgVo+/3vKKacUAcDhw4dXsUkpAQIECBAgQIAAAQIECBAgQIAAAQIEGkdAALBx7rWTEiBAgAABAgQIECBAgAABAgQ+FIFaPv/br1+/4tO/lU8A9+rV60O5bksJECBAgAABAgQIECBAgAABAgQIECDQ2QUEADv7HXJ9BAgQIECAAAECBAgQIECAAIEuLrBy5cpoaWmJ1atXlz7JiBEjYt68eTF27NjSPQoJECBAgAABAgQIECBAgAABAgQIECDQaAICgI12x52XAAECBAgQIECAAAECBAgQIJBRYOvWrXHbbbfFNddcE6+++mrpzV/+8peLAODBBx9cukchAQIECBAgQIAAAQIECBAgQIAAAQIEGk1AALDR7rjzEiBAgAABAgQIECBAgAABAgQyCrzwwgsxf/78uPPOO2Pbtm2lNu++++4xa9asuOiii6Jnz56lehQRIECAAAECBAgQIECAAAECBAgQIECgEQUEABvxrjszAQIECBAgQIAAAQIECBAgQCCTwIoVK4rP/65Zs6b0xpEjRxZv/xszZkzpHoUECBAgQIAAAQIECBAgQIAAAQIECBBoRAEBwEa8685MgAABAgQIECBAgAABAgQIEMgg0NraGjfffHMsWrQo3nzzzdIbTz/99CIAeMABB5TuUUiAAAECBAgQIECAAAECBAgQIECAAIFGFBAAbMS77swECBAgQIAAAQIECBAgQIAAgQwCTz/9dFx99dVx3333xfbt20tt3HPPPaO5uTnOO++86NGjR6keRQQIECBAgAABAgQIECBAgAABAgQIEGhUAQHARr3zzk2AAAECBAgQIECAAAECBAgQ6GCBBx98sHiT3xNPPFF606hRo4qe448/vnSPQgIECBAgQIAAAQIECBAgQIAAAQIECDSqgABgo9555yZAgAABAgQIECBAgAABAgQIdKDAW2+9FYsXL46bbroptmzZUnrTlClTigDgoEGDSvcoJECAAAECBAgQIECAAAECBAgQIECAQKMKCAA26p13bgIECBAgQIAAAQIECBAgQIBABwpU3vrX0tISDzzwQOkt++yzT/H537PPPju6d+9euk8hAQIECBAgQIAAAQIECBAgQIAAAQIEGlVAALBR77xzEyBAgAABAgQIECBAgAABAgQ6UOC+++4r3uT39NNPl97yuc99rug5+uijS/coJECAAAECBAgQIECAAAECBAgQIECAQCMLCAA28t13dgIECBAgQIAAAQIECBAgQIBABwhs3Lgxrrvuurj11lvjnXfeKbWhW7duxZv/5s6dGwMGDCjVo4gAAQIECBAgQIAAAQIECBAgQIAAAQKNLiAA2OhPgPMTIECAAAECBAgQIECAAAECBBILrF27tniT34oVK0pPHjRoUMyePTumTJkSO++8c+k+hQQIECBAgAABAgQIECBAgAABAgQIEGhkAQHARr77zk6AAAECBAgQIECAAAECBAgQ6ACB73//+0UA8E9/+lPp6ccff3zRM2rUqNI9CgkQIECAAAECBAgQIECAAAECBAgQINDoAgKAjf4EOD8BAgQIECBAgAABAgQIECBAIKHAyy+/HAsWLIjly5dHW1tbqcndu3eP888/v3gD4B577FGqRxEBAgQIECBAgAABAgQIECBAgAABAgQIRAgAegoIECBAgAABAgQIECBAgAABAgSSCaxcubJ4k9+vfvWr0jMPOOCAmDNnTpx++unR1NRUuk8hAQIECBAgQIAAAQIECBAgQIAAAQIEGl1AALDRnwDnJ0CAAAECBAgQIECAAAECBAgkEqi88W/p0qWxcOHC+Otf/1p66pgxY4rQ4MiRI0v3KCRAgAABAgQIECBAgAABAgQIECBAgAABbwD0DBAgQIAAAQIECBAgQIAAAQIECCQSePbZZ2P+/Plxzz33xLZt20pN7dWrV3z961+Pyy+/PD760Y+W6lFEgAABAgQIECBAgAABAgQIECBAgAABAv8U8AZATwIBAgQIECBAgAABAgQIECBAgEASgQcffLB4k98TTzxRet4hhxwSV111VYwfPz522mmn0n0KCRAgQIAAAQIECBAgQIAAAQIECBAgQEAA0DNAgAABAgQIECBAgAABAgQIECCQQODNN9+MxYsXx5IlS6K1tbX0xLFjxxahwREjRpTuUUiAAAECBAgQIECAAAECBAgQIECAAAEC/xTwBkBPAgECBAgQIECAAAECBAgQIECAQLsFHn/88SLI95Of/KT0rF133TVmzpwZ06dPj969e5fuU0iAAAECBAgQIECAAAECBAgQIECAAAEC/xQQAPQkECBAgAABAgQIECBAgAABAgQItFvgrrvuKgKAzz//fOlZlbf+zZ07N8aNG1e6RyEBAgQIECBAgAABAgQIECBAgAABAgQI/FtAANDTQIAAAQIECBAgQIAAAQIECBAg0C6BV155JRYsWBC33357tLW1lZ41fvz4IjR4yCGHlO5RSIAAAQIECBAgQIAAAQIECBAgQIAAAQL/FhAA9DQQIECAAAECBAgQIECAAAECBAi0S2DVqlXR0tISjzzySOk5/fv3j1mzZsWFF14YPXv2LN2nkAABAgQIECBAgAABAgQIECBAgAABAgT+LSAA6GkgQIAAAQIECBAgQIAAAQIECBCoWaC1tTWWLl0aixYtitdff730nJEjRxZv/xszZkzpHoUECBAgQIAAAQIECBAgQIAAAQIECBAg8F4BAUBPBAECBAgQIECAAAECBAgQIECAQM0Cf/zjH2P+/Pnxox/9KLZv3156zqRJk4oA4Cc+8YnSPQoJECBAgAABAgQIECBAgAABAgQIECBA4L0CAoCeCAIECBAgQIAAAQIECBAgQIAAgZoF7r333iLI98wzz5Sesffee0dzc3Occ8450aNHj9J9CgkQIECAAAECBAgQIECAAAECBAgQIEDgvQICgJ4IAgQIECBAgAABAgQIECBAgACBmgQ2bNgQCxcujDvuuCP+8Y9/lJ4xevToIjR4zDHHlO5RSIAAAQIECBAgQIAAAQIECBAgQIAAAQLvFxAA9FQQIECAAAECBAgQIECAAAECBAjUJPDwww8XQb5HH320dH/ljX/nnntuXHHFFVF5E6AfAQIECBAgQIAAAQIECBAgQIAAAQIECNQuIABYu51OAgQIECBAgAABAgQIECBAgEDDCmzevDluueWWuP766+ONN94o7fCpT30qZs+eHaeddlo0NTWV7lNIgAABAgQIECBAgAABAgQIECBAgAABAu8XEAD0VBAgQIAAAQIECBAgQIAAAQIECFQt8OSTT8bVV18dDzzwQGzfvr10/4QJE4q3Bh500EGlexQSIECAAAECBAgQIECAAAECBAgQIECAwH8XEAD0ZBAgQIAAAQIECBAgQIAAAQIECFQtcPfddxdBvnXr1pXu3W+//YpP/06ePDl69uxZuk8hAQIECBAgQIAAAQIECBAgQIAAAQIECPx3AQFATwYBAgQIECBAgAABAgQIECBAgEBVAi+99FIsXLgwvv3tb0dbW1vp3pNPPrkIDR522GGlexQSIECAAAECBAgQIECAAAECBAgQIECAwP8WEAD0dBAgQIAAAQIECBAgQIAAAQIECFQl8NOf/rQI8v3ud78r3de/f/+YOXNmTJs2LXr37l26TyEBAgQIECBAgAABAgQIECBAgAABAgQI/G8BAUBPBwECBAgQIECAAAECBAgQIECAQGmBv/zlL7F48eL41re+FVu2bCndN3r06Jg7d24ce+yxpXsUEiBAgAABAgQIECBAgAABAgQIECBAgMAHCwgAekIIECBAgAABAgQIECBAgAABAgRKCzz00EPF2/9+/etfl+6pvPGv8ua/yhsAK28C9CNAgAABAgQIECBAgAABAgQIECBAgACBNAICgGkcTSFAgAABAgQIECBAgAABAgQI1L3Axo0b44YbbohvfvObsXnz5tLnHTFiRFx11VUxduzY2GmnnUr3KSRAgAABAgQIECBAgAABAgQIECBAgACBDxYQAPSEECBAgAABAgQIECBAgAABAgQIlBJYvXp18fa/VatWlar/V9GkSZOKz/8OHjy4qj7FBAgQIECAAAECBAgQIECAAAECBAgQIPDBAgKAnhACBAgQIECAAAECBAgQIECAAIEdCrz11ltxyy23xDe+8Y144403dlj/r4IhQ4ZEc3NzTJw4Mbp37166TyEBAgQIECBAgAABAgQIECBAgAABAgQI7FhAAHDHRioIECBAgAABAgQIECBAgAABAg0vsGbNmmhpaYmf/exn8e6775b2OO2004q3Bg4dOrR0j0ICBAgQIECAAAECBAgQIECAAAECBAgQKCcgAFjOSRUBAgQIECBAgAABAgQIECBAoGEFtmzZErfddlssXrw4Xn311dIO+++/f1xxxRXxta99LXr27Fm6TyEBAgQIECBAgAABAgQIECBAgAABAgQIlBMQACznpIoAAQIECBAgQIAAAQIECBAg0LACa9eujfnz58eKFSti27ZtpR3Gjh1bvP1vxIgRpXsUEiBAgAABAgQIECBAgAABAgQIECBAgEB5AQHA8lYqCRAgQIAAAQIECBAgQIAAAQINJ/Dmm2/GrbfeGkuWLImNGzeWPv/AgQPj8ssvj7POOit69epVuk8hAQIECBAgQIAAAQIECBAgQIAAAQIECJQXEAAsb6WSAAECBAgQIECAAAECBAgQINBwAqtXr46WlpZYtWpVvPvuu6XPf+KJJxZv/zv88MNL9ygkQIAAAQIECBAgQIAAAQIECBAgQIAAgeoEBACr81JNgAABAgQIECBAgAABAgQIEGgYgddeey1uvPHGWLZsWbz99tulz73nnnvGzJkz47zzzovevXuX7lNIgAABAgQIECBAgAABAgQIECBAgAABAtUJCABW56WaAAECBAgQIECAAAECBAgQINAwAj//+c+Lt/g99thjVZ35uOOOK/qOPPLIqvoUEyBAgAABAgQIECBAgAABAgQIECBAgEB1AgKA1XmpJkCAAAECBAgQIECAAAECBAg0hMD69evj+uuvj+XLl8eWLVtKn3mPPfaIGTNmxLRp06JPnz6l+xQSIECAAAECBAgQIECAAAECBAgQIECAQPUCAoDVm+kgQIAAAQIECBAgQIAAAQIECNS9wI9//OPiLX6///3vqzrrCSecUPQdccQRVfUpJkCAAAECBAgQIECAAAECBAgQIECAAIHqBQQAqzfTQYAAAQIECBAgQIAAAQIECBCoa4FK6O+6666LSgjwnXfeKX3WfffdNy677LI488wzvf2vtJpCAgQIECBAgAABAgQIECBAgAABAgQI1C4gAFi7nU4CBAgQIECAAAECBAgQIECAQN0JvP7667F06dK49dZbo/J3Nb9x48YVb/8bPnx4NW1qCRAgQIAAAQIECBAgQIAAAQIECBAgQKBGAQHAGuG0ESBAgAABAgQIECBAgAABAgTqUWDFihXR0tISa9eujXfffbf0EQ888MCYNWtWTJw4MXbZZZfSfQoJECBAgAABAgQIECBAgAABAgQIECBAoHYBAcDa7XQSIECAAAECBAgQIECAAAECBOpK4Omnn47FixfHvffeG62traXP1tTUFF/96ldjzpw5MWTIkNJ9CgkQIECAAAECBAgQIECAAAECBAgQIECgfQICgO3z002AAAECBAgQIECAAAECBAgQqAuBTZs2xR133BE33XRTbNiwoaozHXroodHc3Bynnnpq9OjRo6pexQQIECBAgAABAgQIECBAgAABAgQIECBQu4AAYO12OgkQIECAAAECBAgQIECAAAECdSPw8MMPx/z58+PRRx+Nbdu2lT7XRz7ykZg6dWrMmDEj9tlnn9J9CgkQIECAAAECBAgQIECAAAECBAgQIECg/QICgO03NIEAAQIECBAgQIAAAQIECBAg0KUFnn/++bj++uvjrrvuis2bN1d1ltGjRxef/j3mmGOi8ilgPwIECBAgQIAAAQIECBAgQIAAAQIECBDIJyAAmM/aJgIECBAgQIAAAQIECBAgQIBAEoGNGzfGs88+G+vWrYuXXnopevfuHUOGDIlhw4bFfvvtV9WOLVu2xPe+971YvHhxvPjii1X17r///nHppZfG5MmTo/ImQD8CBAgQIECAAAECBAgQIECAAAECBAgQyCsgAJjX2zYCBAgQIECAAAECBAgQIECAQLsE1qxZE7fddlv89re/jbfffjtaW1uLN+9VAniDBw+O008/Pb74xS/GrrvuWmpP5ZO/11xzTVQ+Abx169ZSPZWi7t27x1e+8pW48sor45Of/GTpPoUECBAgQIAAAQIECBAgQIAAAQIECBAgkE5AADCdpUkECBAgQIAAAQIECBAgQIAAgQ4VeOKJJ+LGG2+MBx98MP7+97+/b1ePHj1iwIABcdlll8XZZ59dhPQ+6PfnP/+5mPed73ynCBNW8zv88MOjubk5TjrppB3uqWauWgIECBAgQIAAAQIECBAgQIAAAQIECBAoLyAAWN5KJQECBAgQIECAAAECBAgQIEDgQxN47bXXYsmSJbFs2bLYtGnTB17HCSecEHPnzo1Ro0b9z7p33nkn7rnnnli4cGE899xzVZ2rEjKcPn16nHPOOaXfNFjVAsUECBAgQIAAAQIECBAgQIAAAQIECBAgUEpAALAUkyICBAgQIECAAAECBAgQIECAwIcrsGrVqpg3b16sXr16hxfSt2/fIqA3Y8aMqPz9336VT/9ee+21sXLlymhra9vhzP8sOOWUU4prGTZsWFV9igkQIECAAAECBAgQIECAAAECBAgQIEAgrYAAYFpP0wgQIECAAAECBAgQIECAAAECHSLw3e9+N1paWuLFF18sNf+MM84o3gJ4wAEHvK9+3bp1ccMNN8Tdd99d9ad/K6G/WbNmxamnnho9e/YsdS2KCBAgQIAAAQIECBAgQIAAAQIECBAgQKBjBAQAO8bVVAIECBAgQIAAAQIECBAgQIBAUoHKp3orb90r+7a+z3/+80UA8IgjjnjPdbzxxhuxfPnyuPnmm+Pll1+u6hp33333uPDCC+Oiiy6Kyt9+BAgQIECAAAECBAgQIECAAAECBAgQIPDhCggAfrj+thMgQIAAAQIECBAgQIAAAQIESglU3v5XCQCW/R199NFFALDy73/+VqxYEfPnz4+1a9fGtm3byo4r6k488cS46qqrYuTIkdGtW7eqehUTIECAAAECBAgQIECAAAECBAgQIECAQHoBAcD0piYSIECAAAECBAgQIECAAAECBJILpAgAPvnkk7Fo0aJ44IEHorW1taprPPjgg2PmzJkxYcKE6NWrV1W9igkQIECAAAECBAgQIECAAAECBAgQIECgYwQEADvG1VQCBAgQIECAAAECBAgQIECAQFKB9gYAN2zYEEuWLInbb789Nm3aVNW19e3bN6ZOnRqXXHJJDBw4sKpexQQIECBAgAABAgQIECBAgAABAgQIECDQcQICgB1nazIBAgQIECBAgAABAgQIECBAIJlAewKAbW1tcf/998eCBQviqaeeqvqajjnmmJgzZ06MHj06mpqaqu7XQIAAAQIECBAgQIAAAQIECBAgQIAAAQIdIyAA2DGuphIgQIAAAQIECBAgQIAAAQIEkgq0JwD4m9/8pgj//eIXv4hKGLCa39ChQ2PGjBkxfvz46NOnTzWtagkQIECAAAECBAgQIECAAAECBAgQIECggwUEADsY2HgCBAgQIECAAAECBAgQIECAQAqBWgOAlU/23njjjfGDH/wg3n777aou5eMf/3hMmzYtLrjggujfv39VvYoJECBAgAABAgQIECBAgAABAgQIECBAoOMFBAA73tgGAgQIECBAgAABAgQIECBAgEC7BWoJAFbCe88991wsXbo0NmzYUNU1VD71O27cuOLTv8OGDYtu3bpV1a+YAAECBAgQIECAAAECBAgQIECAAAECBDpeQACw441tIECAAAECBAgQIECAAAECBAi0W6CWAOChhx4aq1evjj/84Q+xffv2qq5h5MiRccUVV8SYMWOiZ8+eVfUqJkCAAAECBAgQIECAAAECBAgQIECAAIE8AgKAeZxtIUCAAAECBAgQIECAAAECBAi0S6DaAOCnP/3pIrj3+OOPR1tbW1W7Bw8eHJdeemmcccYZ0bdv36p6FRMgQIAAAQIECBAgQIAAAQIECBAgQIBAPgEBwHzWNhEgQIAAAQIECBAgQIAAAQIEahaoNgDYp0+fYtfmzZur2tmvX7+YMmVKTJ8+PQYNGlRVr2ICBAgQIECAAAECBAgQIECAAAECBAgQyCsgAJjX2zYCBAgQIECAAAECBAgQIECAQE0C1QYAa1oSEV/4whdizpw58dnPfjaamppqHaOPAAECBAgQIECAAAECBAgQIECAAAECBDIICABmQLaCAAECBAgQIECAAAECBAgQINBegRwBwOHDh8fMmTPjlFNOiV69erX3kvUTIECAAAECBAgQIECAAAECBAgQIECAQAcLCAB2MLDxBAgQIECAAAECBAgQIECAAIEUAh0dABw4cGBcfPHFMXXq1Kh8BtiPAAECBAgQIECAAAECBAgQIECAAAECBDq/gABg579HrpAAAQIECBAgQIAAAQIECBAgEB0ZAOzdu3dMmDChePvfQQcdRJsAAQIECBAgQIAAAQIECBAgQIAAAQIEuoiAAGAXuVEukwABAgQIECBAgAABAgQIEGhsgY4MAB577LFx5ZVXxlFHHRXdu3dvbGinJ0CAAAECBAgQIECAAAECBAgQIECAQBcSEADsQjfLpRIgQIAAAQIECBAgQIAAAQKNK9BRAcDhw4cXb/4bN25cVN4E6EeAAAECBAgQIECAAAECBAgQIECAAAECXUdAALDr3CtXSoAAAQIECBAgQIAAAQIECDSwQEcEAPfff/+4+OKLY/LkydGvX78G1nV0AgQIECBAgAABAgQIECBAgAABAgQIdE0BAcCued9cNQECBAgQIECAAAECBAgQINBgAqkDgLvttlsR/KsEAPfbb78G03RcAgQIECBAgAABAgQIECBAgAABAgQI1IeAAGB93EenIECAAAECBAgQIECAAAECBOpcIHUA8OSTT47Zs2fHZz7zmWhqaqpzPccjQIAAAQIECBAgQIAAAQIECBAgQIBAfQoIANbnfXUqAgQIECBAgAABAgQIECBAoM4EUgYAK6G/WbNmxUknnRS77LJLnUk5DgECBAgKSfEXAAAgAElEQVQQIECAAAECBAgQIECAAAECBBpHQACwce61kxIgQIAAAQIECBAgQIAAAQJdWCBVAHDIkCFxySWXxMSJE6Nv375dWMSlEyBAgAABAgQIECBAgAABAgQIECBAgIAAoGeAAAECBAgQIECAAAECBAgQINAFBFIEAPv37x8XXXRRXHjhhfGxj32sC5zaJRIgQIAAAQIECBAgQIAAAQIECBAgQIDABwkIAHo+CBAgQIAAAQIECBAgQIAAAQJdQKC9AcCdd945zj333Jg9e3bstddeXeDELpEAAQIECBAgQIAAAQIECBAgQIAAAQIEdiQgALgjIf9PgAABAgQIECBAgAABAgQIEOgEAtdee23Mmzcvtm7dWtPVnHnmmUX/vvvuW1O/JgIECBAgQIAAAQIECBAgQIAAAQIECBDofAICgJ3vnrgiAgQIECBAgAABAgQIECBAgMD7BJYtWxaVtwC+9tprVetMmTKlCP8NGjSo6l4NBAgQIECAAAECBAgQIECAAAECBAgQINB5BQQAO++9cWUECBAgQIAAAQIECBAgQIAAgf8XuP/++4sQ31NPPVWVivBfVVyKCRAgQIAAAQIECBAgQIAAAQIECBAg0KUEBAC71O1ysQQIECBAgAABAgQIECBAgECjCjz00EPFGwAfffTRUgQDBw6MSvhv6tSp3vxXSkwRAQIECBAgQIAAAQIECBAgQIAAAQIEup6AAGDXu2eumAABAgQIECBAgAABAgQIEGhAgU2bNsUPf/jDWLJkSTz77LMfKDB48OC44IILYtKkSbHHHns0oJYjEyBAgAABAgQIECBAgAABAgQIECBAoDEEBAAb4z47JQECBAgQIECAAAECBAgQIFAHAn/729/innvuiWXLlsUzzzwT27Zte8+pdtpppxg2bFicf/758aUvfSl23333Oji1IxAgQIAAAQIECBAgQIAAAQIECBAgQIDA/xIQAPRsECBAgAABAgQIECBAgAABAgS6kEAlBLhu3bp47LHHYuXKlbF+/fri6gcMGBCjR4+Oo446Kg455JDYbbfdutCpXCoBAgQIECBAgAABAgQIECBAgAABAgQI1CIgAFiLmh4CBAgQIECAAAECBAgQIECAwIcosH379qh8Evj111+P1tbW4kp69epVvPGvX79+0dTU9CFendUECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQM9YLyQAAB17SURBVIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIE/q9dO6YBAABAGObfNSYWrhqApPcIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCgQEkam26Rgph9wAAAABJRU5ErkJggg==',
                'guess': "test",
                'answer': "diamond"}
        data = json.dumps(data)
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/saveDoodle',
                data=data
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"saved" in response.data)


    def test_viewDoodles(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get(
                '/viewDoodles',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"You have not yet completed any doodles in this class yet!" in response.data)

    def test_convertDoodleImage(self):
        image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACgAAAAQcCAYAAABZf8JlAAAgAElEQVR4XuzdX6iX1bYG4C81KlFJDQ0FM4IVJqVFFlakQoVYkVIhBv0xMhLMQsyKzOValZVlpEWGUaKIhFkUmQgKKShYeiFYhoKJSYkUZiKamnr4TQ7sm8NxstP5/YY+wqZ9MZbz9Rnj8uVbF5w6depU5Q8BAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECAQSuACBcBQ+xKWAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgkAQVAh0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBB95u90AACAASURBVAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEAgooAAYcGkiEyBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABBUA3QIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEAgooAAZcmsgECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQEAB0A0QIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAIGAAgqAAZcmMgECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQUAB0AwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIKCAAmDApYlMgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQUAN0AAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAIKKAAGHBpIhMgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQVAN0CAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAIKKAAGXJrIBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEBAAdANECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgACBgAIKgAGXJjIBAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIEFAAdAMECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCCggAJgwKWJTIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEFADdAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQCCigABhwaSITIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAEFQDdAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQCCigABlyayAQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAQAHQDRAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYACCoABlyYyAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBQAHQDBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgoIACYMCliUyAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBBQA3QABAgQIECBAgAABAgQIECBAgACB80xg+/bt1fr166tt27ZVu3fvrjp37lxdffXV1dChQ6sbb7yx6tat23km4p9LgAABAgQIECBAgAABAgQIECBAIKaAAmDMvUlNgAABAgQIECBAgAABAgQIECBA4L8S+Prrr6t58+ZVO3bsqA4ePFgdOXKk6tixY9W1a9eqe/fu1ciRI6sJEyZU11xzzX/19/shAgQIECBAgAABAgQIECBAgAABAgTKCSgAlrP2EgECBAgQIECAAAECBAgQIECAAIFaBdauXVvNmjWrWrduXXXs2LH/M0uPHj2qp59+upo8eXLV+P/+ECBAgAABAgQIECBAgAABAgQIECDQvAIKgM27G8kIECBAgAABAgQIECBAgAABAgQInDGBnTt3VrNnz66WLFlSHT58+P/9exu/Bri1tbW65557ztj7/iICBAgQIECAAAECBAgQIECAAAECBM68gALgmTf1NxIgQIAAAQIECBAgQIAAAQIECBBoOoGVK1dWM2fOrDZt2nTabJdcckn6CuDzzz/vK4Cn1TJAgAABAgQIECBAgAABAgQIECBAoD4BBcD67L1MgAABAgQIECBAgAABAgQIECBAoJjAggULUgFw7969WW+OHTs2fQVwwIABWfOGCBAgQIAAAQIECBAgQIAAAQIECBAoL6AAWN7ciwQIECBAgAABAgQIECBAgAABAgSKC7z22mupAPjPP/9kvX3HHXekAuBtt92WNW+IAAECBAgQIECAAAECBAgQIECAAIHyAgqA5c29SIAAAQIECBAgQIAAAQIECBAgQKC4QFtbWyoA5v4ZPnx4KgA2/usPAQIECBAgQIAAAQIECBAgQIAAAQLNKaAA2Jx7kYoAAQIECBAgQIAAAQIECBAgQIDAGRVQADyjnP4yAgQIECBAgAABAgQIECBAgAABAk0hoADYFGsQggABAgQIECBAgAABAgQIECBAgMDZFZg1a1b6AuDx48ezHho6dGiav+uuu7LmDREgQIAAAQIECBAgQIAAAQIECBAgUF5AAbC8uRcJECBAgAABAgQIECBAgAABAgQIFBd45513qsZXAA8ePJj19nXXXZcKgGPGjMmaN0SAAAECBAgQIECAAAECBAgQIECAQHkBBcDy5l4kQIAAAQIECBAgQIAAAQIECBAgUFxg/vz5qQC4b9++rLevuuqqqrW1tXr44Yez5g0RIECAAAECBAgQIECAAAECBAgQIFBeQAGwvLkXCRAgQIAAAQIECBAgQIAAAQIECBQXWLRoUSoA7tq1K+vtPn36pALgk08+mTVviAABAgQIECBAgAABAgQIECBAgACB8gIKgOXNvUiAAAECBAgQIECAAAECBAgQIECguMAXX3yRfqXv1q1bs97u0aNHKgBOnjw5a94QAQIECBAgQIAAAQIECBAgQIAAAQLlBRQAy5t7kQABAgQIECBAgAABAgQIECBAgEBxgdWrV6cvAG7YsCHr7c6dO6cC4LRp07LmDREgQIAAAQIECBAgQIAAAQIECBAgUF5AAbC8uRcJECBAgAABAgQIECBAgAABAgQIFBf47rvv0hcAV61alfV2hw4dUgFwxowZWfOGCBAgQIAAAQIECBAgQIAAAQIECBAoL6AAWN7ciwQIECBAgAABAgQIECBAgAABAgSKC2zbti19AXDZsmXZb0+ZMiWVBrt27Zr9MwYJECBAgAABAgQIECBAgAABAgQIECgnoABYztpLBAgQIECAAAECBAgQIECAAAECBGoT2LNnTyoAfvzxx9kZxo8fn74CeMUVV2T/jEECBAgQIECAAAECBAgQIECAAAECBMoJKACWs/YSAQIECBAgQIAAAQIECBAgQIAAgdoE/vzzz/Q1v3nz5mVnGD16dCoADh48OPtnDBIgQIAAAQIECBAgQIAAAQIECBAgUE5AAbCctZcIECBAgAABAgQIECBAgAABAgQI1CZw7Nix9AXAWbNmZWe4/fbbU2lwxIgR2T9jkAABAgQIECBAgAABAgQIECBAgACBcgIKgOWsvUSAAAECBAgQIECAAAECBAgQIECgNoFTp05Vr7/+etXe3l4dPXo0K8e1116bvgB4//33Z80bIkCAAAECBAgQIECAAAECBAgQIECgrIACYFlvrxEgQIAAAQIECBAgQIAAAQIECBCoTaDx638bXwHcv39/VoZ+/fqlLwCOHz8+a94QAQIECBAgQIAAAQIECBAgQIAAAQJlBRQAy3p7jQABAgQIECBAgAABAgQIECBAgEBtAp988kkq9O3ZsycrQ8+ePdP8pEmTsuYNESBAgAABAgQIECBAgAABAgQIECBQVkABsKy31wgQIECAAAECBAgQIECAAAECBAjUJrB8+fL0BcAffvghK0Pnzp3TrwCeNm1a1rwhAgQIECBAgAABAgQIECBAgAABAgTKCigAlvX2GgECBAgQIECAAAECBAgQIECAAIHaBFavXp0KgBs2bMjK0KFDh+rll1+uZsyYUTX+vz8ECBAgQIAAAQIECBAgQIAAAQIECDSXgAJgc+1DGgIECBAgQIAAAQIECBAgQIAAAQJnTWDTpk3pV/quXLky+43G1/8aXwFsfA3QHwIECBAgQIAAAQIECBAgQIAAAQIEmktAAbC59iENAQIECBAgQIAAAQIECBAgQIAAgbMmsGPHjvQFwKVLl2a/MWnSpFQAvOyyy7J/xiABAgQIECBAgAABAgQIECBAgAABAmUEFADLOHuFAAECBAgQIECAAAECBAgQIECAQO0C+/btSwXA+fPnZ2d5/PHHUwGwX79+2T9jkAABAgQIECBAgAABAgQIECBAgACBMgIKgGWcvUKAAAECBAgQIECAAAECBAgQIECgdoG///47FQDfeOON7Czjxo1Lvza4paUl+2cMEiBAgAABAgQIECBAgAABAgQIECBQRkABsIyzVwgQIECAAAECBAgQIECAAAECBAjULnDq1KnqlVdeqdrb26sTJ05k5RkzZkz6AuCgQYOy5g0RIECAAAECBAgQIECAAAECBAgQIFBOQAGwnLWXCBAgQIAAAQIECBAgQIAAAQIECNQu0Pj6X+OLfkePHs3KMnLkyDR/8803Z80bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXeDtt99Ovwb40KFDWVmGDx+evgDY+K8/BAgQIECAAAECBAgQIECAAAECBAg0l4ACYHPtQxoCBAgQIECAAAECBAgQIECAAAECZ1Vg7ty56Yt+Bw4cyHqn8eW/xnzjS4D+ECBAgAABAgQIECBAgAABAgQIECDQXAIKgM21D2kIECBAgAABAgQIECBAgAABAgQInFWBDz74IBX6fv/996x3Bg0alL4AOGbMmKx5QwQIECBAgAABAgQIECBAgAABAgQIlBNQACxn7SUCBAgQIECAAAECBAgQIECAAAECtQssWLAg/Qrg3377LStLS0tLKgyOGzcua94QAQIECBAgQIAAAQIECBAgQIAAAQLlBBQAy1l7iQABAgQIECBAgAABAgQIECBAgEDtAgsXLkwFwN27d2dl6d+/f/oC4GOPPZY1b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaBJUuWpC/67dy5MytL3759UwFwwoQJWfOGCBAgQIAAAQIECBAgQIAAAQIECBAoJ6AAWM7aSwQIECBAgAABAgQIECBAgAABAgRqF/j0009TAXD79u1ZWXr37p0KgBMnTsyaN0SAAAECBAgQIECAAAECBAgQIECAQDkBBcBy1l4iQIAAAQIECBAgQIAAAQIECBAgULvA8uXLUwHwxx9/zMrSs2fPND9p0qSseUMECBAgQIAAAQIECBAgQIAAAQIECJQTUAAsZ+0lAgQIECBAgAABAgQIECBAgAABArULfPnll1VbW1u1ZcuWrCyXXnpp+gLgs88+mzVviAABAgQIECBAFkNdPwAAIABJREFUgAABAgQIECBAgACBcgIKgOWsvUSAAAECBAgQIECAAAECBAgQIECgdoEVK1akAuDmzZuzsnTp0iUVAKdOnZo1b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaBVatWpQLgxo0bs7JcfPHFqQD4wgsvZM0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXWDNmjWpALh+/fqsLJ06dUoFwOnTp2fNGyJAgAABAgQIECBAgAABAgQIECBAoJyAAmA5ay8RIECAAAECBAgQIECAAAECBAgQqF1g7dq11cyZM6t169ZlZbngggtSAbDxP38IECBAgAABAgQIECBAgAABAgQIEGguAQXA5tqHNAQIECBAgAABAgQIECBAgAABAgTOqkCjANj4AmDjv7l/GoVBBcBcLXMECBAgQIAAAQIECBAgQIAAAQIEygkoAJaz9hIBAgQIECBAgAABAgQIECBAgACB2gUUAGtfgQAECBAgQIAAAQIECBAgQIAAAQIEzpiAAuAZo/QXESBAgAABAgQIECBAgAABAgQIEGh+AQXA5t+RhAQIECBAgAABAgQIECBAgAABAgRyBRQAc6XMESBAgAABAgQIECBAgAABAgQIEDgHBBQAz4El+icQIECAAAECBAgQIECAAAECBAgQ+F8BBUCnQIAAAQIECBAgQIAAAQIECBAgQOA8ElAAPI+W7Z9KgAABAgQIECBAgAABAgQIECBwzgsoAJ7zK/YPJECAAAECBAgQIECAAAECBAgQIPAfAQVA10CAAAECBAgQIECAAAECBAgQIEDg3BFQADx3dulfQoAAAQIECBAgQIAAAQIECBAgQOC0AgqApyUyQIAAAQIECBAgQIAAAQIECBAgQCCMgAJgmFUJSoAAAQIECBAgQIAAAQIECBAgQODfCygA/ntDfwMBAgQIECBAgAABAgQIECBAgACBZhFQAGyWTchBgAABAgQIECBAgAABAgQIECBAoICAAmABZE8QIECAAAECBAgQIECAAAECBAgQKCSgAFgI2jMECBAgQIAAAQIECBAgQIAAAQIEmkFAAbAZtiADAQIECBAgQIAAAQIECBAgQIAAgTMjoAB4Zhz9LQQIECBAgAABAgQIECBAgAABAgRCCCgAhliTkAQIECBAgAABAgQIECBAgAABAgSyBBQAs5gMESBAgAABAgQIECBAgAABAgQIEDg3BBQAz409+lcQIECAAAECBAgQIECAAAECBAgQaAgoALoDAgQIECBAgAABAgQIECBAgAABAueRgALgebRs/1QCBAgQIECAAAECBAgQIECAAIFzXkAB8JxfsX8gAQIECBAgQIAAAQIECBAgQIAAgf8IKAC6BgIECBAgQIAAAQIECBAgQIAAAQLnjoAC4LmzS/8SAgQIECBAgAABAgQIECBAgAABAqcVUAA8LZEBAgQIECBAgAABAgQIECBAgAABAmEEFADDrEpQAgQIECBAgAABAgQIECBAgAABAv9eQAHw3xv6GwgQIECAAAECBAgQIECAAAECBAg0i4ACYLNsQg4CBAgQIECAAAECBAgQIECAAAECBQS+/fbbqq2trVq3bl3Wax06dKhaW1urGTNmZM0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXWDNmjXVzJkzqw0bNmRlueiii1IB8MUXX8yaN0SAAAECBAgQIECAAAECBAgQIECAQDkBBcBy1l4iQIAAAQIECBAgQIAAAQIECBAgULvAqlWr0hcAN27cmJWlS5cuqQA4derUrHlDBAgQIECAAAECBAgQIECAAAECBAiUE1AALGftJQIECBAgQIAAAQIECBAgQIAAAQK1C6xYsSIVADdv3pyVpXv37qkA+Mwzz2TNGyJAgAABAgQIECBAgAABAgQIECBAoJyAAmA5ay8RIECAAAECBAgQIECAAAECBAgQqF3gq6++Sr8CeMuWLVlZevXqleYnTpyYNW+IAAECBAgQIECAAAECBAgQIECAAIFyAgqA5ay9RIAAAQIECBAgQIAAAQIECBAgQKB2gc8//zx9AXDr1q1ZWfr27ZsKgE888UTWvCECBAgQIECAAAECBAgQIECAAAECBMoJKACWs/YSAQIECBAgQIAAAQIECBAgQIAAgdoFli1blgp9P/30U1aW/v37p/lHH300a94QAQIECBAgQIAAAQIECBAgQIAAAQLlBBQAy1l7iQABAgQIECBAgAABAgQIECBAgEDtAkuXLk1fANyxY0dWlpaWlqq1tbV66KGHsuYNESBAgAABAgQIECBAgAABAgQIECBQTkABsJy1lwgQIECAAAECBAgQIECAAAECBAjULrB48eJUAPz555+zsgwcODAVAB988MGseUMECBAgQIAAAQIECBAgQIAAAQIECJQTUAAsZ+0lAgQIECBAgAABAgQIECBAgAABArULLFy4MP1K319++SUry+DBg1MBcPTo0VnzhggQIECAAAECBAgQIECAAAECBAgQKCegAFjO2ksECBAgQIAAAQIECBAgQIAAAQIEahf46KOP0hcAf/3116wsQ4YMSYXBUaNGZc0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXeDDDz9Mhb59+/ZlZbnlllvS/J133pk1b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaB999/P30B8I8//sjKMmzYsFQAHD58eNa8IQIECBAgQIAAAQIECBAgQIAAAQIEygkoAJaz9hIBAgQIECBAgAABAgQIECBAgACB2gXmzp2bCn0HDhzIytL48l9ra2t16623Zs0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoXWDOnDmpAHjo0KGsLKNGjUoFwJtuuilr3hABAgQIECBAgAABAgQIECBAgAABAuUEFADLWXuJAAECBAgQIECAAAECBAgQIECAQO0Cb775ZvoVwEeOHMnKct9996UC4PXXX581b4gAAQIECBAgQIAAAQIECBAgQIAAgXICCoDlrL1EgAABAgQIECBAgAABAgQIECBAoHaBWbNmpS8AHj9+PCvLAw88kOYHDhyYNW+IAAECBAgQIECAAAECBAgQIECAAIFyAgqA5ay9RIAAAQIECBAgQIAAAQIECBAgQKB2gfb29vQFwJMnT2ZlGTduXCoAtrS0ZM0bIkCAAAECBAgQIECAAAECBAgQIECgnIACYDlrLxEgQIAAAQIECBAgQIAAAQIECBCoVaDxa38bZb7Zs2dn53jkkUfSz1x55ZXZP2OQAAECBAgQIECAAAECBAgQIECAAIEyAgqAZZy9QoAAAQIECBAgQIAAAQIECBAgQKB2gb1796Yy34IFC7KzTJw4Mf1Mr169sn/GIAECBAgQIECAAAECBAgQIECAAAECZQQUAMs4e4UAAQIECBAgQIAAAQIECBAgQIBA7QLbtm1LZb7PPvssO8tzzz2XfqZz587ZP2OQAAECBAgQIECAAAECBAgQIECAAIEyAgqAZZy9QoAAAQIECBAgQIAAAQIECBAgQKB2gQ0bNlRtbW3V6tWrs7J07NixmjFjRjV9+vSqQ4cOWT9jiAABAgQIECBAgAABAgQIECBAgACBcgIKgOWsvUSAAAECBAgQIECAAAECBAgQIECgVoFvvvkmfc1v8+bNWTm6detWtba2VlOmTMmaN0SAAAECBAgQIECAAAECBAgQIECAQFkBBcCy3l4jQIAAAQIECBAgQIAAAQIECBAgUJvAkiVLUgFw586dWRn69OmT5idMmJA1b4gAAQIECBAgQIAAAQIECBAgQIAAgbICCoBlvb1GgAABAgQIECBAgAABAgQIECBAoDaB9957LxX69u/fn5WhpaUlzY8bNy5r3hABAgQIECBAgAABAgQIECBAgAABAmUFFADLenuNAAECBAgQIECAAAECBAgQIECAQC0CJ0+erF599dWqvb29OnHiRFaGG264IRUA77333qx5QwQIECBAgAABAgQIECBAgAABAgQIlBVQACzr7TUCBAgQIECAAAECBAgQIECAAAECtQj89ddfqcz37rvvZr8/bNiwqrW1tRoxYkT2zxgkQIAAAQIECBAgQIAAAQIECBAgQKCcgAJgOWsvESBAgAABAgQIECBAgAABAgQIEKhNYNeuXVVbW1u1aNGi7Ax33313KgAOGTIk+2cMEiBAgAABAgQIECBAgAABAgQIECBQTkABsJy1lwgQIECAAAECBAgQIECAAAECBAjUJrBp06b0BcCVK1dmZxg7dmwqAA4YMCD7ZwwSIECAAAECBAgQIECAAAECBAgQIFBOQAGwnLWXCBAgQIAAAQIECBAgQIAAAQIECNQm0Cj+Nb4A+P3332dneOqpp1IB8PLLL8/+GYMECBAgQIAAAQIECBAgQIAAAQIECJQTUAAsZ+0lAgQIECBAgAABAgQIECBAgAABArUJLF68OH0BsPGrgHP+dOrUqXrppZfS/y688MKcHzFDgAABAgQIECBAgAABAgQIECBAgEBhAQXAwuCeI0CAAAECBAgQIECAAAECBAgQIFCHwJw5c1IB8NChQ1nP9+7dO803vgLoDwECBAgQIECAAAECBAgQIECAAAECzSmgANice5GKAAECBAgQIECAAAECBAgQIECAwBkTOHz4cNXe3l699dZb1cmTJ7P+3sGDB6df/zt69OiseUMECBAgQIAAAQIECBAgQIAAAQIE/oe9Ow3yujrzhn+xNAjuEhUFIypu4z4uEDfEDbdo0DFEcRcBFdwDNNC2TTebigoIanRwiqgZxXIB4xIzrhkXNOAS0IkLFdRRAVFBpVm6eap/99xPzXM/k9vTTS//5dNVli+4rnOu8zn/l9/6HQLNLyAA2PzmdiRAgAABAgQIECBAgAABAgQIECDQrAKffPJJ9jW/GTNmJO97wgknZD09evRI7lFIgAABAgQIECBAgAABAgQIECBAgEDzCggANq+33QgQIECAAAECBAgQIECAAAECBAg0u8C8efOyMN+cOXOS977wwguzLwDuuOOOyT0KCRAgQIAAAQIECBAgQIAAAQIECBBoXgEBwOb1thsBAgQIECBAgAABAgQIECBAgACBZhd45plnoqKiIl599dXkvUtLS7PQYLt27ZJ7FBIgQIAAAQIECBAgQIAAAQIECBAg0LwCAoDN6203AgQIECBAgAABAgQIECBAgAABAs0ucP/992dhvg8//DBp76222iqrHzp0aFK9IgIECBAgQIAAAQIECBAgQIAAAQIEWkZAALBl3O1KgAABAgQIECBAgAABAgQIECBAoNkEbrvttizQ9+233ybt+Q//8A9Z/ZlnnplUr4gAAQIECBAgQIAAAQIECBAgQIAAgZYREABsGXe7EiBAgAABAgQIECBAgAABAgQIEGgWgZUrV0ZlZWVMmjQpamtrk/Y85phjory8PI444oikekUECBAgQIAAAQIECBAgQIAAAQIECLSMgABgy7jblQABAgQIECBAgAABAgQIECBAgECzCPzlL3+JioqKePjhh5P369+/f/YFwO7duyf3KCRAgAABAgQIECBAgAABAgQIECBAoPkFBACb39yOBAgQIECAAAECBAgQIECAAAECBJpN4PHHH88CgPPnz0/e87rrrsu+ALjJJpsk9ygkQIAAAQIECBAgQIAAAQIECBAgQKD5BQQAm9/cjgQIECBAgAABAgQIECBAgAABAgSaRWDdunVx6623RlVVVaxYsSJpzy233DIL/11xxRXRqlWrpB5FBAgQIECAAAECBAgQIECAAAECBAi0jIAAYMu425UAAQIECBAgQIAAAQIECBAgQIBAkwv87W9/izFjxsS9994b69evT9pv3333zZ7/7du3b1K9IgIECBAgQIAAAQIECBAgQIAAAQIEWk5AALDl7O1MgAABAgQIECBAgAABAgQIECBAoEkFXnjhhez537r/p/6dfPLJ2RcADz744NQWdQQIECBAgAABAgQIECBAgAABAgQItJCAAGALwduWAAECBAgQIECAAAECBAgQIECAQFMLzJw5M/ua36JFi5K3GjBgQNbTpUuX5B6FBAgQIECAAAECBAgQIECAAAECBAi0jIAAYMu425UAAQIECBAgQIAAAQIECBAgQIBAkwp8++23MX78+Lj11ltjzZo1SXttuummMXLkyLj22mujpKQkqUcRAQIECBAgQIAAAQIECBAgQIAAAQItJyAA2HL2diZAgAABAgQIECBAgAABAgQIECDQZAILFy7MvuQ3a9as5D123XXXrOfss89O7lFIgAABAgQIECBAgAABAgQIECBAgEDLCQgAtpy9nQkQIECAAAECBAgQIECAAAECBAg0mcBTTz0VFRUV8frrryfvcdxxx2UBwEMPPTS5RyEBAgQIECBAgAABAgQIECBAgAABAi0nIADYcvZ2JkCAAAECBAgQIECAAAECBAgQINBkAnfddVcWAPz888+T9xg4cGAWANxuu+2SexQSIECAAAECBAgQIECAAAECBAgQINByAgKALWdvZwIECBAgQIAAAQIECBAgQIAAAQJNIrB06dKoqqqK6dOnx7p165L26Ny5c4wePToGDRoUbdu2TepRRIAAAQIECBAgQIAAAQIECBAgQIBAywoIALasv90JECBAgAABAgQIECBAgAABAgQINLrA3Llzsy/51T0DnPr3s5/9LOs5/vjjU1vUESBAgAABAgQIECBAgAABAgQIECDQwgICgC18AbYnQIAAAQIECBAgQIAAAQIECBAg0NgCDzzwQBbm++CDD5KXPvvss6O8vDx222235B6FBAgQIECAAAECBAgQIECAAAECBAi0rIAAYMv6250AAQIECBAgQIAAAQIECBAgQIBAowosX748xo8fH1OnTo3Vq1cnrb355pvHiBEj4uqrr4727dsn9SgiQIAAAQIECBAgQIAAAQIECBAgQKDlBQQAW/4OTECAAAECBAgQIECAAAECBAgQIECg0QT+/Oc/Z1//e+KJJ5LX3GeffbKe008/PblHIQECBAgQIECAAAECBAgQIECAAAECLS8gANjyd2ACAgQIECBAgAABAgQIECBAgAABAo0m8NBDD2Vhvvfeey95zV/84hfZ87/7779/co9CAgQIECBAgAABAgQIECBAgAABAgRaXkAAsOXvwAQECBAgQIAAAQIECBAgQIAAAQIEGkXgm2++iYkTJ8Ztt90W1dXVSWt26NAhrrnmmhg+fHhsuummST2KCBAgQIAAAQIECBAgQIAAAQIECBDIDQEBwNy4B1MQIECAAAECBAgQIECAAAECBAgQ2GCBt99+O/v632OPPZa81m677ZZ9/e+ss86KVq1aJfcpJECAAAECBAgQIECAAAECBAgQIECg5QUEAFv+DkxAgAABAgQIECBAgAABAgQIECBAoFEEHnnkkSwA+O677yavd+KJJ2YBwB49eiT3KCRAgAABAgQIECBAgAABAgQIECBAIDcEBABz4x5MQYAAAQIECBAgQIAAAQIECBAgQGCDBFasWBE33nhj3HLLLbFq1aqktdq2bRuXX355jB49On7yk58k9SgiQIAAAQIECBAgQIAAAQIECBAgQCB3BAQAc+cuTEKAAAECBAgQIECAAAECBAgQIECgwQLvvPNOVFRURN1XAFP/dtxxxygrK4sLLrgg2rRpk9qmjgABAgQIECBAgAABAgQIECBAgACBHBEQAMyRizAGAQIECBAgQIAAAQIECBAgQIAAgQ0RaMjzv0cffXT2/O+RRx65IVvrJUCAAAECBAgQIECAAAECBAgQIECghQQEAFsI3rYECBAgQIAAAQIECBAgQIAAAQIEGkugIc//1u19ySWXZAHALl26NNYo1iFAgAABAgQIECBAgAABAgQIECBAoBkFBACbEdtWBAgQIECAAAECBAgQIECAAAECBJpCoCHP/9aF/kaNGpWFANu2bdsUY1mTAAECBAgQIECAAAECBAgQIECAAIEmFhAAbGJgyxMgQIAAAQIECBAgQIAAAQIECBBoaoGGPP9b9+zvDTfcEL17927q8axPgAABAgQIECBAgAABAgQIECBAgEATCQgANhGsZQkQIECAAAECBAgQIECAAAECBAg0h0BDn/+98MILswDgT3/60+YY0x4ECBAgQIAAAQIECBAgQIAAAQIECDSBgABgE6BakgABAgQIECBAgAABAgQIECBAgEBzCTTk+d/OnTtnz/8OGjQoSkpKmmtU+xAgQIAAAQIECBAgQIAAAQIECBAg0MgCAoCNDGo5AgQIECBAgAABAgQIECBAgAABAs0p0JDnfw877LDs63/HHntsc45qLwIECBAgQIAAAQIECBAgQIAAAQIEGllAALCRQS1HgAABAgQIECBAgAABAgQIECBAoLkE6p7/nThxYtx6662xatWq5G3PO++8LAC40047JfcoJECAAAECBAgQIECAAAECBAgQIEAg9wQEAHPvTkxEgAABAgQIECBAgAABAgQIECBAIEng7bffzoJ8jz32WFJ9XdE222wTI0eOjEsvvTTatWuX3KeQAAECBAgQIECAAAECBAgQIECAAIHcExAAzL07MREBAgQIECBAgAABAgQIECBAgACBJIGHH344CwAuWLAgqb6uqGfPnllPnz59knsUEiBAgAABAgQIECBAgAABAgQIECCQmwICgLl5L6YiQIAAAQIECBAgQIAAAQIECBAg8H8V+Prrr7PnfydPnhzV1dXJWuecc04WANxll12SexQSIECAAAECBAgQIECAAAECBAgQIJCbAgKAuXkvpiJAgAABAgQIECBAgAABAgQIECDwfxWYN29eFuSbM2dOstR2220XpaWlMWjQIM//JqspJECAAAECBAgQIECAAAECBAgQIJC7AgKAuXs3JiNAgAABAgQIECBAgAABAgQIECDwdwUefPDBLAD4/vvvJyv16tUr6znqqKOSexQSIECAAAECBAgQIECAAAECBAgQIJC7AgKAuXs3JiNAgAABAgQIECBAgAABAgQIECDwPwp89dVXMWHChJg6dWqsXr06Salt27YxePDgGDVqVHTu3DmpRxEBAgQIECBAgAABAgQIECBAgAABArktIACY2/djOgIECBAgQIAAAQIECBAgQIAAAQL/P4E33ngj+5Lfk08+mazTvXv3GD16dJxzzjnRpk2b5D6FBAgQIECAAAECBAgQIECAAAECBAjkroAAYO7ejckIECBAgAABAgQIECBAgAABAgQI/I8CDzzwQBYA/OCDD5KFTjnllKznwAMPTO5RSIAAAQIECBAgQIAAAQIECBAgQIBAbgsIAOb2/ZiOAAECBAgQIECAAAECBAgQIECAwP9HYNmyZTF+/PiYNm1a8vO/m222WVx33XVxzTXXxMYbb0yUAAECBAgQIECAAAECBAgQIECAAIECERAALJCLdAwCBAgQIECAAAECBAgQIECAAIHiEHjllVeyL/k9++yzyQfef//9s57TTjstuUchAQIECBAgQIAAAQIECBAgQIAAAQK5LyAAmPt3ZEICBAgQIECAAAECBAgQIECAAAECmUBNTU3cc889UVlZGZ999lmyyq9+9assALj77rsn9ygkQIAAAQIECBAgQIAAAQIECBAgQCD3BQQAc/+OTEiAAAECBAgQIECAAAECBAgQIEAgE/joo4+iqqoq7rvvvli3bl2SyrbbbhulpaUxePDgaN++fVKPIgIECBAgQIAAAQIECBAgQIAAAQIE8kNAADA/7smUBAgQIECAAAECBAgQIECAAAECBGLOnDnZl/zmzZuXrHHEEUdkPUcffXRyj0ICBAgQIECAAAECBAgQIECAAAECBPJDQAAwP+7JlAQIECBAgAABAgQIECBAgAABAkUu8PXXX8eNN94YkydPjlWrViVptG7dOi655JK4/vrrY/vtt0/qUUSAAAECBAgQIECAAAECBAgQIECAQP4ICADmz12ZlAABAgQIECBAgAABAgQIECBAoIgF5s6dm33J76mnnkpW6NatW4wePTrOP//8aNu2bXKfQgIECBAgQIAAAQIECBAgQIAAAQIE8kNAADA/7smUBAgQIECAAAECBAgQIECAAAECRS7wL//yL1kA8G9/+1uyxAknnJD19OjRI7lHIQECBAgQIECAAAECBAgQIECAAAEC+SMgAJg/d2VSAgQIECBAgAABAgQIECBAgACBIhWoC/2NHTs26kKAa9euTVLo2LFjXHnllTFs2LDYYostknoUESBAgAABAgQIECBAgAABAgQIECCQXwICgPl1X6YlQIAAAQIECBAgQIAAAQIECBAoQoG6Z3/rvuRX9wxw6t9ee+0V119/fZx55pnRqlWr1DZ1BAgQIECAAAECBAgQIECAAAECBAjkkYAAYB5dllEJECBAgAABAgQIECBAgAABAgSKT2DFihUxadKkuOWWW+K7775LBjj99NOz0OA+++yT3KOQAAECBAgQIECAAAECBAgQIECAAIH8EhAAzK/7Mi0BAgQIECBAgAABAgQIECBAgECRCcybNy8qKipizpw5sX79+qTTb7XVVjF8+PC44oorYqONNkrqUUSAAAECBAgQIECAAAECBAgQIECAQP4JCADm352ZmAABAgQIECBAgAABAgQIECBAoIgE7rvvvuxLfh999FHyqQ8++OCs56STTkruUUiAAAECBAgQIECAAAECBAgQIECAQP4JCADm352ZmAABAgQIECBAgAABAgQIECBAoEgEPv300xg/fnx2QnBHAAAgAElEQVTcc889sWbNmuRTn3POOVkAcJdddknuUUiAAAECBAgQIECAAAECBAgQIECAQP4JCADm352ZmAABAgQIECBAgAABAgQIECBAoEgEnnvuuSzI9/LLLyefeLvttouRI0fGwIEDo127dsl9CgkQIECAAAECBAgQIECAAAECBAgQyD8BAcD8uzMTEyBAgAABAgQIECBAgAABAgQIFIHA2rVrY/r06TFu3LhYsmRJ8ol79eqVhQaPOuqo5B6FBAgQIECAAAECBAgQIECAAAECBAjkp4AAYH7em6kJECBAgAABAgQIECBAgAABAgQKXOCDDz6IqqqquP/++6OmpibptG3atIlBgwZFWVlZdO7cOalHEQECBAgQIECAAAECBAgQIECAAAEC+SsgAJi/d2dyAgQIECBAgAABAgQIECBAgACBAhZ44oknoqKiIt58883kU+68885Z+O/cc8+NujCgPwIECBAgQIAAAQIECBAgQIAAAQIECltAALCw79fpCBAgQIAAAQIECBAgQIAAAQIE8lDgu+++i0mTJmX/rVy5MvkEJ598cvb870EHHZTco5AAAQIECBAgQIAAAQIECBAgQIAAgfwVEADM37szOQECBAgQIECAAAECBAgQIECAQIEKvPPOO9nX/x599NFYv3590ik322yzuPbaa+Oaa66JTTbZJKlHEQECBAgQIECAAAECBAgQIECAAAEC+S0gAJjf92d6AgQIECBAgAABAgQIECBAgACBAhSYNWtWFgBcsGBB8ukOOOCAKC8vj1NPPTVatWqV3KeQAAECBAgQIECAAAECBAgQIECAAIH8FRAAzN+7MzkBAgQIECBAgAABAgQIECBAgEABCnz11VcxYcKEuP3226O6ujr5hGeffXb2/O+uu+6a3KOQAAECBAgQIECAAAECBAgQIECAAIH8FhAAzO/7Mz0BAgQIECBAgAABAgQIECBAgECBCbz++utZkO/pp59OPtn2228fpaWlMXDgwGjXrl1yn0ICBAgQIECAAAECBAgQIECAAAECBPJbQAAwv+/P9AQIECBAgAABAgQIECBAgAABAgUmMHPmzCwAuGjRouST9e7dO+s58sgjk3sUEiBAgAABAgQIECBAgAABAgQIECCQ/wICgPl/h05AgAABAgQIECBAgAABAgQIECBQIAL/+Z//GePGjYu777471qxZk3Sq9u3bx2WXXZZ9AXDrrbdO6lFEgAABAgQIECBAgAABAgQIECBAgEBhCAgAFsY9OgUBAgQIECBAgAABAgQIECBAgEABCDz//PPZl/xeeuml5NPsscceUVZWFv369Ys2bdok9ykkQIAAAQIECBAgQIAAAQIECBAgQCD/BQQA8/8OnYAAAQIECBAgQIAAAQIECBAgQKAABKqrq2PatGkxYcKEWLZsWfKJ+vbtm4UG99133+QehQQIECBAgAABAgQIECBAgAABAgQIFIaAAGBh3KNTECBAgAABAgQIECBAgAABAgQI5LnAggULorKyMmbNmhW1tbVJp+nUqVMMHz48hgwZEh06dEjqUUSAAAECBAgQIECAAAECBAgQIECAQOEICAAWzl06CQECBAgQIECAAAECBAgQIECAQB4L1AX/6r7kt3DhwuRT9OzZM+vp06dPco9CAgQIECBAgAABAgQIECBAgAABAgQKR0AAsHDu0kkIECBAgAABAgQIECBAgAABAgTyVOCLL77Inv696667ou4p4NS/Cy+8MAsA/vSnP01tUUeAAAECBAgQIECAAAECBAgQIECAQAEJCAAW0GU6CgECBAgQIECAAAECBAgQIECAQH4KvPDCC1mQ78UXX0w+QLdu3WLkyJFxwQUXRElJSXKfQgIECBAgQIAAAQIECBAgQIAAAQIECkdAALBw7tJJCBAgQIAAAQIECBAgQIAAAQIE8lCg7ot/06ZNy74AuGzZsuQTnHjiiVlo8JBDDknuUUiAAAECBAgQIECAAAECBAgQIECAQGEJCAAW1n06DQECBAgQIECAAAECBAgQIECAQJ4JLFiwICorK2PWrFlRW1ubNP1mm20W1157bVxzzTWxySabJPUoIkCAAAECBAgQIECAAAECBAgQIECg8AQEAAvvTp2IAAECBAgQIECAAAECBAgQIEAgjwTqgn91X/JbuHBh8tT/+I//GOXl5fHzn/88WrVqldynkAABAgQIECBAgAABAgQIECBAgACBwhIQACys+3QaAgQIECBAgAABAgQIECBAgACBPBL44osvsqd/77rrrqh7Cjj1r3///llosHv37qkt6ggQIECAAAECBAgQIECAAAECBAgQKEABAcACvFRHIkCAAAECBAgQIECAAAECBAgQyA+B559/PioqKuLFF19MHrhr165RWloaAwYMiHbt2iX3KSRAgAABAgQIECBAgAABAgQIECBAoPAEBAAL706diAABAgQIECBAgAABAgQIECBAIA8Evv/++5gyZUrcfPPNsXz58uSJjz322Ozrf4cddlhyj0ICBAgQIECAAAECBAgQIECAAAECBApTQACwMO/VqQgQIECAAAECBAgQIECAAAECBHJcYP78+TFmzJiYPXt21NbWJk3bsWPHGDp0aAwbNiy22mqrpB5FBAgQIECAAAECBAgQIECAAAECBAgUroAAYOHerZMRIECAAAECBAgQIECAAAECBAjksMDMmTOzL/ktWrQoecq99947rr/++jjjjDOidevWyX0KCRAgQIAAAQIECBAgQIAAAQIECBAoTAEBwMK8V6ciQIAAAQIECBAgQIAAAQIECBDIYYGPP/44xo0bF3UhwLVr1yZP+stf/jILDe65557JPQoJECBAgAABAgQIECBAgAABAgQIEChcAQHAwr1bJyNAgAABAgQIECBAgAABAgQIEMhRgccffzwL8r311lvJE3bu3DlGjBgRgwcPjvbt2yf3KSRAgAABAgQIECBAgAABAgQIECBAoHAFBAAL926djAABAgQIECBAgAABAgQIECBAIAcFvvzyy7jxxhvjjjvuiFWrViVP2KtXrygvL4/evXsn9ygkQIAAAQIECBAgQIAAAQIECBAgQKCwBQQAC/t+nY4AAQIECBAgQIAAAQIECBAgQCDHBF544YXs638vvvhi8mTt2rXLvvw3cuTI2HbbbZP7FBIgQIAAAQIECBAgQIAAAQIECBAgUNgCAoCFfb9OR4AAAQIECBAgQIAAAQIECBAgkEMC33//fUyZMiVuvvnmWL58efJku+++e5SVlcWvfvWraNOmTXKfQgIECBAgQIAAAQIECBAgQIAAAQIECltAALCw79fpCBAgQIAAAQIECBAgQIAAAQIEckhg/vz5MWbMmJg9e3bU1tYmT/aLX/wi+2rgfvvtl9yjkAABAgQIECBAgAABAgQIECBAgACBwhcQACz8O3ZCAgQIECBAgAABAgQIECBAgACBHBH47W9/mwX5Pv744+SJOnXqFMOHD48hQ4ZEhw4dkvsUEiBAgAABAgQIECBAgAABAgQIECBQ+AICgIV/x05IgAABAgQIECBAgAABAgQIECCQAwKLFi2KcePGxcyZM2PNmjXJE/Xs2TMLDfbp0ye5RyEBAgQIECBAgAABAgQIECBAgAABAsUhIABYHPfslAQIECBAgAABAgQIECBAgAABAi0sMGfOnCzIN2/evORJWrVqFRdddFGUl5fHDjvskNynkAABAgQIECBAgAABAgQIECBAgACB4hAQACyOe3ZKAgQIECBAgAABAgQIECBAgACBFhRYunRp3HjjjTFt2rRYtWpV8iQ77bRTjBo1Ks4777woKSlJ7lNIgAABAgQIECBAgAABAgQIECBAgEBxCAgAFsc9OyUBAgQIECBAgAABAgQIECBAgEALCrz88svZ1/+ee+65ek1xyimnZF//O+igg+rVp5gAAQIECBAgQIAAAQIECBAgQIAAgeIQEAAsjnt2SgIECBAgQIAAAQIECBAgQIAAgRYSqK6ujunTp8eECROi7kuAqX+dOnWKYcOGxZAhQ6Jjx46pbeoIECBAgAABAgQIECBAgAABAgQIECgiAQHAIrpsRyVAgAABAgQIECBAgAABAgQIEGh+gXfffTcqKyvjkUceiZqamuQBDjvssOyrgccee2xyj0ICBAgQIECAAAECBAgQIECAAAECBIpLQACwuO7baQkQIECAAAECBAgQIECAAAECBJpZ4He/+10W5PvrX/+avHP79u1j8ODBUVpaGttuu21yn0ICBAgQIECAAAECBAgQIECAAAECBIpLQACwuO7baQkQIECAAAECBAgQIECAAAECBJpRYPHixTF+/PiYMWNGrFmzJnnnvfbaK0aPHh1nnnlmtGnTJrlPIQECBAgQIECAAAECBAgQIECAAAECxSUgAFhc9+20BAgQIECAAAECBAgQIECAAAECzSjw1FNPZV//mzt3br127devX9a3xx571KtPMQECBAgQIECAAAECBAgQIECAAAECxSUgAFhc9+20BAgQIECAAAECBAgQIECAAAECzSSwfPnyuOmmm2LKlCnxww8/JO/atWvX7Onfiy++OOqeAvZHgAABAgQIECBAgAABAgQIECBAgACBvycgAOi3QYAAAQIECBAgQIAAAQIECBAgQKAJBF599dXsK35/+MMf6rV6nz59sr6ePXvWq08xAQIECBAgQIAAAQIECBAgQIAAAQLFJyAAWHx37sQECBAgQIAAAQIECBAgQIAAAQJNLLB27dr4zW9+E2PHjo3PP/88ebctttgirrvuurjqqqti4403Tu5TSIAAAQIECBAgQIAAAQIECBAgQIBAcQoIABbnvTs1AQIECBAgQIAAAQIECBAgQIBAEwq89957UVVVFQ899FCsW7cueacePXpkX/874YQTknsUEiBAgAABAgQIECBAgAABAgQIECBQvAICgMV7905OgAABAgQIECBAgAABAgQIECDQRAKzZs3KgnwLFy5M3qFt27YxYMCAGD16dHTp0iW5TyEBAgQIECBAgAABAgQIECBAgAABAsUrIABYvHfv5AQIECBAgAABAgQIECBAgAABAk0g8Nlnn8WECRPi7rvvjtWrVyfvsPvuu8eoUaPirLPOirowoD8CBAgQIECAAAECBAgQIECAAAECBAj8mIAA4I8J+XcCBAgQIECAAAECBAgQIECAAAEC9RB49tlns6//vfLKK/XoijjjjDOyvr333rtefYoJECBAgAABAgQIECBAgAABAgQIECheAQHA4r17JydAgAABAgQIECBAgAABAgQIEGhkgRUrVsQtt9yS/bdy5crk1bfbbrsYMWJEDBw4MDbaaKPkPoUECBAgQIAAAQIECBAgQIAAAQIECBS3gABgcd+/0xMgQIAAAQIECBAgQIAAAQIECDSiwBtvvBEVFRXx5JNPxvr165NXPuaYY7Kv/x1++OHJPQoJECBAgAABAgQIECBAgAABAgQIECAgAOg3QIAAAQIECBAgQIAAAQIECBAgQKARBGpra2PGjBlRWVkZixcvTl5x0003jauuuiquvfba2HzzzZP7FBIgQIAAAQIECBAgQIAAAQIECBAgQEAA0G+AAAECBAgQIECAAAECBAgQIECAQCMIfPDBBzF27Ni4//77Y926dckrHnjggXH99dfHz3/+82jVqlVyn0ICBAgQIECAAAECBAgQIECAAAECBAgIAPoNECBAgAABAgQIECBAgAABAgQIEGgEgUcffTR7xvedd95JXq0u8Hf++edHeXl5dOvWLblPIQECBAgQIECAAAECBAgQIECAAAECBOoEBAD9DggQIECAAAECBAgQIECAAAECBAhsoMAXX3wREydOjDvvvDOqq6uTV9tll11i1KhRcc4550RJSUlyn0ICBAgQIECAAAECBAgQIECAAAECBAjUCQgA+h0QIECAAAECBAgQIECAAAECBAgQ2ECB559/Pvv630svvVSvlU477bSsb//9969Xn2ICBAgQIECAAAECBAgQIECAAAECBAjUCQgA+h0QIECAAAECBAgQIECAAAECBAgQ2ACB77//PqZMmRI33XRTfP3118krbbPNNjF8+PC49NJLo0OHDsl9CgkQIECAAAECBAgQIECAAAECBAgQIPC/BQQA/RYIECBAgAABAgQIECBAgAABAgQIbIDA/PnzY8yYMTF79uyora1NXqlXr17Z1/+OOuqo5B6FBAgQIECAAAECBAgQIECAAAECBAgQ+O8CAoB+DwQIECBAgAABAgQIECBAgAABAgQ2QOC3v/1tFuT7+OOPk1fp2LFjDBkyJIYNGxadOnVK7lNIgAABAgQIECBAgAABAgQIECBAgACB/y4gAOj3QIAAAQIECBAgQIAAAQIECBAgQKCBAosWLYpx48bFzJkzY82aNcmr7LffflFWVhZ9+/aN1q1bJ/cpJECAAAECBAgQIECAAAECBAgQIECAwH8XEAD0eyBAgAABAgQIECBAgAABAgQIECDQQIE5c+ZkX/+bN29evVbo379/1te9e/d69SkmQIAAAQIECBAgQIAAAQIECBAgQIDAfxcQAPR7IECAAAECBAgQIECAAAECBAgQINAAgaVLl8aNN94Y06ZNi1WrViWv0K1btygtLY0LLrgg2rVrl9ynkAABAgQIECBAgAABAgQIECBAgAABAv+ngACg3wQBAgQIECBAgAABAgQIECBAgACBBgi8/PLL2Vf8nnvuuXp1n3zyyVnfQQcdVK8+xQQIECBAgAABAgQIECBAgAABAgQIEPg/BQQA/SYIECBAgAABAgQIECBAgAABAgQI1FOguro67rjjjhg/fnzUfQkw9a9Tp04xbNiwGDJkSHTs2DG1TR0BAgQIECBAgAABAgQIECBAgAABAgT+RwEBQD8MAgQIECBAgAABAgQIECBAgAABAvUUeP/996OysjIefPDBqKmpSe4+7LDDsq//HXvssck9CgkQIECAAAECBAgQIECAAAECBAgQIPD3BAQA/TYIECBAgAABAgQIECBAgAABAgQI1FPg8ccfj4qKipg/f35yZ/v27WPw4MFRWloa2267bXKfQgIECBAgQIAAAQIECBAgQIAAAQIECPw9AQFAvw0CBAgQIECAAAECBAgQIECAAAEC9RBYsWJF3HjjjXHrrbfGDz/8kNy51157xejRo+PMM8+MNm3aJPcpJECAAAECBAgQIECAAAECBAgQIECAwN8TEAD02yBAgAABAgQIECBAgAABAgQIECBQD4G6r/7VPeM7e/bsenRF9OvXL+vbY4896tWnmAABAgQIECBAgAABAgQIECBAgAABAn9PQADQb4MAAQIECBAgQIAAAQIECBAgQIBAPQT+9V//NQvy/cd//EdyV9euXbOnfy+++OKoewrYHwECBAgQIECAAAECBAgQIECAAAECBBpDQACwMRStQYAAAQIECBAgQIAAAQIECBAgUBQCS5YsiQkTJsT06dNj9erVyWc+5phjstDg4YcfntyjkAABAgQIECBAgAABAgQIECBAgAABAj8mIAD4Y0L+nQABAgQIECBAgAABAgQIECBAgMB/CbzyyitZkO/ZZ59NNtloo43i8ssvz74A2KlTp+Q+hQQIECBAgAABAgQIECBAgAABAgQIEPgxAQHAHxPy7wQIECBAgAABAgQIECBAgAABAgT+S+Dee+/NAoCLFy9ONtlzzz2jrKws+vXrF61bt07uU0iAAAECBAgQIECAAAECBAgQIECAAIEfExAA/DEh/06AAAECBAgQIECAAAECBAgQIEAgIj755JMYO3ZszJgxI9auXZts0rdv3yw0uO+++yb3KCRAgAABAgQIECBAgAABAgQIECBAgECKgABgipIaAgQIECBAgAABAgQIECBAgACBohf44x//GBUVFfGnP/0p2WKrrbaK4cOHx9ChQ6NDhw7JfQoJECBAgAABAgQIECBAgAABAgQIECCQIiAAmKKkhgABAgQIECBAgAABAgQIECBAoKgF1qxZE9OmTYvx48fH0qVLky0OOeSQ7Ot/J554YnKPQgIECBAgQIAAAQIECBAgQIAAAQIECKQKCACmSqkjQIAAAQIECBAgQIAAAQIECBAoWoG//vWvUVlZGb/73e+ipqYm2eG8887LAoA77bRTco9CAgQIECBAgAABAgQIECBAgAABAgQIpAoIAKZKqSNAgAABAgQIECBAgAABAgQIEChagTlz5mRBvnnz5iUbdO3aNUaOHBkDBgyIkpKS5D6FBAgQIECAAAECBAgQIECAAAECBAgQSBUQAEyVUkeAAAECBAgQIECAAAECBAgQIFCUAitXroybb745Jk2aFN9//32ywTHHHJOFBg8//PDkHoUECBAgQIAAAQIECBAgQIAAAQIECBCoj4AAYH201BIgQIAAAQIECBAgQIAAAQIECBSdwNtvvx0VFRXx6KOPJp99o402issvvzxKS0ujU6dOyX0KCRAgQIAAAQIECBAgQIAAAQIECBAgUB8BAcD6aKklQIAAAQIECBAgQIAAAQIECBAoOoGHHnoo+5Lfe++9l3z2PffcM8rKyqJfv37RunXr5D6FBAgQIECAAAECBAgQIECAAAECBAgQqI+AAGB9tNQSIECAAAECBAgQIECAAAECBAgUlcCyZcti/PjxMW3atFi9enXy2fv27ZuFBvfdd9/kHoUECBAgQIAAAQIECBAgQIAAAQIECBCor4AAYH3F1BMgQIAAAQIECBAgQIAAAQIECBSNwPz587Mg3+zZs5PPvNVWW8Xw4cNj6NCh0aFDh+Q+hQQIECBAgAABAgQIECBAgAABAgQIEKivgABgfcXUEyBAgAABAgQIECBAgAABAgQIFI1AXfCvLgBYFwRM/TvkkEOynhNPPDG1RR0BAgQIECBAgAABAgQIECBAgAABAgQaJCAA2CA2TQQIECBAgAABAgQIECBAgAABAsUgUPf0b0VFRSxdujT5uOedd14WANxpp52SexQSIECAAAECBAgQIECAAAECBAgQIECgIQICgA1R00OAAAECBAgQIECAAAECBAgQIFDwAkuWLImqqqqYPn161NTUJJ23S5cuMXLkyLjkkkuipKQkqUcRAQIECBAgQIAAAQIECBAgQIAAAQIEGiogANhQOX0ECBAgQIAAAQIECBAgQIAAAQIFLTBv3rzs6391zwCn/h166KFRXl4exx9/fGqLOgIECBAgQIAAAQIECBAgQIAAAQIECDRYQACwwXQaCRAgQIAAAQIECBAgQIAAAQIEClmgLvhX95Tv/Pnzk4/Zr1+/LAC45557JvcoJECAAAECBAgQIECAAAECBAgQIECAQEMFBAAbKqePAAECBAgQIECAAAECBAgQIECgoAWmTZuWfQFw6dKlSeds3759/PrXv47S0tLo2LFjUo8iAgQIECBAgAABAgQIECBAgAABAgQIbIiAAOCG6OklQIAAAQIECBAgQIAAAQIECBAoSIGvvvoqqqqqYurUqVFTU5N0xm7dumVf/zv//POjVatWST2KCBAgQIAAAQIECBAgQIAAAQIECBAgsCECAoAboqeXAAECBAgQIECAAAECBAgQIECgIAXeeuut7Pnfxx9/PPl8RxxxRNZz9NFHJ/coJECAAAECBAgQIECAAAECBAgQIECAwIYICABuiJ5eAgQIECBAgAABAgQIECBAgACBghSYPXt2FuabP39+8vn69++f9XTv3j25RyEBAgQIECBAgAABAgQIECBAgAABAgQ2REAAcEP09BIgQIAAAQIECBAgQIAAAQIECBSkwLRp06KioiKWLl2adL6OHTvGiBEjYtiwYdG+ffukHkUECBAgQIAAAQIECBAgQIAAAQIECBDYUAEBwA0V1E+AAAECBAgQIECAAAECBAgQIFBQAt98801UVlbG5MmTo6amJulsu+yyS/b1v3POOSepXhEBAgQIECBAgAABAgQIECBAgAABAgQaQ0AAsDEUrUGAAAECBAgQIECAAAECBAgQIFAwAu+++24W5nvkkUeSz9S7d+8oLy+PXr16JfcoJECAAAECBAgQIECAAAECBAgQIECAwIYKCABuqKB+AgQIECBAgAABAgQIECBAgACBghJ44oknsgDgn//85+RzXXTRRVnPDjvskNyjkAABAgQIECBAgAABAgQIECBAgAABAhsqIAC4oYL6CRAgQIAAAQIECBAgQIAAAQIECkpg+vTpWZhv6dKlSefaZJNNYtSoUXHttddGSUlJUo8iAgQIECBAgAABAgQIECBAgAABAgQINIaAAGBjKFqDAAECBAgQIECAAAECBAgQIECgIARWrFgRVVVVccstt0RNTU3SmXbffffs+d+zzjorqV4RAQIECBAgQIAAAQIECBAgQIAAAQIEGktAALCxJK1DgAABAgQIECBAgAABAgQIECCQ9wLvvfde9vW/hx56KPksffr0yXp69uyZ3KOQAAECBAgQIECAAAECBAgQIECAAAECjSEgANgYitYgQIAAAQIECBAgQIAAAQIECBAoCIGnn346C/O9/vrryee59NJLs55tttkmuUchAQIECBAgQIAAAQIECBAgQIAAAQIEGkNAALAxFK1BgAABAgQIECBAgAABAgQIECBQEAJ33nlnFub78ssvk86z+eabx+jRo+Pqq6+ONm3aJPUoIkCAAAECBAgQIECAAAECBAgQIECAQGMJCAA2lqR1CBAgQIAAAQIECBAgQIAAAQIE8lrgu+++i6qqqpg0aVKsW7cu6Sz77LNPFhg8/fTTk+oVESBAgAABAgQIECBAgAABAgQIECBAoDEFBAAbU9NaBAgQIECAAAECBAgQIECAAAECeSvw3nvvZWG+hx56KPkMp512Wtaz//77J/coJECAAAECBAgQIECAAAECBAgQIECAQGMJCAA2lqR1CBAgQIAAAQIECBAgQIAAAQIE8lrgqfAbc2sAACAASURBVKeeysJ8c+fOTT7HlVdeGeXl5bHlllsm9ygkQIAAAQIECBAgQIAAAQIECBAgQIBAYwkIADaWpHUIECBAgAABAgQIECBAgAABAgTyWmD69OlRUVERS5YsSTrHFltsEWVlZXHVVVdF69atk3oUESBAgAABAgQIECBAgAABAgQIECBAoDEFBAAbU9NaBAgQIECAAAECBAgQIECAAAECeSnwzTffRFVVVdx2221RU1OTdIa99947+2LgGWeckVSviAABAgQIECBAgAABAgQIECBAgAABAo0tIADY2KLWI0CAAAECBAgQIECAAAECBAgQyDuBBQsWZGG+hx9+OHn2k046Kes5+OCDk3sUEiBAgAABAgQIECBAgAABAgQIECBAoDEFBAAbU9NaBAgQIECAAAECBAgQIECAAAECeSnw+9//Pgvzvfnmm8nzDxo0KMrLy2O77bZL7lFIgAABAgQIECBAgAABAgQIECBAgACBxhQQAGxMTWsRIECAAAECBAgQIECAAAECBAjkpcDtt98eFRUVsWzZsqT5O3bsGKNGjYphw4ZF27Ztk3oUESBAgAABAgQIECBAgAABAgQIECBAoLEFBAAbW9R6BAgQIECAAAECBAgQIECAAAECeSXw1VdfRWVlZdSFAGtqapJm33XXXbOv//Xv3z+pXhEBAgQIECBAgAABAgQIECBAgAABAgSaQkAAsClUrUmAAAECBAgQIECAAAECBAgQIJA3Am+99Vb2/O/jjz+ePPMxxxyTBQCPOOKI5B6FBAgQIECAAAECBAgQIECAAAECBAgQaGwBAcDGFrUeAQIECBAgQIAAAQIECBAgQIBAXgnMnj07e/533rx5yXOfd955WQBw5513Tu5RSIAAAQIECBAgQIAAAQIECBAgQIAAgcYWEABsbFHrESBAgAABAgQIECBAgAABAgQI5I3A+vXrY+rUqVkAcPny5Ulzl5SUxIgRI2LUqFHRvn37pB5FBAgQIECAAAECBAgQIECAAAECBAgQaAoBAcCmULUmAQIECBAgQIAAAQIECBAgQIBAXgh8+eWXMWbMmLjzzjujtrY2aeaf/vSn2df/LrrooqR6RQQIECBAgAABAgQIECBAgAABAgQIEGgqAQHAppK1LgECBAgQIECAAAECBAgQIECAQM4LvPHGG3HDDTfEk08+mTzroYcemvUcd9xxyT0KCRAgQIAAAQIECBAgQIAAAQIECBAg0BQCAoBNoWpNAgQIECBAgAABAgQIECBAgACBvBB45JFHsjDfu+++mzzvmWeemX0BcK+99kruUUiAAAECBAgQIECAAAECBAgQIECAAIGmEBAAbApVaxIgQIAAAQIECBAgQIAAAQIECOS8wNq1a2Py5MlRVVUV3377bfK8V155ZRYA3HLLLZN7FBIgQIAAAQIECBAgQIAAAQIECBAgQKApBAQAm0LVmgQIECBAgAABAgQIECBAgAABAjkv8Mknn0RlZWX88z//c9TW1ibNu80220RZWVlcdtll0bp166QeRQQIECBAgAABAgQIECBAgAABAgQIEGgqAQHAppK1LgECBAgQIECAAAECBAgQIECAQE4LvPTSS9nzv88//3zynAcccEDWc+qppyb3KCRAgAABAgQIECBAgAABAgQIECBAgEBTCQgANpWsdQkQIECAAAECBAgQIECAAAECBHJa4N57783CfIsXL06e8+STT856DjrooOQehQQIECBAgAABAgQIECBAgAABAgQIEGgqAQHAppK1LgECBAgQIECAAAECBAgQIECAQM4KLFmyJMaOHRt33HFHrF27NnnOgQMHRnl5eWy//fbJPQoJECBAgAABAgQIECBAgAABAgQIECDQVAICgE0la10CBAgQIECAAAECBAgQIECAAIGcFXjttdeioqIinn766eQZt9566xg1alRcdtllUVJSktynkAABAgQIECBAgAABAgQIECBAgAABAk0lIADYVLLWJUCAAAECBAgQIECAAAECBAgQyFmBBx54IHvK94MPPkiesWfPnllPnz59knsUEiBAgAABAgQIECBAgAABAgQIECBAoCkFBACbUtfaBAgQIECAAAECBAgQIECAAAECOSfw9ddfx/jx42PKlCmxevXq5PnOO++87PnfnXfeOblHIQECBAgQIECAAAECBAgQIECAAAECBJpSQACwKXWtTYAAAQIECBAgQIAAAQIECBAgkHMC8+fPz77kN3v27OTZOnfuHKWlpTF48OBo165dcp9CAgQIECBAgAABAgQIECBAgAABAgQINKWAAGBT6lqbAAECBAgQIECAAAECBAgQIEAg5wQefvjhqKioiL/85S/Jsx122GFZaPDYY49N7lFIgAABAgQIECBAgAABAgQIECBAgACBphYQAGxqYesTIECAAAECBAgQIECAAAECBAjkjMB3330XEydOjEmTJsWqVauS57rwwguz53933HHH5B6FBAgQIECAAAECBAgQIECAAAECBAgQaGoBAcCmFrY+AQIECBAgQIAAAQIECBAgQIBAzggsWLAg+/rfrFmzkmfafvvtY+TIkTFw4MAoKSlJ7lNIgAABAgQIECBAgAABAgQIECBAgACBphYQAGxqYesTIECAAAECBAgQIECAAAECBAjkjMCcOXOyp3znzZuXPNORRx6Z9fTu3Tu5RyEBAgQIECBAgAABAgQIECBAgAABAgSaQ0AAsDmU7UGAAAECBAgQIECAAAECBAgQINDiAtXV1TF58uSYMGFCfPPNN8nzDBgwIAsAdunSJblHIQECBAgQIECAAAECBAgQIECAAAECBJpDQACwOZTtQYAAAQIECBAgQIAAAQIECBAg0OICH374YYwZMybuv//+qK2tTZqna9euMXr06Lj44oujbdu2ST2KCBAgQIAAAQIECBAgQIAAAQIECBAg0FwCAoDNJW0fAgQIECBAgAABAgQIECBAgACBFhV45plnoqKiIl599dXkOY4++ugoLy+PumeA/REgQIAAAQIECBAgQIAAAQIECBAgQCDXBAQAc+1GzEOAAAECBAgQIECAAAECBAgQINDoAjU1NXHHHXdEZWVlLFmyJGn91q1bx6BBg+L666+Pzp07J/UoIkCAAAECBAgQIECAAAECBAgQIECAQHMKCAA2p7a9CBAgQIAAAQIECBAgQIAAAQIEWkRg8eLFUVVVFTNmzIi6MGDK34477hhlZWVx/vnne/43BUwNAQIECBAgQIAAAQIECBAgQIAAAQLNLiAA2OzkNiRAgAABAgQIECBAgAABAgQIEGhugeeffz5uuOGGeOmll5K3Pu6447KeQw89NLlHIQECBAgQIECAAAECBAgQIECAAAECBJpTQACwObXtRYAAAQIECBAgQIAAAQIECBAg0OwC69atizvvvDPGjh0bX3zxRdL+JSUlcdlll8WoUaNi6623TupRRIAAAQIECBAgQIAAAQIECBAgQIAAgeYWEABsbnH7ESBAgAABAgQIECBAgAABAgQINKvARx99FJWVlXHfffclP/+78847Z8//nnvuudGmTZtmnddmBAgQIECAAAECBAgQIECAAAECBAgQSBUQAEyVUkeAAAECBAgQIECAAAECBAgQIJCXAr///e+zp3zffPPN5PlPOOGErKdHjx7JPQoJECBAgAABAgQIECBAgAABAgQIECDQ3AICgM0tbj8CBAgQIECAAAECBAgQIECAAIFmE/juu+9i0qRJ2X8rV65M2rd9+/YxdOjQKC0tja222iqpRxEBAgQIECBAgAABAgQIECBAgAABAgRaQkAAsCXU7UmAAAECBAgQIECAAAECBAgQINAsAu+8805UVFTEo48+GuvXr0/ac9ddd82e/+3fv3+0bt06qUcRAQIECBAgQIAAAQIECBAgQIAAAQIEWkJAALAl1O1JgAABAgQIECBAgAABAgQIECDQLAKzZs3KnvJduHBh8n4nnnhi1nPIIYck9ygkQIAAAQIECBAgQIAAAQIECBAgQIBASwgIALaEuj0JECBAgAABAgQIECBAgAABAgSaXGDZsmUxYcKEmDZtWlRXVyftV/f87xVXXBEjRozw/G+SmCICBAgQIECAAAECBAgQIECAAAECBFpSQACwJfXtTYAAAQIECBAgQIAAAQIECBAg0GQCr776avYlvz/84Q/Je3j+N5lKIQECBAgQIECAAAECBAgQIECAAAECOSAgAJgDl2AEAgQIECBAgAABAgQIECBAgACBxhe49957swDg4sWLkxf3/G8ylUICBAgQIECAAAECBAgQIECAAAECBHJAQAAwBy7BCAQIECBAgAABAgQIECBAgAABAo0rUBf6GzduXMyYMSPWrl2btLjnf5OYFBEgQIAAAQIECBAgQIAAAQIECBAgkEMCAoA5dBlGIUCAAAECBAgQIECAAAECBAgQaByBZ599Nvv63yuvvJK8oOd/k6kUEiBAgAABAgQIECBAgAABAgQIECCQIwICgDlyEcYgQIAAAQIECBAgQIAAAQIECBBoHIFVq1bF1KlTY+LEibF8+fLkRU8++eQsNHjQQQcl9ygkQIAAAQIECBAgQIAAAQIECBAgQIBASwoIALakvr0JECBAgAABAgQIECBAgAABAgQaXWDhwoUxZsyYmDVrVtTW1iatv9lmm8W1114b11xzTWyyySZJPYoIECBAgAABAgQIECBAgAABAgQIECDQ0gICgC19A/YnQIAAAQIECBAgQIAAAQIECBBoVIFHHnkk+5Lfu+++m7zuAQccEOXl5XHqqadGq1atkvsUEiBAgAABAgQIECBAgAABAgQIECBAoCUFBABbUt/eBAgQIECAAAECBAgQIECAAAECjSpQ9+Rv3dO/U6ZMierq6uS1zz777Cw0uOuuuyb3KCRAgAABAgQIECBAgAABAgQIECBAgEBLCwgAtvQN2J8AAQIECBAgQIAAAQIECBAgQKDRBObOnZsF+Z566qnkNbfffvsoLS2NgQMHRrt27ZL7FBIgQIAAAQIECBAgQIAAAQIECBAgQKClBQQAW/oG7E+AAAECBAgQIECAAAECBAgQINBoAvfdd18WAPzoo4+S1+zdu3fWc+SRRyb3KCRAgAABAgQIECBAgAABAgQIECBAgEAuCAgA5sItmIEAAQIECBAgQIAAAQIECBAgQGCDBb788ssYN25c3HnnnbFmzZqk9eq++HfZZZfFyJEjY+utt07qUUSAAAECBAgQIECAAAECBAgQIECAAIFcERAAzJWbMAcBAgQIECBAgAABAgQIECBAgMAGCfzpT3/KvuT3b//2b8nr7LHHHlFWVhb9+vWLNm3aJPcpJECAAAECBAgQIECAAAECBAgQIECAQC4ICADmwi2YgQABAgQIECBAgAABAgQIECBAYIMFZsyYkQUAP/nkk+S1+vbtG+Xl5bHffvsl9ygkQIAAAQIECBAgQIAAAQIECBAgQIBArggIAObKTZiDAAECBAgQIECAAAECBAgQIECgwQKffvpp9vzvPffcE2vXrk1aZ4sttohhw4bFVVddFR06dEjqUUSAAAECBAgQIECAAAECBAgQIECAAIFcEhAAzKXbMAsBAgQIECBAgAABAgQIECBAgECDBJ5//vns638vvfRScv8BBxyQ9Zx66qnJPQoJECBAgAABAgQIECBAgAABAgQIECCQSwICgLl0G2YhQIAAAQIECBAgQIAAAQIECBCot0BNTU3cddddUVlZGV988UVyf79+/bIA4B577JHco5AAAQIECBAgQIAAAQIECBAgQIAAAQK5JCAAmEu3YRYCBAgQIECAAAECBAgQIECAAIF6CyxatCiqqqpi5syZsW7duqT+n/zkJzFixIgYMmRItG/fPqlHEQECBAgQIECAAAECBAgQIECAAAECBHJNQAAw127EPAQIECBAgAABAgQIECBAgAABAvUSeOaZZ7Iv+b322mvJfT169Mh6TjjhhOQehQQIECBAgAABAgQIECBAgAABAgQIEMg1AQHAXLsR8xAgQIAAAQIECBAgQIAAAQIECCQLrF69OqZOnRrjx4+P5cuXJ/ede+65WQBw5513Tu5RSIAAAQIECBAgQIAAAQIECBAgQIAAgVwTEADMtRsxDwECBAgQIECAAAECBAgQIECAQLLABx98EJWVlXH//fdHbW1tUl/nzp2jtLQ0Bg8eHO3atUvqUUSAAAECBAgQIECAAAECBAgQIECAAIFcFBAAzMVbMRMBAgQIECBAgAABAgQIECBAgECSwFNPPZV9yW/u3LlJ9XVFhx9+eNZzzDHHJPcoJECAAAECBAgQIECAAAECBAgQIECAQC4KCADm4q2YiQABAgQIECBAgAABAgQIECBA4EcF6p7/nTJlSkyYMKFez/9edNFFWQBwhx12+NE9FBAgQIAAAQIECBAgQIAAAQIECBAgQCCXBQQAc/l2zEaAAAECBAgQIECAAAECBAgQIPB3BRry/G/Xrl1j1KhRcfHFF0dJSQldAgQIECBAgAABAgQIECBAgAABAgQI5LWAAGBeX5/hCRAgQIAAAQIECBAgQIAAAQLFK9CQ53+POuqo7Ot/vXr1Kl44JydAgAABAgQIECBAgAABAgQIECBAoGAEBAAL5iodhAABAgQIECBAgAABAgQIECBQPAINff73kksuifLy8ujSpUvxYDkpAQIECBAgQIAAAQIECBAgQIAAAQIFKyAAWLBX62AECBAgQIAAAQIECBAgQIAAgcIV2JDnfwcMGBBt27YtXBwnI0CAAAECBAgQIECAAAECBAgQIECgaAQEAIvmqh2UAAECBAgQIECAAAECBAgQIFA4Ap7/LZy7dBICBAgQIECAAAECBAgQIECAAAECBBouIADYcDudBAgQIECAAAECBAgQIECAAAECLSDg+d8WQLclAQIECBAgQIAAAQIECBAgQIAAAQI5KSAAmJPXYigCBAgQIECAAAECBAgQIECAAIG/J+D5X78NAgQIECBAgAABAgQIECBAgAABAgQI/C8BAUC/BAIECBAgQIAAAQIECBAgQIAAgbwS8PxvXl2XYQkQIECAAAECBAgQIECAAAECBAgQaEIBAcAmxLU0AQIECBAgQIAAAQIECBAgQIBA4wpUV1fH5MmTY+LEifH1118nL37JJZdEeXl5dOnSJblHIQECBAgQIECAAAECBAgQIECAAAECBHJdQAAw12/IfAQIECBAgAABAgQIECBAgAABAv+vwPvvvx9jxoyJBx98MGpra5NkunbtGqNGjYoBAwZE27Ztk3oUESBAgAABAgQIECBAgAABAgQIECBAIB8EBADz4ZbMSIAAAQIECBAgQIAAAQIECBAgkAnMnj07brjhhpg/f36yyFFHHZX19OrVK7lHIQECBAgQIECAAAECBAgQIECAAAECBPJBQAAwH27JjAQIECBAgAABAgQIECBAgAABArFy5cq46aab4pZbbonvv/8+WcTzv8lUCgkQIECAAAECBAgQIECAAAECBAgQyDMBAcA8uzDjEiBAgAABAgQIECBAgAABAgSKVeDtt9+OioqKePTRR5MJPP+bTKWQAAECBAgQIECAAAECBAgQIECAAIE8FBAAzMNLMzIBAgQIECBAgAABAgQIECBAoBgFZs2alT3lu3DhwuTje/43mUohAQIECBAgQIAAAQIECBAgQIAAAQJ5KCAAmIeXZmQCBAgQIECAAAECBAgQIECAQLEJLF++PCZMmBBTp06N6urq5ON7/jeZSiEBAgQIECBAgAABAgQIECBAgAABAnkoIACYh5dmZAIECBAgQIAAAQIECBAgQIBAsQm88cYb2df/nnzyyeSje/43mUohAQIECBAgQIAAAQIECBAgQIAAAQJ5KiAAmKcXZ2wCBAgQIECAAAECBAgQIECAQDEJ3H///VkA8MMPP0w+tud/k6kUEiBAgAABAgQIECBAgAABAgQIECCQpwICgHl6ccYmQIAAAQIECBAgQIAAAQIECBSLwJdffhnjx4+PO+64I9asWZN8bM//JlMpJECAAAECBAgQIECAAAECBAgQIEAgTwUEAPP04oxNgAABAgQIECBAgAABAgQIECgWgX//93/Pvv73xz/+MfnInv9NplJIgAABAgQIECBAgAABAgQIECBAgEAeCwgA5vHlGZ0AAQIECBAgQIAAAQIECBAgUAwCM2bMiIqKili8eHHycT3/m0ylkAABAgQIECBAgAABAgQIECBAgACBPBYQAMzjyzM6AQIECBAgQIAAAQIECBAgQKDQBT799NMYN25c3HPPPbF27drk43r+N5lKIQECBAgQIECAAAECBAgQIECAAAECeSwgAJjHl2d0AgQIECBAgAABAgQIECBAgEChC7zwwgvZ878vvvhi8lE9/5tMpZAAAQIECBAgQIAAAQIECBAgQIAAgTwXEADM8ws0PgECBAgQIECAAAECBAgQIECgkAXuvvvu7Pnfzz77LPmYnv9NplJIgAABAgQIECBAgAABAgQIECBAgECeCwgA5vkFGp8AAQIECBAgQIAAAQIECBAgUKgCdc//jh07Nnv+d926dcnH9PxvMpVCAgQIECBAgAABAgQIECBAgAABAgTyXEAAMM8v0PgECBAgQIAAAQIECBAgQIAAgUIV8Pxvod6scxEgQIAAAQIECBAgQIAAAQIECBAg0FgCAoCNJWkdAgQIECBAgAABAgQIECBAgACBRhVoyPO/vXv3jhtuuCGOPPLIRp3FYgQIECBAgAABAgQIECBAgAABAgQIEMhFAQHAXLwVMxEgQIAAAQIECBAgQIAAAQIEilygIc//tmnTJgYNGhRlZWXRuXPnIhd0fAIECBAgQIAAAQIECBAgQIAAAQIEikFAALAYbtkZCRAgQIAAAQIECBAgQIAAAQJ5JtCQ53932mmnGD16dJx//vlRFwb0R4AAAQIECBAgQIAAAQIECBAgQIAAgUIXEAAs9Bt2PgIECBAgQIAAAQIECBAgQIBAHgo05Pnf448/Pnv+92c/+1kentjIBAgQIECAAAECBAgQIECAAAECBAgQqL+AAGD9zXQQIECAAAECBAgQIECAAAECBAg0oUBDnv9t3759DBkyJEpLS6NTp05NOJ2lCRAgQIAAAQIECBAgQIAAAQIECBAgkDsCAoC5cxcmIUCAAAECBAgQIECAAAECBAgQiIiGPP+72267RVlZWZx99tnRunVrjgQIECBAgAABAgQIECBAgAABAgQIECgKAQHAorhmhyRAgAABAgQIECBAgAABAgQI5I9AQ57/PeWUU7Lnfw888MD8OahJCRAgQIAAAQIECBAgQIAAAQIECBAgsIECAoAbCKidAAECBAgQIECAAAECBAgQIECg8QQa8vzvxhtvHNdcc038+te/jk033bTxhrESAQIECBAgQIAAAQIECBAgQIAAAQIEclxAADDHL8h4BAgQIECAAAECBAgQIECAAIFiEmjI87977bVXlJeXxz/90z9Fq1ationLWQkQIECAAAECBAgQIECAAAECBAgQKHIBAcAi/wE4PgECBAgQIECAAAECBAgQIEAglwQa8vxv3759s+d/991331w6ilkIECBAgAABAgQIECBAgAABAgQIECDQ5AICgE1ObAMCBAgQIECAAAECBAgQIECAAIEUgYY8/7v55pvHsGHD4uqrr44OHTqkbKOGAAECBAgQIECAAAECBAgQIECAAAECBSMgAFgwV+kgBAgQIECAAAECBAgQIECAAIH8FmjI87/7779/9vW/0047Lb8Pb3oCBAgQIECAAAECBAgQIECAAAECBAg0QEAAsAFoWggQIECAAAECBAgQIECAAAECBBpXoKamJn7zm99EZWVlfP7558mL//KXv8wCgHvuuWdyj0ICBAgQIECAAAECBAgQIECAAAECBAgUioAAYKHcpHMQIECAAAECBAgQIECAAAECBPJYYNGiRVFVVRUzZ86MdevWJZ2kU6dOMXz48Bg6dGhstNFGST2KCBAgQIAAAQIECBAgQIAAAQIECBAgUEgCAoCFdJvOQoAAAQIECBAgQIAAAQIECBDIU4Fnnnkm+5Lfa6+9lnyCgw8+OOs56aSTknsUEiBAgAABAgQIECBAgAABAgQIECBAoJAEBAAL6TadhQABAgQIECBAgAABAgQIECCQhwLV1dUxZcqUmDhxYixfvjz5BP37988CgN27d0/uUUiAAAECBAgQIECAAAECBAgQIECAAIFCEhAALKTbdBYCBAgQIECAAAECBAgQIECAQB4KvP/++zFmzJh48MEHo7a2NukEW2+9dZSWlsbll18e7dq1S+pRRIAAAQIECBAgQIAAAQIECBAgQIAAgUITEAAstBt1HgIECBAgQIAAAQIECBAgQIBAngk8/vjjUVFREfPnz0+evGfPntnX//r06ZPco5AAAQIECBAgQIAAAQIECBAgQIAAAQKFJiAAWGg36jwECBAgQIAAAQIECBAgQIAAgTwSWLFiRdx0001xyy23xA8//JA8+bnnnpsFAHfeeefkHoUECBAgQIAAAQIECBAgQIAAAQIECBAoNAEBwEK7UechQIAAAQIECBAgQIAAAQIECOSRwFtvvZV9/e+xxx5LnnrbbbfNnv+99NJLPf+brKaQAAECBAgQIECAAAECBAgQIECAAIFCFBAALMRbdSYCBAgQIECAAAECBAgQIECAQJ4IPPTQQ9mX/N57773kiQ899NCs57jjjkvuUUiAAAECBAgQIECAAAECBAgQIECAAIFCFBAALMRbdSYCBAgQIECAAAECBAgQIECAQB4IfPXVVzFhwoS4/fbbo7q6Onni888/PwsAduvWLbnn/2Hv7mO1rOs/gH/wCAiEWGIqIhpKKk1gzaSJko+FugXaJAolUHxEmygiHkE4oiCoiSbMlNaDaT60pVuNVgpJloNy02o+4cwmYpqkmHDsnQq5ogAAIABJREFUDPC3+2r9ylly3ff5nq/n3Pfr/oez8Xm4vq/r+vO961JIgAABAgQIECBAgAABAgQIECBAgACBehQQAKzHu+pMBAgQIECAAAECBAgQIECAAIEuILBmzZri878rVqwofbV77bVXNDc3x3nnnRfdu3cv3aeQAAECBAgQIECAAAECBAgQIECAAAEC9SggAFiPd9WZCBAgQIAAAQIECBAgQIAAAQJdQODOO+8s3uT3wgsvlL7aI488sug57rjjSvcoJECAAAECBAgQIECAAAECBAgQIECAQL0KCADW6511LgIECBAgQIAAAQIECBAgQIBAJxZ45ZVXYsGCBXH77bdHW1tb6SudMmVKEQAcNGhQ6R6FBAgQIECAAAECBAgQIECAAAECBAgQqFcBAcB6vbPORYAAAQIECBAgQIAAAQIECBDoxAKrV68ugnyrVq0qfZV77713XHnllXHOOef4/G9pNYUECBAgQIAAAQIECBAgQIAAAQIECNSzgABgPd9dZyNAgAABAgQIECBAgAABAgQIdFKB5cuXFwHAl19+ufQVjh49OubOnRvHHnts6R6FBAgQIECAAAECBAgQIECAAAECBAgQqGcBAcB6vrvORoAAAQIECBAgQIAAAQIECBDohALr16+Pa6+9NiohwK1bt5a+wrPOOqsIAO67776lexQSIECAAAECBAgQIECAAAECBAgQIECgngUEAOv57jobAQIECBAgQIAAAQIECBAgQKATCvzyl78s3v73yCOPlL66ffbZp/j879SpU33+t7SaQgIECBAgQIAAAQIECBAgQIAAAQIE6l1AALDe77DzESBAgAABAgQIECBAgAABAgQ6mcAdd9wRLS0tVX3+9+ijjy7e/lf5148AAQIECBAgQIAAAQIECBAgQIAAAQIE/ikgAOhJIECAAAECBAgQIECAAAECBAgQyCZQy+d/u3XrFmeffXYRABwwYEC2a7WIAAECBAgQIECAAAECBAgQIECAAAECnV1AALCz3yHXR4AAAQIECBAgQIAAAQIECBCoI4FaPv87aNCgmD17dkyZMiV23nnnOtJwFAIECBAgQIAAAQIECBAgQIAAAQIECLRPQACwfX66CRAgQIAAAQIECBAgQIAAAQIEqhCo5fO/J5xwQvH2v1GjRlWxSSkBAgQIECBAgAABAgQIECBAgAABAgTqX0AAsP7vsRMSIECAAAECBAgQIECAAAECBDqFQC2f/+3Ro0dMmzYtmpubo3///p3iHC6CAAECBAgQIECAAAECBAgQIECAAAECnUVAALCz3AnXQYAAAQIECBAgQIAAAQIECBCoc4FaPv974IEHxpw5c2LixInR1NRU50KOR4AAAQIECBAgQIAAAQIECBAgQIAAgeoEBACr81JNgAABAgQIECBAgAABAgQIECBQo0Atn/89+eSTY968eXHYYYfVuFUbAQIECBAgQIAAAQIECBAgQIAAAQIE6ldAALB+762TESBAgAABAgQIECBAgAABAgQ6jUAtn//t3bt3TJ8+PWbOnBm77rprpzmLCyFAgAABAgQIECBAgAABAgQIECBAgEBnERAA7Cx3wnUQIECAAAECBAgQIECAAAECBOpYoJbP/w4dOjTmzp0bp512WnTr1q2OdRyNAAECBAgQIECAAAECBAgQIECAAAECtQkIANbmposAAQIECBAgQIAAAQIECBAgQKAKgVo+/3vKKacUAcDhw4dXsUkpAQIECBAgQIAAAQIECBAgQIAAAQIEGkdAALBx7rWTEiBAgAABAgQIECBAgAABAgQ+FIFaPv/br1+/4tO/lU8A9+rV60O5bksJECBAgAABAgQIECBAgAABAgQIECDQ2QUEADv7HXJ9BAgQIECAAAECBAgQIECAAIEuLrBy5cpoaWmJ1atXlz7JiBEjYt68eTF27NjSPQoJECBAgAABAgQIECBAgAABAgQIECDQaAICgI12x52XAAECBAgQIECAAAECBAgQIJBRYOvWrXHbbbfFNddcE6+++mrpzV/+8peLAODBBx9cukchAQIECBAgQIAAAQIECBAgQIAAAQIEGk1AALDR7rjzEiBAgAABAgQIECBAgAABAgQyCrzwwgsxf/78uPPOO2Pbtm2lNu++++4xa9asuOiii6Jnz56lehQRIECAAAECBAgQIECAAAECBAgQIECgEQUEABvxrjszAQIECBAgQIAAAQIECBAgQCCTwIoVK4rP/65Zs6b0xpEjRxZv/xszZkzpHoUECBAgQIAAAQIECBAgQIAAAQIECBBoRAEBwEa8685MgAABAgQIECBAgAABAgQIEMgg0NraGjfffHMsWrQo3nzzzdIbTz/99CIAeMABB5TuUUiAAAECBAgQIECAAAECBAgQIECAAIFGFBAAbMS77swECBAgQIAAAQIECBAgQIAAgQwCTz/9dFx99dVx3333xfbt20tt3HPPPaO5uTnOO++86NGjR6keRQQIECBAgAABAgQIECBAgAABAgQIEGhUAQHARr3zzk2AAAECBAgQIECAAAECBAgQ6GCBBx98sHiT3xNPPFF606hRo4qe448/vnSPQgIECBAgQIAAAQIECBAgQIAAAQIECDSqgABgo9555yZAgAABAgQIECBAgAABAgQIdKDAW2+9FYsXL46bbroptmzZUnrTlClTigDgoEGDSvcoJECAAAECBAgQIECAAAECBAgQIECAQKMKCAA26p13bgIECBAgQIAAAQIECBAgQIBABwpU3vrX0tISDzzwQOkt++yzT/H537PPPju6d+9euk8hAQIECBAgQIAAAQIECBAgQIAAAQIEGlVAALBR77xzEyBAgAABAgQIECBAgAABAgQ6UOC+++4r3uT39NNPl97yuc99rug5+uijS/coJECAAAECBAgQIECAAAECBAgQIECAQCMLCAA28t13dgIECBAgQIAAAQIECBAgQIBABwhs3Lgxrrvuurj11lvjnXfeKbWhW7duxZv/5s6dGwMGDCjVo4gAAQIECBAgQIAAAQIECBAgQIAAAQKNLiAA2OhPgPMTIECAAAECBAgQIECAAAECBBILrF27tniT34oVK0pPHjRoUMyePTumTJkSO++8c+k+hQQIECBAgAABAgQIECBAgAABAgQIEGhkAQHARr77zk6AAAECBAgQIECAAAECBAgQ6ACB73//+0UA8E9/+lPp6ccff3zRM2rUqNI9CgkQIECAAAECBAgQIECAAAECBAgQINDoAgKAjf4EOD8BAgQIECBAgAABAgQIECBAIKHAyy+/HAsWLIjly5dHW1tbqcndu3eP888/v3gD4B577FGqRxEBAgQIECBAgAABAgQIECBAgAABAgQIRAgAegoIECBAgAABAgQIECBAgAABAgSSCaxcubJ4k9+vfvWr0jMPOOCAmDNnTpx++unR1NRUuk8hAQIECBAgQIAAAQIECBAgQIAAAQIEGl1AALDRnwDnJ0CAAAECBAgQIECAAAECBAgkEqi88W/p0qWxcOHC+Otf/1p66pgxY4rQ4MiRI0v3KCRAgAABAgQIECBAgAABAgQIECBAgAABbwD0DBAgQIAAAQIECBAgQIAAAQIECCQSePbZZ2P+/Plxzz33xLZt20pN7dWrV3z961+Pyy+/PD760Y+W6lFEgAABAgQIECBAgAABAgQIECBAgAABAv8U8AZATwIBAgQIECBAgAABAgQIECBAgEASgQcffLB4k98TTzxRet4hhxwSV111VYwfPz522mmn0n0KCRAgQIAAAQIECBAgQIAAAQIECBAgQEAA0DNAgAABAgQIECBAgAABAgQIECCQQODNN9+MxYsXx5IlS6K1tbX0xLFjxxahwREjRpTuUUiAAAECBAgQIECAAAECBAgQIECAAAEC/xTwBkBPAgECBAgQIECAAAECBAgQIECAQLsFHn/88SLI95Of/KT0rF133TVmzpwZ06dPj969e5fuU0iAAAECBAgQIECAAAECBAgQIECAAAEC/xQQAPQkECBAgAABAgQIECBAgAABAgQItFvgrrvuKgKAzz//fOlZlbf+zZ07N8aNG1e6RyEBAgQIECBAgAABAgQIECBAgAABAgQI/FtAANDTQIAAAQIECBAgQIAAAQIECBAg0C6BV155JRYsWBC33357tLW1lZ41fvz4IjR4yCGHlO5RSIAAAQIECBAgQIAAAQIECBAgQIAAAQL/FhAA9DQQIECAAAECBAgQIECAAAECBAi0S2DVqlXR0tISjzzySOk5/fv3j1mzZsWFF14YPXv2LN2nkAABAgQIECBAgAABAgQIECBAgAABAgT+LSAA6GkgQIAAAQIECBAgQIAAAQIECBCoWaC1tTWWLl0aixYtitdff730nJEjRxZv/xszZkzpHoUECBAgQIAAAQIECBAgQIAAAQIECBAg8F4BAUBPBAECBAgQIECAAAECBAgQIECAQM0Cf/zjH2P+/Pnxox/9KLZv3156zqRJk4oA4Cc+8YnSPQoJECBAgAABAgQIECBAgAABAgQIECBA4L0CAoCeCAIECBAgQIAAAQIECBAgQIAAgZoF7r333iLI98wzz5Sesffee0dzc3Occ8450aNHj9J9CgkQIECAAAECBAgQIECAAAECBAgQIEDgvQICgJ4IAgQIECBAgAABAgQIECBAgACBmgQ2bNgQCxcujDvuuCP+8Y9/lJ4xevToIjR4zDHHlO5RSIAAAQIECBAgQIAAAQIECBAgQIAAAQLvFxAA9FQQIECAAAECBAgQIECAAAECBAjUJPDwww8XQb5HH320dH/ljX/nnntuXHHFFVF5E6AfAQIECBAgQIAAAQIECBAgQIAAAQIECNQuIABYu51OAgQIECBAgAABAgQIECBAgEDDCmzevDluueWWuP766+ONN94o7fCpT30qZs+eHaeddlo0NTWV7lNIgAABAgQIECBAgAABAgQIECBAgAABAu8XEAD0VBAgQIAAAQIECBAgQIAAAQIECFQt8OSTT8bVV18dDzzwQGzfvr10/4QJE4q3Bh500EGlexQSIECAAAECBAgQIECAAAECBAgQIECAwH8XEAD0ZBAgQIAAAQIECBAgQIAAAQIECFQtcPfddxdBvnXr1pXu3W+//YpP/06ePDl69uxZuk8hAQIECBAgQIAAAQIECBAgQIAAAQIECPx3AQFATwYBAgQIECBAgAABAgQIECBAgEBVAi+99FIsXLgwvv3tb0dbW1vp3pNPPrkIDR522GGlexQSIECAAAECBAgQIECAAAECBAgQIECAwP8WEAD0dBAgQIAAAQIECBAgQIAAAQIECFQl8NOf/rQI8v3ud78r3de/f/+YOXNmTJs2LXr37l26TyEBAgQIECBAgAABAgQIECBAgAABAgQI/G8BAUBPBwECBAgQIECAAAECBAgQIECAQGmBv/zlL7F48eL41re+FVu2bCndN3r06Jg7d24ce+yxpXsUEiBAgAABAgQIECBAgAABAgQIECBAgMAHCwgAekIIECBAgAABAgQIECBAgAABAgRKCzz00EPF2/9+/etfl+6pvPGv8ua/yhsAK28C9CNAgAABAgQIECBAgAABAgQIECBAgACBNAICgGkcTSFAgAABAgQIECBAgAABAgQI1L3Axo0b44YbbohvfvObsXnz5tLnHTFiRFx11VUxduzY2GmnnUr3KSRAgAABAgQIECBAgAABAgQIECBAgACBDxYQAPSEECBAgAABAgQIECBAgAABAgQIlBJYvXp18fa/VatWlar/V9GkSZOKz/8OHjy4qj7FBAgQIECAAAECBAgQIECAAAECBAgQIPDBAgKAnhACBAgQIECAAAECBAgQIECAAIEdCrz11ltxyy23xDe+8Y144403dlj/r4IhQ4ZEc3NzTJw4Mbp37166TyEBAgQIECBAgAABAgQIECBAgAABAgQI7FhAAHDHRioIECBAgAABAgQIECBAgAABAg0vsGbNmmhpaYmf/exn8e6775b2OO2004q3Bg4dOrR0j0ICBAgQIECAAAECBAgQIECAAAECBAgQKCcgAFjOSRUBAgQIECBAgAABAgQIECBAoGEFtmzZErfddlssXrw4Xn311dIO+++/f1xxxRXxta99LXr27Fm6TyEBAgQIECBAgAABAgQIECBAgAABAgQIlBMQACznpIoAAQIECBAgQIAAAQIECBAg0LACa9eujfnz58eKFSti27ZtpR3Gjh1bvP1vxIgRpXsUEiBAgAABAgQIECBAgAABAgQIECBAgEB5AQHA8lYqCRAgQIAAAQIECBAgQIAAAQINJ/Dmm2/GrbfeGkuWLImNGzeWPv/AgQPj8ssvj7POOit69epVuk8hAQIECBAgQIAAAQIECBAgQIAAAQIECJQXEAAsb6WSAAECBAgQIECAAAECBAgQINBwAqtXr46WlpZYtWpVvPvuu6XPf+KJJxZv/zv88MNL9ygkQIAAAQIECBAgQIAAAQIECBAgQIAAgeoEBACr81JNgAABAgQIECBAgAABAgQIEGgYgddeey1uvPHGWLZsWbz99tulz73nnnvGzJkz47zzzovevXuX7lNIgAABAgQIECBAgAABAgQIECBAgAABAtUJCABW56WaAAECBAgQIECAAAECBAgQINAwAj//+c+Lt/g99thjVZ35uOOOK/qOPPLIqvoUEyBAgAABAgQIECBAgAABAgQIECBAgEB1AgKA1XmpJkCAAAECBAgQIECAAAECBAg0hMD69evj+uuvj+XLl8eWLVtKn3mPPfaIGTNmxLRp06JPnz6l+xQSIECAAAECBAgQIECAAAECBAgQIECAQPUCAoDVm+kgQIAAAQIECBAgQIAAAQIECNS9wI9//OPiLX6///3vqzrrCSecUPQdccQRVfUpJkCAAAECBAgQIECAAAECBAgQIECAAIHqBQQAqzfTQYAAAQIECBAgQIAAAQIECBCoa4FK6O+6666LSgjwnXfeKX3WfffdNy677LI488wzvf2vtJpCAgQIECBAgAABAgQIECBAgAABAgQI1C4gAFi7nU4CBAgQIECAAAECBAgQIECAQN0JvP7667F06dK49dZbo/J3Nb9x48YVb/8bPnx4NW1qCRAgQIAAAQIECBAgQIAAAQIECBAgQKBGAQHAGuG0ESBAgAABAgQIECBAgAABAgTqUWDFihXR0tISa9eujXfffbf0EQ888MCYNWtWTJw4MXbZZZfSfQoJECBAgAABAgQIECBAgAABAgQIECBAoHYBAcDa7XQSIECAAAECBAgQIECAAAECBOpK4Omnn47FixfHvffeG62traXP1tTUFF/96ldjzpw5MWTIkNJ9CgkQIECAAAECBAgQIECAAAECBAgQIECgfQICgO3z002AAAECBAgQIECAAAECBAgQqAuBTZs2xR133BE33XRTbNiwoaozHXroodHc3Bynnnpq9OjRo6pexQQIECBAgAABAgQIECBAgAABAgQIECBQu4AAYO12OgkQIECAAAECBAgQIECAAAECdSPw8MMPx/z58+PRRx+Nbdu2lT7XRz7ykZg6dWrMmDEj9tlnn9J9CgkQIECAAAECBAgQIECAAAECBAgQIECg/QICgO03NIEAAQIECBAgQIAAAQIECBAg0KUFnn/++bj++uvjrrvuis2bN1d1ltGjRxef/j3mmGOi8ilgPwIECBAgQIAAAQIECBAgQIAAAQIECBDIJyAAmM/aJgIECBAgQIAAAQIECBAgQIBAEoGNGzfGs88+G+vWrYuXXnopevfuHUOGDIlhw4bFfvvtV9WOLVu2xPe+971YvHhxvPjii1X17r///nHppZfG5MmTo/ImQD8CBAgQIECAAAECBAgQIECAAAECBAgQyCsgAJjX2zYCBAgQIECAAAECBAgQIECAQLsE1qxZE7fddlv89re/jbfffjtaW1uLN+9VAniDBw+O008/Pb74xS/GrrvuWmpP5ZO/11xzTVQ+Abx169ZSPZWi7t27x1e+8pW48sor45Of/GTpPoUECBAgQIAAAQIECBAgQIAAAQIECBAgkE5AADCdpUkECBAgQIAAAQIECBAgQIAAgQ4VeOKJJ+LGG2+MBx98MP7+97+/b1ePHj1iwIABcdlll8XZZ59dhPQ+6PfnP/+5mPed73ynCBNW8zv88MOjubk5TjrppB3uqWauWgIECBAgQIAAAQIECBAgQIAAAQIECBAoLyAAWN5KJQECBAgQIECAAAECBAgQIEDgQxN47bXXYsmSJbFs2bLYtGnTB17HCSecEHPnzo1Ro0b9z7p33nkn7rnnnli4cGE899xzVZ2rEjKcPn16nHPOOaXfNFjVAsUECBAgQIAAAQIECBAgQIAAAQIECBAgUEpAALAUkyICBAgQIECAAAECBAgQIECAwIcrsGrVqpg3b16sXr16hxfSt2/fIqA3Y8aMqPz9336VT/9ee+21sXLlymhra9vhzP8sOOWUU4prGTZsWFV9igkQIECAAAECBAgQIECAAAECBAgQIEAgrYAAYFpP0wgQIECAAAECBAgQIECAAAECHSLw3e9+N1paWuLFF18sNf+MM84o3gJ4wAEHvK9+3bp1ccMNN8Tdd99d9ad/K6G/WbNmxamnnho9e/YsdS2KCBAgQIAAAQIECBAgQIAAAQIECBAgQKBjBAQAO8bVVAIECBAgQIAAAQIECBAgQIBAUoHKp3orb90r+7a+z3/+80UA8IgjjnjPdbzxxhuxfPnyuPnmm+Pll1+u6hp33333uPDCC+Oiiy6Kyt9+BAgQIECAAAECBAgQIECAAAECBAgQIPDhCggAfrj+thMgQIAAAQIECBAgQIAAAQIESglU3v5XCQCW/R199NFFALDy73/+VqxYEfPnz4+1a9fGtm3byo4r6k488cS46qqrYuTIkdGtW7eqehUTIECAAAECBAgQIECAAAECBAgQIECAQHoBAcD0piYSIECAAAECBAgQIECAAAECBJILpAgAPvnkk7Fo0aJ44IEHorW1taprPPjgg2PmzJkxYcKE6NWrV1W9igkQIECAAAECBAgQIECAAAECBAgQIECgYwQEADvG1VQCBAgQIECAAAECBAgQIECAQFKB9gYAN2zYEEuWLInbb789Nm3aVNW19e3bN6ZOnRqXXHJJDBw4sKpexQQIECBAgAABAgQIECBAgAABAgQIECDQcQICgB1nazIBAgQIECBAgAABAgQIECBAIJlAewKAbW1tcf/998eCBQviqaeeqvqajjnmmJgzZ06MHj06mpqaqu7XQIAAAQIECBAgQIAAAQIECBAgQIAAAQIdIyAA2DGuphIgQIAAAQIECBAgQIAAAQIEkgq0JwD4m9/8pgj//eIXv4hKGLCa39ChQ2PGjBkxfvz46NOnTzWtagkQIECAAAECBAgQIECAAAECBAgQIECggwUEADsY2HgCBAgQIECAAAECBAgQIECAQAqBWgOAlU/23njjjfGDH/wg3n777aou5eMf/3hMmzYtLrjggujfv39VvYoJECBAgAABAgQIECBAgAABAgQIECBAoOMFBAA73tgGAgQIECBAgAABAgQIECBAgEC7BWoJAFbCe88991wsXbo0NmzYUNU1VD71O27cuOLTv8OGDYtu3bpV1a+YAAECBAgQIECAAAECBAgQIECAAAECBDpeQACw441tIECAAAECBAgQIECAAAECBAi0W6CWAOChhx4aq1evjj/84Q+xffv2qq5h5MiRccUVV8SYMWOiZ8+eVfUqJkCAAAECBAgQIECAAAECBAgQIECAAIE8AgKAeZxtIUCAAAECBAgQIECAAAECBAi0S6DaAOCnP/3pIrj3+OOPR1tbW1W7Bw8eHJdeemmcccYZ0bdv36p6FRMgQIAAAQIECBAgQIAAAQIECBAgQIBAPgEBwHzWNhEgQIAAAQIECBAgQIAAAQIEahaoNgDYp0+fYtfmzZur2tmvX7+YMmVKTJ8+PQYNGlRVr2ICBAgQIECAAAECBAgQIECAAAECBAgQyCsgAJjX2zYCBAgQIECAAAECBAgQIECAQE0C1QYAa1oSEV/4whdizpw58dnPfjaamppqHaOPAAECBAgQIECAAAECBAgQIECAAAECBDIICABmQLaCAAECBAgQIECAAAECBAgQINBegRwBwOHDh8fMmTPjlFNOiV69erX3kvUTIECAAAECBAgQIECAAAECBAgQIECAQAcLCAB2MLDxBAgQIECAAAECBAgQIECAAIEUAh0dABw4cGBcfPHFMXXq1Kh8BtiPAAECBAgQIECAAAECBAgQIECAAAECBDq/gABg579HrpAAAQIECBAgQIAAAQIECBAgEB0ZAOzdu3dMmDChePvfQQcdRJsAAQIECBAgQIAAAQIECBAgQIAAAQIEuoiAAGAXuVEukwABAgQIECBAgAABAgQIEGhsgY4MAB577LFx5ZVXxlFHHRXdu3dvbGinJ0CAAAECBAgQIECAAAECBAgQIECAQBcSEADsQjfLpRIgQIAAAQIECBAgQIAAAQKNK9BRAcDhw4cXb/4bN25cVN4E6EeAAAECBAgQIECAAAECBAgQIECAAAECXUdAALDr3CtXSoAAAQIECBAgQIAAAQIECDSwQEcEAPfff/+4+OKLY/LkydGvX78G1nV0AgQIECBAgAABAgQIECBAgAABAgQIdE0BAcCued9cNQECBAgQIECAAAECBAgQINBgAqkDgLvttlsR/KsEAPfbb78G03RcAgQIECBAgAABAgQIECBAgAABAgQI1IeAAGB93EenIECAAAECBAgQIECAAAECBOpcIHUA8OSTT47Zs2fHZz7zmWhqaqpzPccjQIAAAQIECBAgQIAAAQIECBAgQIBAfQoIANbnfXUqAgQIECBAgAABAgQIECBAoM4EUgYAK6G/WbNmxUknnRS77LJLnUk5DgECBAgKSfEXAAAgAElEQVQQIECAAAECBAgQIECAAAECBBpHQACwce61kxIgQIAAAQIECBAgQIAAAQJdWCBVAHDIkCFxySWXxMSJE6Nv375dWMSlEyBAgAABAgQIECBAgAABAgQIECBAgIAAoGeAAAECBAgQIECAAAECBAgQINAFBFIEAPv37x8XXXRRXHjhhfGxj32sC5zaJRIgQIAAAQIECBAgQIAAAQIECBAgQIDABwkIAHo+CBAgQIAAAQIECBAgQIAAAQJdQKC9AcCdd945zj333Jg9e3bstddeXeDELpEAAQIECBAgQIAAAQIECBAgQIAAAQIEdiQgALgjIf9PgAABAgQIECBAgAABAgQIEOgEAtdee23Mmzcvtm7dWtPVnHnmmUX/vvvuW1O/JgIECBAgQIAAAQIECBAgQIAAAQIECBDofAICgJ3vnrgiAgQIECBAgAABAgQIECBAgMD7BJYtWxaVtwC+9tprVetMmTKlCP8NGjSo6l4NBAgQIECAAAECBAgQIECAAAECBAgQINB5BQQAO++9cWUECBAgQIAAAQIECBAgQIAAgf8XuP/++4sQ31NPPVWVivBfVVyKCRAgQIAAAQIECBAgQIAAAQIECBAg0KUEBAC71O1ysQQIECBAgAABAgQIECBAgECjCjz00EPFGwAfffTRUgQDBw6MSvhv6tSp3vxXSkwRAQIECBAgQIAAAQIECBAgQIAAAQIEup6AAGDXu2eumAABAgQIECBAgAABAgQIEGhAgU2bNsUPf/jDWLJkSTz77LMfKDB48OC44IILYtKkSbHHHns0oJYjEyBAgAABAgQIECBAgAABAgQIECBAoDEEBAAb4z47JQECBAgQIECAAAECBAgQIFAHAn/729/innvuiWXLlsUzzzwT27Zte8+pdtpppxg2bFicf/758aUvfSl23333Oji1IxAgQIAAAQIECBAgQIAAAQIECBAgQIDA/xIQAPRsECBAgAABAgQIECBAgAABAgS6kEAlBLhu3bp47LHHYuXKlbF+/fri6gcMGBCjR4+Oo446Kg455JDYbbfdutCpXCoBAgQIECBAgAABAgQIECBAgAABAgQI1CIgAFiLmh4CBAgQIECAAAECBAgQIECAwIcosH379qh8Evj111+P1tbW4kp69epVvPGvX79+0dTU9CFendUECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQM9YLyQAAB17SURBVIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCChgABgQkyjCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIBALgEBwFzS9hAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAgYQCAoAJMY0iQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQK5BAQAc0nbQ4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEEgoIACbENIoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECOQSEADMJW0PAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBBIKCAAmBDTKAIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgkEtAADCXtD0ECBAgQIAAAQIECBAgQIAAAQIE/q9dO6YBAABAGObfNSYWrhqApPcIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCAQFgiGmKAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAi8BASAL2k/BAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIEAgFBAAhpimCBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIDAS0AA+JL2Q4AAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIEQgEBYIhpigABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIvAQEgC9pPwQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAIBQQAIaYpggQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAwEtAAPiS9kOAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBEIBAWCIaYoAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECLwEBIAvaT8ECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQIAAAQIECBAgQCAUEACGmKYIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgMBLQAD4kvZDgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgQIECBAgAABAgRCgQEkam26Rgph9wAAAABJRU5ErkJggg=='
        filename = convertDoodleImage(image, "unittest")
        self.assertTrue("doodles" == filename.split("/")[0])

    def test_printDoodles(self):
        user_id = create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        doodle = Doodles(foreign_answer="hello", foreign_guess="hello", location="test")
        db.session.add(doodle)
        db.session.commit()
        student_doodle = Student_Doodles(user_id=user_id, doodle_id=doodle.doodle_id)
        class_doodle = Class_Doodles(class_id="test", doodle_id=doodle.doodle_id)
        db.session.add_all([student_doodle, class_doodle])
        db.session.commit()

        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/printDoodles'
            )
            self.assertEqual(response.status_code, 302)

    def test_printDoodles2(self):
        user_id = create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        doodle = Doodles(foreign_answer="hello", foreign_guess="hello", location="test")
        db.session.add(doodle)
        db.session.commit()
        student_doodle = Student_Doodles(user_id=user_id, doodle_id=doodle.doodle_id)
        class_doodle = Class_Doodles(class_id="test", doodle_id=doodle.doodle_id)
        db.session.add_all([student_doodle, class_doodle])
        db.session.commit()
        doodle = Doodles(foreign_answer="hello", foreign_guess="hello", location="test")
        db.session.add(doodle)
        db.session.commit()
        student_doodle = Student_Doodles(user_id=user_id, doodle_id=doodle.doodle_id)
        class_doodle = Class_Doodles(class_id="test", doodle_id=doodle.doodle_id)
        db.session.add_all([student_doodle, class_doodle])
        db.session.commit()
        doodle = Doodles(foreign_answer="hello", foreign_guess="hello", location="test")
        db.session.add(doodle)
        db.session.commit()
        student_doodle = Student_Doodles(user_id=user_id, doodle_id=doodle.doodle_id)
        class_doodle = Class_Doodles(class_id="test", doodle_id=doodle.doodle_id)
        db.session.add_all([student_doodle, class_doodle])
        db.session.commit()
        doodle = Doodles(foreign_answer="hello", foreign_guess="hello", location="test")
        db.session.add(doodle)
        db.session.commit()
        student_doodle = Student_Doodles(user_id=user_id, doodle_id=doodle.doodle_id)
        class_doodle = Class_Doodles(class_id="test", doodle_id=doodle.doodle_id)
        db.session.add_all([student_doodle, class_doodle])
        db.session.commit()

        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/printDoodles'
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"Doodle Book" in response.data)

    def test_printDoodles3(self):
        user_id = create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/printDoodles'
            )
            self.assertEqual(response.status_code, 302)


    def test_printSummary(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/printSummary/test/student/1',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"You have yet to complete Course 1!" in response.data)

    def test_statsFromCompletedCourses(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get(
                '/completedCourses/student',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"You have not joined any classes yet!" in response.data)

    def test_statsFromCompletedCourses2(self):
        user_id = create_user("student", "test@test.com", app.config['PASSWORD'], current_class="test")
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        student_class = Student_Class(user_id, "test")
        db.session.add(student_class)
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.get(
                '/completedCourses/student',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"You have not yet completed any courses!" in response.data)


    def test_summary(self):
        newClass = Class("testclass1", "test", 2019, "French", "Class")
        db.session.add_all([newClass])
        db.session.commit()
        create_user(app.config['USERNAME'], "test@test.com", app.config['PASSWORD'], current_class="testclass1")
        student_class = Student_Class(app.config['USERNAME'], "testclass1")
        db.session.add_all([student_class])
        db.session.commit()
        with self.client:
            login(self.client, app.config['USERNAME'], app.config['PASSWORD'])
            response = self.client.post(
                '/summary/test/student/1',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"You have yet to complete Course 1!" in response.data)

    def test_createFindMeConfiguration(self):
        items = {'car': '123'}
        items = json.dumps(items)
        config = Find_Me_Configurations(class_id="test", items=items, eng_loc="test", for_loc="test")
        db.session.add(config)
        db.session.commit()
        response = self.client.post(
            '/createFindMeConfiguration/test'
        )
        self.assertEqual(response.status_code, 200)

    def test_createFindMeConfiguration2(self):
        response = self.client.post(
            '/createFindMeConfiguration/test'
        )
        self.assertEqual(response.status_code, 200)

    def test_searchForImages(self):
        data = {'search_term': '123'}
        data = json.dumps(data)
        response = self.client.post(
            '/searchForImages',
            data=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"image_urls" in response.data)

    def test_saveFindMeConfiguration(self):
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            newClass = Class("test", "test", 2019, "French", "Class")
            db.session.add(newClass)
            db.session.commit()
            data = {"config" : json.dumps({'car':123})}
            response = self.client.post(
                '/saveFindMeConfiguration/test',
                data=data
            )
            self.assertEqual(response.status_code, 302)
    
    def test_printFindMeConfiguration(self):
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/printFindMeConfiguration/test'
            )
            self.assertTrue(response.status_code, 302)

    def test_printFindMeConfiguration2(self):
        items = {'car': '123'}
        items = json.dumps(items)
        config = Find_Me_Configurations(class_id="test", items=items, eng_loc="test", for_loc="test")
        db.session.add(config)
        db.session.commit()
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/printFindMeConfiguration/test'
            )
            self.assertTrue(response.status_code, 200)

    def test_findMeConfiguration(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        userid = create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        teacherClass = Teacher_Class(user_id=userid, class_id="test")
        db.session.add(teacherClass)
        db.session.commit()
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/findMeConfiguration'
            )
            self.assertTrue(response.status_code, 200)

    def test_findMeConfiguration2(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        userid = create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/findMeConfiguration'
            )
            self.assertTrue(response.status_code, 302)




    def test_customFind(self):
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'languageIndex', "0")
            self.client.set_cookie('localhost', 'word', "book")
            self.client.set_cookie('localhost', 'activity_id', "21")
            response = self.client.post(
                '/customFind'
            )
            self.assertEqual(response.status_code, 302)

    def test_getCustomWord(self):
        fore, eng = getCustomWord('app/static/custom_find/test_for.txt', 'app/static/custom_find/test_eng.txt')
        self.assertEqual(fore, "voiture")
        self.assertEqual(eng, "car")

    def test_findCustomWord(self):
        fore = findCustomWord("car", 'app/static/custom_find/test_for.txt', 'app/static/custom_find/test_eng.txt')
        self.assertEqual(fore, "voiture")


    def test_createTextFiles(self):
        data = {"car": 123}
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        for_loc, eng_loc = createTextFiles(data, "test")
        self.assertEqual(for_loc, 'app/static/custom_find/test_for.txt')
        self.assertEqual(eng_loc, 'app/static/custom_find/test_eng.txt')

    @mock.patch('requests.post')
    def test_sendDataForTraining(self, mock_post):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            the_response = Response()
            the_response.status_code = 200
            the_response._content = b'We will notify you when your model has finished training!'
            mock_post.return_value = the_response
            data = {'category':'food',
                    'items':['potato', 'orange'],
                    'classname':'test'}
            data = json.dumps(data)

            response = self.client.post(
                '/sendDataForTraining',
                data={'data': data}
            )
            self.assertEqual(response.status_code, 302)
            self.assertTrue(b'unittest' in response.data)

    def test_finishedTraining(self):
        task = Task()
        db.session.add(task)
        db.session.commit()
        user_task = User_Task(user_id='test', task_id=task.task_id)
        db.session.add(user_task)
        db.session.commit()
        data = {'user_id': 'test',
                'class_id': 'test',
                'model_path': 'test',
                'category':'test'}
        data = json.dumps(data)
        response = self.client.post(
            '/finishedTraining',
            data=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Model Stored in DB" in response.data)

    def test_customGame(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        m = Model(model_loc='static/models/food_test_saved_model_web',for_loc='static/models/food_test_saved_model_web/for_labels.txt',eng_loc='static/models/food_test_saved_model_web/output_labels.txt', category='food')
        db.session.add(m)
        db.session.commit()
        cm = Class_Model(model_id=m.model_id, class_id='test')
        db.session.add(cm)
        db.session.commit()
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            self.client.set_cookie('localhost', 'activity_id', "22")
            response = self.client.post(
                '/customGame/test/food'
            )
            self.assertEqual(response.status_code, 200)

    def test_customGameImages(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="test")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/customGameImages/test/food'
            )
            self.assertEqual(response.status_code, 302)

    def test_printCustomGamesImages(self):
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/printCustomGamesImages/test/food'
            )
            self.assertTrue(response.status_code, 302)

    def test_printCustomGamesImages2(self):
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add(newClass)
        db.session.commit()
        create_user("unittest", "test@test.com", app.config['PASSWORD'], current_class="unittest")
        with self.client:
            data = {'potato': 123}
            data = json.dumps(data)
            login(self.client, "unittest", app.config['PASSWORD'])
            response = self.client.post(
                '/printCustomGamesImages/test/food',
                data={'images':data}
            )
            self.assertTrue(response.status_code, 200)

    def test_getCustomGameWord(self):
        a = getCustomGameWord('food', 'test')
        self.assertTrue(len(a), 2)

    def test_findCustomGameWord(self):
        a = findCustomGameWord('chocolate','food', 'test')
        self.assertTrue(a, "Chocolat")



if __name__ == '__main__':
    unittest.main()
