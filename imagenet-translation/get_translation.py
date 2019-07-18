import requests
import json

from googletrans import Translator

# def get_translation_free(predictions, language):
#
#     translatedPredictions = []
#     for prediction in predictions:
#         prediction = prediction[1].split("_")
#         prediction = "+".join(prediction)
#         r = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + language +  "&dt=t&q=" + prediction)
#         content = json.loads(str(r.content, 'utf-8'))
#         translatedPredictions.append(content[0][0][0])
#
#     return translatedPredictions
translator = Translator()

def get_translation_free(predictions, language):

    translatedPredictions = []
    for prediction in predictions:
        prediction = prediction[1].split("_")
        prediction = " ".join(prediction)
        print(prediction)
        translatedPrediction = translator.translate(prediction, dest=language).text
        print(translatedPrediction)
        translatedPredictions.append(translatedPrediction)

    return translatedPredictions



