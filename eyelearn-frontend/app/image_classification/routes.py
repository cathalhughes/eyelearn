from flask import render_template, redirect, url_for, flash, request, make_response, jsonify
from app import db
from app.models import Student_Vocab
from flask_login import login_user, logout_user, current_user, login_required
from app.image_classification import bp
import urllib.parse as urlparse
import random
import requests
import json
import os


import io
from azure.cognitiveservices.search.imagesearch import ImageSearchAPI
from msrest.authentication import CognitiveServicesCredentials
import datetime
subscription_key = "456aa06c006041b787e834923e7ee183"
client = ImageSearchAPI(CognitiveServicesCredentials(subscription_key))

endpoints = {"sports":"predictSport",
              "emojis":"predictEmotion",
              "animals":"predictAnimal",
              "vehicles":"predictVehicle",
             "classroom":"translateObject"}
translationLanguage = {0: "fr", 1:"es"}

sports = {"golf":["golf", "golf"],"tennis":["tennis", "tenis"],"football":["foot", "fútbol"],"boxing":["boxe", "boxeo"],"skiing":["ski", "esquí"],"horseriding":["équitation", "equitación"],"basketball":["basket", "baloncesto"],"swimming":["nager", "nadando"],"volleyball":["volley-ball", "voleibol"],"rugby":["rugby", "rugby"]}
emotionsEmojis = {"angry":["fâché", "enojado"],"awkward":["gênant", "torpe"],"annoyed":["agacé", "irritado"],"cool":["impressionnant", "increíble"],"sad":["triste", "triste"],"shock":["choc", "choque"],"love":["amour", "amor"],"tired":["fatigué", "cansado"],"sick":["malade", "enfermos"], "scared":["effrayé", "asustado"], "funny":["marrant", "gracioso"]}
animals = {"bird":["oiseau", "pájaro"],"cat":["chat", "gato"],"cow":["vache", "vaca"],"dog":["chien", "perro"],"frog":["grenouille", "rana"],"hippo":["hipopotame", "hipopótamo"],"horse":["cheval", "caballo"],"lion":["leon", "león"],"monkey":["singe", "mono"], "bear": ["ours", "oso"], "fish":["poisson", "pez"], "pig":["porc", "cerdo"], "sheep": ["mouton", "oveja"], "tiger": ["tigre", "tigre"]}
vehicles = {"aeroplane":["avion", "avión"],"bike":["vélo", "bicicleta"],"bus":["autobus", "autobús"],"car":["voiture", "coche"],"train":["train", "entrenar"],"ferry":["traversier", "transportar"],"helicopter":["hélicoptère", "helicóptero"],"motorbike":["moto", "moto"],"taxi":["taxi", "taxi"], "truck":["camion", "camión"]}
classroom = {"monitor":["moniteur"],"glasses":["lunettes"],"computer":["ordinateur"],"mouse":["souris"],"CD Player":["lecteur CD"],"pencil case":["trousse"],"pencil sharpener":["taille-crayon"],"pen":["stylo"],"bottle":["bouteille"], "chair":["chaise"], "desk":["bureau"], "eraser":["gomme"], "printer":["imprimante"], "projector":["projecteur"], "backpack":["sac à dos"], "clock":["l'horloge"], "ruler":["règle"]}
emotions = {'happy': ['heureux', 'feliz'], 'sad': ['triste', 'triste'],'angry': ['fâché', 'enojado'],'fear': ['peur', 'temor'],'neutral': ['neutre', 'neutro'],'surprise': ['surprise', 'sorpresa'],'disgust': ['dégoût', 'asco']}

categories = {"sports":sports,
              "emojis":emotionsEmojis,
              "animals":animals,
              "vehicles":vehicles,
              "classroom": classroom}



@bp.route('/selfie/<category>', methods=['POST', "GET"])
@login_required
def selfie(category=None):
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    wordDict = getDictForGame(category)
    if word == " " or word not in wordDict:
        key = random.choice(list(wordDict.keys()))
        print(key)

        wordForGame = wordDict[key][languageIndex]
        word = key
        print(word)

    else:
        wordForGame = wordDict[word][languageIndex]

    wordlist = list(wordForGame)

    scrwordlist = wordlist

    scrword = " "

    for i in range(0, len(scrwordlist)):
        scrword = (scrword + scrwordlist[i] + " ")
    print(scrword, word)
    scramble = {"Your word is....": scrword}
    resp = make_response(render_template('selfie.html', scramble=scramble, category=[category]))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/imagenet/<category>', methods=['POST', "GET"])
@login_required
def imagenet(category):
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    wordDict = getDictForGame(category)
    if word == " ":
        key = random.choice(list(wordDict.keys()))
        print(key)

        wordForGame = wordDict[key][languageIndex]
        word = key
        print(word)

    else:
        wordForGame = wordDict[word][languageIndex]

    wordlist = list(wordForGame)

    scrwordlist = wordlist

    scrword = " "

    for i in range(0, len(scrwordlist)):
        scrword = (scrword + scrwordlist[i] + " ")
    print(scrword, word)
    scramble = {"Your word is....": scrword}
    resp = make_response(render_template('imagenet.html', scramble=scramble, category=[category]))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/sendImagenet/<category>', methods=['POST', 'GET'])
@login_required
def sendImagenet(category):
    endpoint = getEndpoint(category)
    numGames = int(request.cookies.get("numGames"))
    numCorrect = int(request.cookies.get("correct"))
    numGames += 1
    url = request.referrer
    path = urlparse.urlparse(url).path
    image = request.files['image']
    image.save('image.png')
    if endpoint == "translateObject":
        r = requests.post("https://35.196.67.10/translateObject", files={'image1': open('foo.png', 'rb')}, verify=False)
    else:
        r = requests.post("https://104.196.196.153/" + endpoint, files={'image1': open('image.png', 'rb')}, verify=False)
    print(r.content)

    results = str(r.content, "utf-8")
    print(results)
    word = request.cookies.get('word')
    print(word, results)
    results = json.loads(results)
    results = results['predictions']

    for result in results:
        guess = result[1].lower()
        print(guess, word)

        if word in guess:

            numCorrect += 1
            resp = make_response(render_template('correct.html', path=path, score=[numCorrect, numGames]))
            resp.set_cookie("correct", str(numCorrect))
            resp.set_cookie("numGames", str(numGames))

            return resp

    resp = make_response(render_template('incorrect.html', path=path, score=[numCorrect, numGames]))
    resp.set_cookie("numGames", str(numGames))
    return resp

@bp.route('/verbs', methods=['POST'])
@login_required
def verbs():
    word = request.cookies.get('word')
    languageIndex = int(request.cookies.get("languageIndex"))
    if word == " ":
        key = random.choice(list(verbs.keys()))
        print(key)
        word = emotions[key][languageIndex]

    wordlist = list(word)

    scrwordlist = wordlist

    scrword = " "

    for i in range(0, len(scrwordlist)):
        scrword = (scrword + scrwordlist[i] + " ")
    print(scrword, word)
    scramble = {"Your verb is....": scrword}

    resp = make_response(render_template('ocr.html', scramble=scramble))
    resp.set_cookie('word', word)
    return resp

@bp.route('/sendTextImage', methods=['POST', 'GET'])
def sendTextImage():
    print("in send text")
    image = request.files['image']
    image.save('text.png')
    r = requests.post("http://192.168.0.241:5004/ocrResult", files={'image1': open('text.png', 'rb')})
    print(r.content)
    results = json.loads(r.content)
    print(results)
    word = request.cookies.get('word')
    print(word, results)
    if results == []:
        print("in here successful mock")
        return render_template('incorrect.html', score=[0,0])
    for result in results:
        if result == word:
            return render_template('correct.html', score=[0,0])
    return render_template('incorrect.html', score=[0,0])

def getEndpoint(category):
    return endpoints[category]

@bp.route('/sendSelfie/<category>', methods=['POST', 'GET'])
def sendSelfie(category):
    endpoint = getEndpoint(category)
    numGames = int(request.cookies.get("numGames"))
    numCorrect = int(request.cookies.get("correct"))
    numGames += 1
    url = request.referrer
    path = urlparse.urlparse(url).path
    image = request.files['image']
    image.save('selfie.png')
    r = requests.post("https://104.196.196.153/" + endpoint, files={'image1': open('selfie.png', 'rb')})
    print(r.content)

    results = str(r.content, "utf-8")
    print(results)
    word = request.cookies.get('word')
    print(word, results)

    guess = results.lower()
    if guess == word or guess==(word+" "):

        numCorrect += 1
        resp = make_response(render_template('correct.html', path=path, score=[numCorrect, numGames]))
        resp.set_cookie("correct", str(numCorrect))
        resp.set_cookie("numGames", str(numGames))

        return resp
    else:
        resp = make_response(render_template('incorrect.html', path=path, score=[numCorrect, numGames]))
        resp.set_cookie("numGames", str(numGames))
        return resp

@bp.route("/swipe/<category>", methods=['GET', 'POST'])
@login_required
def swipe(category):
    paths = []
    # for filename in os.listdir('static\img\pane'):
    #     path = os.path.join('static\img\pane', filename)
    #     print(type(path))
    #     path = "/".join(path.split('\\'))
    #     print(path)
    #     paths.append(path)

    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    # wordForGame = sports[word][0]
    #key = word
    # print(word)
    wordDict = getDictForGame(category)
    if word == " " or word not in wordDict:
        key = random.choice(list(wordDict.keys()))
        print(key)
        wordForGame = wordDict[key][languageIndex]
        word = key
        print(word)
    else:
        wordForGame = wordDict[word][languageIndex]

    wordlist = list(wordForGame)

    scramble = {"Your word is....": " ".join(wordForGame)}

    resp = make_response(render_template('swipe.html', scramble=scramble))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)

    return resp

@bp.route("/swipe1/<category>", methods=['GET', 'POST'])
@login_required
def swipe1(category):
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    language = getTranslationLanguage(languageIndex)
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]

    if word == " ":
        wordForGame, word = getCategoryWord(category, language)
    else:
        wordForGame = findCategoryWord(word, category, language)
    location = '../static/category_models/' + category + '/' + language + '.txt'
    modelLoc = '../static/category_models/' + category
    scramble = {"Your word is....": " ".join(wordForGame)}
    print(word, wordForGame)

    resp = make_response(render_template('swipeClient.html', word=wordForGame, scramble=scramble, location=location, modelLoc=modelLoc))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)

    return resp

@bp.route("/getMorePictures/<category>", methods=['GET', 'POST'])
def getMorePictures(category):
    paths = []
    # for filename in os.listdir('static\img'):
    #     path = os.path.join('static\img', filename)
    #     print(type(path))
    #     path = "/".join(path.split('\\'))
    #     print(path)
    #     paths.append(path)
    for i in range(0, 5):
        paths.append(random.choice(["/".join(os.path.join('static/pictures/' + category, x).split("\\")) for x in os.listdir('app/static/pictures/'+ category)
                       if os.path.isfile(os.path.join('app/static/pictures/' + category, x))]))

    print(paths)

    response = {'data': paths[:]}
    return jsonify(response)

@bp.route('/image', methods=['GET','POST'])
@login_required
def image():
    return render_template("image_upload.html", scramble={})

@bp.route('/sendImage', methods=['POST', 'GET'])
def sendImage():
    image = request.files['image']
    print(image)
    image.save("foo.png")
    languageIndex = int(request.cookies.get("languageIndex"))
    language = getTranslationLanguage(languageIndex)
    #data = open('foo.png', 'rb').read()
    print(os.stat('foo.png').st_size)
    r = requests.post("https://imagenet.eyelearn.club/translateObject", files={'image1': open('foo.png', 'rb')}, data={'language': language}, verify=False)
    print(r.content)
    results = json.loads(r.content)
    print(results['predictions'])
    for result in results['predictions']:
        if check_if_word_in_table_for_user_in_class(current_user.user_id, current_user.current_class, result[1]) == []:
            newVocab = Student_Vocab(english=result[1], translation=result[0], user_id=current_user.user_id, class_id=current_user.current_class, activity_id=14)
            db.session.add(newVocab)
            db.session.commit()

    return render_template("image_upload.html", scramble={}, results=results['predictions'])


@bp.route("/findCategory/<category>", methods=['GET', 'POST'])
def findCategory(category):
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    language = getTranslationLanguage(languageIndex)
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]

    if word == " ":
        wordForGame, word = getCategoryWord(category, language)
    else:
        wordForGame = findCategoryWord(word, category, language)
    location = '../static/category_models/' + category + '/' + language + '.txt'
    modelLoc = '../static/category_models/' + category
    scramble = wordForGame
    print(scramble, word)
    print(scramble)
    resp = make_response(render_template('findCategory.html', scramble=scramble, language=language, answer=word, location=location, modelLoc=modelLoc, path="/findCategory/" + category))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp


@bp.route("/categoryImages/<category>", methods=['POST', 'GET'])
def categoryImages(category):
    f = open('app/static/category_models/' + category + '/eng.txt', "r")
    words = f.readlines()
    words = [word.strip() for word in words]
    random.shuffle(words)
    images = {}
    for word in words:
        random_index = random.randint(0, 9)
        image_results = client.images.search(query=word, count=10)
        image = image_results.value[random_index].content_url
        r = requests.head(image)
        if r.status_code != 200:
            image = image_results.value[random_index - 1].content_url
        images[word] = image
    forPrint = json.dumps(images)
    return render_template("customFindMe.html", config=images, category=category, forPrint=forPrint)

@bp.route('/printCategory/<category>', methods=['GET', 'POST']) ##use class id to find config
def printFindMeConfiguration(category):
    images = json.loads(request.form['images'])
    urls = list(images.values())
    random.shuffle(urls)

    forPrint = [urls[i:i + 4] for i in range(0, len(urls), 4)]
    if len(forPrint[-1]) != 4:
        while len(forPrint[-1]) != 4:
            forPrint[-1].append(random.choice(urls))
            
    date = datetime.datetime.now()
    date = date.strftime("%d %B %Y")
    category = category.capitalize()
    return render_template("printCustomFindMe.html", pages=forPrint, date=date, category=category)



def findCategoryWord(word, category, language):

    f = open('app/static/category_models/' + category + '/eng.txt', "r")
    words = f.readlines()
    f.close()
    print(words)
    words = [word.strip() for word in words]
    index = words.index(word)
    fname = 'app/static/category_models/' + category + '/' + language + '.txt'
    f = io.open(fname, "r", encoding='utf-8')
    foreignWords = f.readlines()[1:]
    print(foreignWords)
    f.close()
    return foreignWords[index].strip()

def getCategoryWord(category, language):
    f = io.open('app/static/category_models/' + category + '/' + language + '.txt', "r", encoding='utf-8')
    foreignWords = f.readlines()[1:]
    print(foreignWords)
    f.close()
    f = open('app/static/category_models/' + category + '/eng.txt')
    words = f.readlines()
    f.close()
    print(words)
    index = random.randint(0, len(words) - 1) #len(words)
    print(foreignWords[index].strip(), words[index].strip())
    return foreignWords[index].strip(), words[index].strip()


def getTranslationLanguage(languageIndex):
    return translationLanguage[languageIndex]

def check_if_word_in_table_for_user_in_class(user_id, class_id, word):
    return Student_Vocab.query.filter_by(user_id=user_id, class_id=class_id, english=word).all()

def getDictForGame(category):
    if category == None:
        category = random.choice(list(categories.keys()))
    return categories[category]
