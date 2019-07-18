from flask import render_template, redirect, url_for, flash, request, make_response
from app import db
from app.models import Student_Vocab, Class_Configs, Class
from flask_login import login_user, logout_user, current_user, login_required
from app.speech_recognition import bp
import urllib.parse as urlparse
import random
import requests
import json

sports = {"golf":["golf"],"tennis":["tennis"],"football":["foot"],"boxing":["boxe"],"skiing":["ski"],"horseriding":["équitation"],"basketball":["basket"],"swimming":["nager"],"volleyball":["volley-ball"],"rugby":["rugby"]}
emotionsEmojis = {"angry":["fâché"],"awkward":["gênant"],"annoyed":["agacé"],"cool":["impressionnant"],"sad":["triste"],"shock":["choc"],"love":["amour"],"tired":["fatigué"],"sick":["malade"], "scared":["effrayé"], "funny":["marrant"]}
animals = {"bird":["oiseau"],"cat":["chat"],"cow":["vache"],"dog":["chien"],"frog":["grenouille"],"hippo":["hipopotame"],"horse":["cheval"],"lion":["leon"],"monkey":["singe"], "bear": [""], "fish":["poisson"], "pig":["porc"], "sheep": ["mouton"], "tiger": ["tigre"]}
vehicles = {"aeroplane":["avion"],"bike":["vélo"],"bus":["autobus"],"car":["voiture"],"train":["train"],"ferry":["traversier"],"helicopter":["hélicoptère"],"motorbike":["moto"],"taxi":["taxi"], "truck":["camion"]}
classroom = {"monitor":["moniteur"],"glasses":["lunettes"],"computer":["ordinateur"],"mouse":["souris"],"CD Player":["lecteur CD"],"pencil case":["trousse"],"pencil sharpener":["taille-crayon"],"pen":["stylo"],"bottle":["bouteille"], "chair":["chaise"], "desk":["bureau"], "eraser":["gomme"], "printer":["imprimante"], "projector":["projecteur"], "backpack":["sac à dos"], "clock":["l'horloge"], "ruler":["règle"]}
allVocab = dict(sports)
allVocab.update(emotionsEmojis)
allVocab.update(animals)
allVocab.update(vehicles)

recognitionLanguages = {0: "fr-FR", 1:"es-ES"}
translationLanguage = {0: "fr", 1:"es"}
voices = {0: "French Female", 1: "Spanish Male"}

@bp.route('/speech', methods=['POST', 'GET'])
@login_required
def speech():
    #word = request.cookies.get('word')
    # # print(word)
    # if word == " ":
    #     key = random.choice(list(fr.keys()))
    #     print(key)
    #     word = key
    #     print(word)
    get_class_vocab(allVocab)
    print(allVocab)
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    voice = getVoice(languageIndex)
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    # print(word)
    if word == " ":
        key = random.choice(list(allVocab.keys()))
        print(key)

        wordForGame = allVocab[key][languageIndex]
        word = wordForGame
        print(word)
    #voice = "French Female"
    wordlist = word
    print(" ".join(wordlist), word)
    # scrwordlist = random.sample(wordlist, len(wordlist))
    #
    # scrword = " "
    #
    # for i in range(0, len(scrwordlist)):
    #     scrword = (scrword + scrwordlist[i] + " ")
    # print(scrword)
    userClass = Class.query.filter_by(class_id=current_user.current_class).first_or_404()
    classLanguage = userClass.get_language()

    scramble = {"Speak in " + classLanguage + "....": [wordlist, voice, word]}

    resp = make_response(render_template('speechrecognition.html', scramble=scramble, voice=voice))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/sendSpeech', methods=['POST', 'GET'])
def sendSpeech():
    audio = request.files['audio_data']
    # image.save('selfie.png')
    numGames = int(request.cookies.get("numGames"))
    numGames += 1
    numCorrect = int(request.cookies.get("correct"))
    languageIndex = int(request.cookies.get("languageIndex"))
    url = request.referrer
    path = urlparse.urlparse(url).path
    print(audio)
    recognitionLanguage = getRecognitionLangauge(languageIndex) ## getLangForUser()
    r = requests.post("https://speech.eyelearn.club/predictWord", files={"audio_data": audio, 'recognition_language': recognitionLanguage}, verify=False)
    print(r.content)
    results = json.loads(r.content)
    print(results)
    word = request.cookies.get('word')
    print(word, type(results['transcription']))
    # if results['transcription'] == None:
    #     print("in here")
    #     return render_template('incorrect.html', score=[0,0])
    # #for result in results['transcription']:
    # if results['transcription'] == word:
    #     return render_template('correct.html', score=[0,0])
    # return render_template('incorrect.html', score=[0,0])

    if results['transcription'] == word or results['transcription'] == (word+" "):

        numCorrect += 1
        resp = make_response(render_template('correct.html', path=path, score=[numCorrect, numGames]))
        resp.set_cookie("correct", str(numCorrect))
        resp.set_cookie("numGames", str(numGames))

        return resp
    else:
        resp = make_response(render_template('incorrect.html', path=path, score=[numCorrect, numGames]))
        resp.set_cookie("numGames", str(numGames))
        return resp


@bp.route('/getSpeechTranslation', methods=['POST', 'GET'])
def getSpeechTranslation():
    audio = request.files['audio_data']
    languageIndex = int(request.cookies.get("languageIndex"))
    lang = getTranslationLanguage(languageIndex)
    voice = getVoice(languageIndex)
    # image.save('selfie.png')
    print(audio)
    recognitionLanguage = 'en-EN'
    r = requests.post("https://speech.eyelearn.club/predictWord", files={"audio_data": audio, "lang": lang, "recognition_language": recognitionLanguage}, verify=False)
    print(r.content)
    results = json.loads(r.content)
    if check_if_word_in_table_for_user_in_class(current_user.user_id, current_user.current_class, results["transcription"]) == []:
        newVocab = Student_Vocab(english=results["transcription"], translation=results['translation'], user_id=current_user.user_id,
                                 class_id=current_user.current_class, activity_id=13)
        db.session.add(newVocab)
        db.session.commit()
    return render_template("speechtranslator.html", results=[results['transcription'], results['translation']], voice=voice)

@bp.route('/speechTranslation', methods=['POST', 'GET'])
@login_required
def speechTranslation():
    return render_template("speechtranslator.html")

def getRecognitionLangauge(languageIndex):
    return recognitionLanguages[languageIndex]

def getTranslationLanguage(languageIndex):
    return translationLanguage[languageIndex]

def getVoice(languageIndex):
    return voices[languageIndex]

def check_if_word_in_table_for_user_in_class(user_id, class_id, word):
    return Student_Vocab.query.filter_by(user_id=user_id, class_id=class_id, english=word).all()

def get_class_vocab(dict):
    config = Class_Configs.query.filter_by(class_id=current_user.current_class).first()
    if config is None:
        return dict
    vocab_data = json.loads(config.vocab_data)
    vocab_data = vocab_data["Speak Up!"]
    vocab_dict = {}
    userClass = Class.query.filter_by(class_id=current_user.current_class).first_or_404()
    classLanguage = userClass.get_language()
    if classLanguage == "French":
        for eng in vocab_data:
            vocab_dict[eng] = [vocab_data[eng], ""]
    else:
        for eng in vocab_data:
            vocab_dict[eng] = ["" , vocab_data[eng]]

    print(vocab_dict)
    dict.update(vocab_dict)
    return dict