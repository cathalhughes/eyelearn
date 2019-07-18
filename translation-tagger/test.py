import unittest
import os
from flask_testing import TestCase
from mock import Mock, patch



from app import app, map_french_tag_to_universal, create_french_to_universal_dict, create_spanish_to_universal_dict, map_spanish_tag_to_universal, pos_tagger_spanish, word_tokenize, pos_tagger_french

get_translation_free = Mock(return_value="Je suis libre")

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


    def test_getPhraseTranslation(self):
        data = {"phrase": "I am free", "language": "fr"}
        response = self.client.post(
            '/getPhraseTranslation',
            data=data,
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'taggedPhrase' in response.data)

    def test_getPhraseTranslation1(self):
        data = {"phrase": "I am free", "language": "es"}
        response = self.client.post(
            '/getPhraseTranslation',
            data=data,
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'taggedPhrase' in response.data)



    def test_get_translation_free(self):
        language = "fr"
        phrase = "I am free"
        translatedPhrase = get_translation_free(phrase, language)
        self.assertNotEqual(translatedPhrase, "")
        self.assertEqual(type(phrase), str)

    def test_map_french_tag_to_universal(self):
        res_french = pos_tagger_french.tag(word_tokenize("je suis libre"))
        simplified_pos_tags_french = map_french_tag_to_universal(res_french)
        self.assertEqual(simplified_pos_tags_french, [('je', 'PRON'), ('suis', 'VERB'), ('libre', 'ADJ')])

    def test_map_french_tag_to_universal1(self):
        res_french = [('je', 'CLS'), ('suis', 'V'), ('libre', 'ADJ')]
        simplified_pos_tags_french = map_french_tag_to_universal(res_french)
        self.assertEqual(simplified_pos_tags_french, [('je', 'PRON'), ('suis', 'VERB'), ('libre', 'ADJ')])

    def test_create_french_to_universal_dict(self):
        dict = create_french_to_universal_dict()
        self.assertEqual(len(dict) > 0, True)

    def test_create_spanish_to_universal_dict(self):
        dict = create_spanish_to_universal_dict()
        self.assertEqual(len(dict) > 0, True)
        self.assertTrue("ADJ" in dict.values())

    def test_map_spanish_tag_to_universal(self):
        res_spanish = pos_tagger_spanish.tag(word_tokenize("soy libre"))
        simplified_pos_tags_spanish = map_spanish_tag_to_universal(res_spanish)

        self.assertEqual(simplified_pos_tags_spanish, [('soy', 'VERB'), ('libre', 'ADJ')])



if __name__ == '__main__':
    unittest.main()
