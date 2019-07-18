from google.cloud import translate
import urllib.request
import requests
import json




def get_translation_free(prediction, language):


    prediction = prediction.split(" ")
    prediction = "+".join(prediction)
    #contents = urllib.request.urlopen("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + language +  "&dt=t&q=" + prediction).read()
    r = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + language +  "&dt=t&q=" + prediction)
    content = json.loads(str(r.content, 'utf-8'))

    return content[0][0][0]

