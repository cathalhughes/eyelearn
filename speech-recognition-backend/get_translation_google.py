from google.cloud import translate
import os
from html import unescape

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="translateKey.json"

translate_client = translate.Client()


def get_translation(prediction, language):

    print(prediction)
    result = translate_client.translate(
        prediction, target_language=language)

    return unescape(result['translatedText'])


