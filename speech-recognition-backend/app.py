from flask import Flask, request, Response, render_template, flash, redirect, url_for, jsonify
from audio_processing import *
import ssl
from flask_cors import CORS
from get_translation_google import *

# ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ctx.load_cert_chain('ssl.crt', 'ssl.key')


app = Flask(__name__)
app.secret_key = "MY_SECRET_KEY"

CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)


recogniser = get_recorder()

@app.route('/predictWord', methods=['GET', 'POST'])
def predictWord():
    #
    print('lang' in request.files)
    audio = request.files["audio_data"]
    recognitionLanguage = str(request.files['recognition_language'].read(), 'utf-8')
    print(recognitionLanguage)

    # audio = request.get_data()['audio_data']
    # audio.save("audio.wav")
    print(audio)
    #audio.save("audio.wav")
    audio = get_audio(audio, recogniser)
    response = recognise_audio(audio, recogniser, recognitionLanguage)
    if 'lang' in request.files != None:
        print("here")
        language = str(request.files['lang'].read(), 'utf-8')
        print(language)
        response['translation'] = get_translation(response['transcription'], language)
    print(response)
    return jsonify(response)

#app.run(host='localhost', port=5001) # ssl_context=ctx ,threaded=True, debug=True)
