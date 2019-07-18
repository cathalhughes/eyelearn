from flask import render_template, redirect, url_for, flash, request, make_response, jsonify, send_from_directory, send_file
from app import db
from app.models import User, Teacher_Class, Class, Student_Class, Activity_Results, Student_Activity, Misspelled_Word, Class_Configs, Student_Class_Level, Find_Me_Configurations
from flask_login import login_user, logout_user, current_user, login_required
from app.main import bp
from datetime import datetime
import unidecode
import urllib.parse as urlparse
import random
from app.utils import checkForIncorrectCharacters
import requests
from app.doodle.routes import findWordForDoodle
from app.everyday_object_classification.routes import findWord, findCustomWord
from app.image_classification.routes import getCategoryWord, findCategoryWord
from app.create_classifier.routes import findCustomGameWord, getCustomGameWord
import os
import app
import json


languageIndices = {"French": 0, "Spanish": 1}
sports = {"golf":["golf", "golf"],"tennis":["tennis", "tenis"],"football":["foot", "fútbol"],"boxing":["boxe", "boxeo"],"skiing":["ski", "esquí"],"horseriding":["équitation", "equitación"],"basketball":["basket", "baloncesto"],"swimming":["nager", "nadando"],"volleyball":["volley-ball", "voleibol"],"rugby":["rugby", "rugby"]}
emotionsEmojis = {"angry":["fâché", "enojado"],"awkward":["gênant", "torpe"],"annoyed":["agacé", "irritado"],"cool":["impressionnant", "increíble"],"sad":["triste", "triste"],"shock":["choc", "choque"],"love":["amour", "amor"],"tired":["fatigué", "cansado"],"sick":["malade", "enfermos"], "scared":["effrayé", "asustado"], "funny":["marrant", "gracioso"]}
animals = {"bird":["oiseau", "pájaro"],"cat":["chat", "gato"],"cow":["vache", "vaca"],"dog":["chien", "perro"],"frog":["grenouille", "rana"],"hippo":["hipopotame", "hipopótamo"],"horse":["cheval", "caballo"],"lion":["leon", "león"],"monkey":["singe", "mono"], "bear": ["ours", "oso"], "fish":["poisson", "pez"], "pig":["porc", "cerdo"], "sheep": ["mouton", "oveja"], "tiger": ["tigre", "tigre"]}
vehicles = {"aeroplane":["avion", "avión"],"bike":["vélo", "bicicleta"],"bus":["autobus", "autobús"],"car":["voiture", "coche"],"train":["train", "entrenar"],"ferry":["traversier", "transportar"],"helicopter":["hélicoptère", "helicóptero"],"motorbike":["moto", "moto"],"taxi":["taxi", "taxi"], "truck":["camion", "camión"]}
classroom = {"monitor":["moniteur"],"glasses":["lunettes"],"computer":["ordinateur"],"mouse":["souris"],"CD Player":["lecteur CD"],"pencil case":["trousse"],"pencil sharpener":["taille-crayon"],"pen":["stylo"],"bottle":["bouteille"], "chair":["chaise"], "desk":["bureau"], "eraser":["gomme"], "printer":["imprimante"], "projector":["projecteur"], "backpack":["sac à dos"], "clock":["l'horloge"], "ruler":["règle"]}
allVocab = dict(sports)
allVocab.update(emotionsEmojis)
allVocab.update(animals)
allVocab.update(vehicles)
numbersDict = {1: ['un', "uno"], 2: ['deux', "dos"],3: ['trois', "tres"],4: ['quatre', "cuatro"],5: ['cinq', "cinco"],6: ['six', "seis"],7: ['sept', "siete"],8: ['huit', "ocho"],9: ['neuf', "nueve"],10: ['dix', "diez"],11: ['onze', "once"]}
voicesForApplication = {0: "French Female", 1: "Spanish Male"}
translationLanguage = {0: "fr", 1:"es"}


def get_class_vocab(dict):
    config = Class_Configs.query.filter_by(class_id=current_user.current_class).first()
    if config is None:
        return dict
    vocab_data = json.loads(config.vocab_data)
    vocab_data = vocab_data["Scramble"]
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


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/')
@login_required
def index():
    # print(current_user.current_class)
    if current_user.current_class == None:
        return redirect(url_for("user_management.createPracticeArea"))
    userClass = Class.query.filter_by(class_id=current_user.current_class).first_or_404()
    classLanguage = userClass.get_language()
    languageIndex = getLanguageIndex(classLanguage)
    get_class_vocab(allVocab)
    print(classLanguage)
    resp = make_response(render_template('index.html'))
    resp.set_cookie('word', " ")
    resp.set_cookie('correct', "0")
    resp.set_cookie('numGames', "0")
    resp.set_cookie('activity_id' " ")
    resp.set_cookie('languageIndex', str(languageIndex))
    return resp

def getLanguageIndex(lanaguage):
    return languageIndices[lanaguage]


@bp.route('/difficulty', methods=['GET', 'POST'])
@login_required
def diff():
    if request.method == 'POST':
        selectedClass = Class.query.filter_by(class_id=current_user.current_class).first()
        customGames = selectedClass.get_custom_games()
        config = Class_Configs.query.filter_by(class_id=current_user.current_class).first()
        if config is None:
            resp = make_response(render_template('level.html', config={}, current_level=0, customGames=customGames))
        else:
            currentLevel = current_user.get_current_level()
            configData = {'layout': json.loads(config.layout_data), 'data': json.loads(config.vocab_data),
                          'unlock_data': json.loads(config.unlock_data)}
            resp = make_response(render_template('level.html', config=configData, current_level=currentLevel,customGames=customGames))
        resp.set_cookie('correct', "0")
        resp.set_cookie('numGames', "0")
        resp.set_cookie('activity_id' " ")
        resp.set_cookie('word', " ")
        return resp
    else:
        selectedClass = Class.query.filter_by(class_id=current_user.current_class).first()
        customGames = selectedClass.get_custom_games()
        config = Class_Configs.query.filter_by(class_id=current_user.current_class).first()
        if config is None:
            resp = make_response(render_template('level.html', config={}, current_level=0, customGames=customGames))
        else:
            currentLevel = current_user.get_current_level()
            print(currentLevel)
            configData = {'layout': json.loads(config.layout_data), 'data': json.loads(config.vocab_data),
                          'unlock_data': json.loads(config.unlock_data)}
            resp = make_response(render_template('level.html', config=configData, current_level=currentLevel, customGames=customGames))
        resp.set_cookie('correct', "0")
        resp.set_cookie('numGames', "0")
        resp.set_cookie('activity_id' " ")
        resp.set_cookie('word', " ")
        return resp

@bp.route('/chooseGame', methods=['GET', 'POST'])
@login_required
def chooseGame():
    if request.method == 'POST':
        resp = make_response(render_template('level.html', config={}, current_level=0))
        resp.set_cookie('correct', "0")
        resp.set_cookie('numGames', "0")
        resp.set_cookie('activity_id' " ")
        resp.set_cookie('word', " ")
        return resp
    else:
        resp = make_response(render_template('level.html', config={}, current_level=0))
        resp.set_cookie('correct', "0")
        resp.set_cookie('numGames', "0")
        resp.set_cookie('activity_id' " ")
        resp.set_cookie('word', " ")
        return resp

@bp.route('/checkguess',methods=['POST'])
@login_required
def check():
    print("IN check guess")
    numGames = int(request.cookies.get("numGames"))
    languageIndex = int(request.cookies.get("languageIndex"))
    numGames += 1
    numCorrect = int(request.cookies.get("correct"))
    url = request.referrer
    path = urlparse.urlparse(url).path
    print(path)
    guess = request.form['guess'].strip()
    print(guess + "in check guess")
    word = request.cookies.get('word')
    print(word, "from swipe")
    if path == "/numbersOrSpelling" or path == "/swipeWords":
        word = allVocab[word][languageIndex]
        word = unidecode.unidecode(word)
    print(word + "------------")
    if "/swipe1" in path:
        print("in swipe1")
        category = path.split("/")[2]
        if languageIndex == 0:
            language = "fr"
        else:
            language = "es"
        word = findCategoryWord(word, category, language)
        print(word + " from swipe1")
        print(guess + " from swwipe1")
    if "/customSwipeGame" in path:
        category = path.split("/")[3]
        print(category)
        word = findCustomGameWord(word, category, current_user.current_class)
        print(word, guess)
    guess = guess.lower()
    word = word.lower()

    if guess == word or guess==(word+" "):

        numCorrect += 1
        resp = make_response(render_template('correct.html', path=path, score=[numCorrect, numGames]))
        resp.set_cookie("correct", str(numCorrect))
        resp.set_cookie("numGames", str(numGames))

        return resp
    else:
        resp = make_response(render_template('incorrect.html', path=path, score=[numCorrect, numGames]))
        resp.set_cookie("numGames", str(numGames))
        if path == "/numbersOrSpelling":
            checkForIncorrectCharacters(guess, word)
        return resp


@bp.route('/scramble', methods=['POST', "GET"])
@login_required
def scramble():
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
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

    # else:
    #     wordForGame = allVocab[word][0]

    wordlist = list(word)
    scrwordlist = random.sample(wordlist, len(wordlist))

    scrword = " "

    for i in range(0, len(scrwordlist)):
        scrword = (scrword + scrwordlist[i] + " ")
    print(scrword)
    scramble = {"Your word is....": scrword}

    resp = make_response(render_template('guess.html', scramble=scramble))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/tts', methods=['POST', "GET"])
@login_required
def tts():
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        print("from form")
        activity_id = request.form["activity_id"]
    print(active_activity, activity_id)
    # print(word)
    if word == " ":
        key = random.choice(list(allVocab.keys()))
        print(key)
        word = key
        print(word)
        wordForGame = allVocab[key][languageIndex]
    else:
        wordForGame = allVocab[word][languageIndex]

    voice = getVoice(languageIndex)

    scramble = {"Your word is....": [wordForGame, voice]}

    resp = make_response(render_template('tts.html', scramble=scramble))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/download')
def downloadUserManual():
    if current_user.role == "Student":
        return send_file('static/manuals/StudentManual.pdf', as_attachment=True)
    return send_file('static/manuals/TeacherManual.pdf', as_attachment=True)


@bp.route('/playAgain', methods=['POST'])
def playAgain():
    print(request.values)
    status = request.form["status"]
    path = request.form["path"]
    print(path)
    if(status == "correct"):
        resp = make_response(redirect(path))
        resp.set_cookie('word', " ")
        return resp
    resp = make_response(redirect(path))
    return resp

@bp.route('/answer',methods=['POST'])
def answer():
    #print(current_user.role)
    word = request.cookies.get('word')
    print(word)
    path = request.form["path"]
    languageIndex = int(request.cookies.get("languageIndex"))
    voice = ""
    english = word


    if path == "/doodle":
        translated, model = findWordForDoodle(word, languageIndex)
    elif path == "/find":
        translated = findWord(word, languageIndex)
    elif path == "/customFind":
        findMeConfig = Find_Me_Configurations.query.filter_by(class_id=current_user.current_class).first()
        translated = findCustomWord(word, findMeConfig.for_loc, findMeConfig.eng_loc)

    elif "findCategory" in path or "swipe1" in path:
        if languageIndex == 0:
            language = "fr"
        else:
            language = "es"
        category = path.split("/")[2]
        translated = findCategoryWord(word, category, language)

    elif "customGame" in path or "customSwipeGame" in path:
        print("customGame")
        translated = findCustomGameWord(word, path.split("/")[3], path.split("/")[2])

    elif path == "/tilesGame":
        print("tiles")
        newVocab = current_user.get_students_new_vocab(current_user.current_class).all()
        englishWords = [vocab.english for vocab in newVocab]
        translations =  [vocab.translation for vocab in newVocab]
        index = englishWords.index(word)
        english = word
        word = translations[index]
        translated = word

    elif path == "/numbersOrSpelling" or path == "/swipeWords":
        english = word
        word = allVocab[word][languageIndex]
        translated = word

    elif path == "/numbers":
        english = word
        translated = numbersDict[int(english)][languageIndex]

    elif word in allVocab:
        translated = allVocab[word][languageIndex]



    else:
        print(word)
        translated = word
        #word = allVocab[word][languageIndex]
        translated = word

    if path == "/speech":
        voice = getVoice(languageIndex)

    if path != "/speech" and path != "/scramble":
        misspelled_word = Misspelled_Word(class_id=current_user.current_class, user_id=current_user.user_id, word=english, translated_word=translated)
        db.session.add(misspelled_word)
        db.session.commit()
    dword = { "Your word was....":word}
    resp = make_response(render_template('answer.html',dword=dword, path=path, voice=voice))
    resp.set_cookie("word", " ")
    return resp




@bp.route("/endgame")
def endGame():
    #Update DB with score and currect user ID
    if(int(request.cookies.get("numGames")) == 0):
        score = 0
    else:
        score = int(request.cookies.get("correct")) / int(request.cookies.get("numGames")) * 100
    activity_id = int(request.cookies.get("activity_id"))
    print(activity_id)
    activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=current_user.current_class)
    db.session.add(activity_result)
    db.session.commit()
    student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id, student_id=current_user.user_id)

    db.session.add(student_activity)
    db.session.commit()

    config = Class_Configs.query.filter_by(class_id=current_user.current_class).first()
    if config is not None:
        current_level = current_user.get_current_level()
        active_level = current_user.get_active_level()
        print(current_level, active_level)
        if active_level < current_level:
            ##do update here
            current_user.freeze_stats()
            current_user.update_level(current_level)
            print("Current Level: " + str(current_level))
            if active_level != 3:
                flash("Congratulations, you have completed Course " + str(active_level) + ", you can now see your stats for this course!")
            else:
                flash("Congratulations you have completed all courses in your class! More statistics have been unlocked as well as a Certificate of Completion!")
            return redirect(url_for("user_management.user", username=current_user.username))


    return redirect(url_for("main.index"))

@bp.route("/swipeWords", methods=["POST", "GET"])
@login_required
def swipeWords():
    word = request.cookies.get('word')
    print(word, "empty")
    get_class_vocab(allVocab)
    verbs.update(allVocab)
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        print("from form")
        activity_id = request.form["activity_id"]
    print(active_activity, activity_id)
    print(word)
    if word == " ":
        key = random.choice(list(verbs.keys()))
        print(key, "word")
        word = verbs[key][languageIndex]
        print(word)
        wordForGame = key
    else:
        wordForGame = word
    scramble = {"Your word is....": wordForGame}

    resp = make_response(render_template('swipeWords.html', scramble=scramble))
    print(word, wordForGame)
    resp.set_cookie('word', wordForGame)
    resp.set_cookie('activity_id', activity_id)
    return resp


verbs = {"to go": ["aller", "ir"], "to think": ["penser", "pensar"], "to talk": ["parler", "hablar"]}
from random import shuffle

@bp.route("/getWords/<word>")
def getWords(word):
    get_class_vocab(allVocab)
    verbs.update(allVocab)
    languageIndex = int(request.cookies.get("languageIndex"))
    print(languageIndex)
    word = " ".join(word.split("_"))
    print(word)
    keyWord = verbs[word][languageIndex]
    print(keyWord)
    data = [keyWord]
    for i in range(9):
        print(i)
        data.append(verbs[random.choice(list(verbs.keys()))][languageIndex])
    shuffle(data)
    print(data)
    response = {'data': data}
    return jsonify(response)

@bp.route("/phraseTranslator", methods=['POST', 'GET'])
@login_required
def phraseTranslator():
    languageIndex = int(request.cookies.get("languageIndex"))
    language = getTranslationLanguage(languageIndex)
    return render_template("tagger.html", language=language)

@bp.route("/info", methods=['POST', 'GET'])
def info():
    return render_template("landing_page.html")



def getTranslationLanguage(languageIndex):
    return translationLanguage[languageIndex]

def getVoice(languageIndex):
    return voicesForApplication[languageIndex]