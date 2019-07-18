from google.cloud import translate
import os
from html import unescape

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="translateKey.json"

translate_client = translate.Client()


def get_translation(predictions, language):
    translatedPredictions = []
    for prediction in predictions:
        prediction = prediction[1].split("_")
        prediction = " ".join(prediction)
        print(prediction)
        result = translate_client.translate(
            prediction, target_language=language)
        translatedPredictions.append(unescape(result['translatedText']))

    return translatedPredictions

