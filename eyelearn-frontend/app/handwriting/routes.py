from flask import render_template, redirect, url_for, flash, request, make_response
from app import db
from app.models import Incorrect_Character, Class
from flask_login import login_user, logout_user, current_user, login_required
from app.handwriting import bp
import random
from app.utils import checkForIncorrectCharacters

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

@bp.route('/numbersOrSpelling', methods=['POST', 'GET'])
@login_required
def numbersOrSpelling() :
    word = request.cookies.get('word')
    #print(word)
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]

    print("here")
    if word == " ":
        word = random.choice(list(allVocab.keys()))

        #listlength = len(spellingWords)
        #word = spellingWords[random.randrange(0, listlength)]

    wordForGame = allVocab[word][languageIndex]
    wordlist = list(word)

    scrwordlist = wordlist


    scrword = " "

    for i in range(0, len(scrwordlist)):
        scrword = (scrword + scrwordlist[i] + " ")
    print(scrword, word)
    scramble = {"Your word is....": scrword}
    userClass = Class.query.filter_by(class_id=current_user.current_class).first_or_404()
    classLanguage = userClass.get_language()
    resp = make_response(render_template('handwriting.html', scramble=scramble, language=classLanguage))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp


@bp.route('/numbers', methods=['POST', 'GET'])
@login_required
def numbers():
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    if word == " ":
        #listlength = len(numbers)
        print("new Number")
        word = random.choice(list(numbersDict.keys()))
        print(word)

        #word = key

    word = int(word)
    wordForGame = numbersDict[word][languageIndex]
    wordlist = list(wordForGame)

    scrwordlist = wordlist

    scrword = " "

    for i in range(0, len(scrwordlist)):
        scrword = (scrword + scrwordlist[i] + " ")
    print(scrword, word)
    scramble = {"Your number is....": scrword}

    resp = make_response(render_template('numbers.html', scramble=scramble))
    resp.set_cookie('word', str(word))
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/checkWord',methods=['POST', 'GET'])
def checkWord():
    guess = request.form['guess']
    print(guess + "--------------------")
    word = request.cookies.get('word')
    languageIndex = int(request.cookies.get("languageIndex"))

    print(guess, word)
    guess = guess.lower()
    word = allVocab[word][languageIndex]
    # if guess not in fr:
    #     return render_template('incorrect.html', score=[0,0])
    # guess = fr[guess]
    if guess == word or guess == (word+" "):
        return render_template('correct.html',score=[0,0])
    else:
        print("in here")
        checkForIncorrectCharacters(guess, word)

        return render_template('incorrect.html', score=[0,0])


@bp.route('/checkNumber', methods=['POST','GET'])
def checkNumber():
    guess = request.form['jsonval']
    print(guess + "--------------------")
    word = request.cookies.get('word')
    print(guess, word)
    guess = guess.lower()
    guess = int(guess)
    if guess not in numbersDict:
        return render_template('incorrect.html', score=[0,0])
    guess = numbersDict[guess]
    if word in guess:
        return render_template('correct.html', score=[0,0])
    else:
        print("in here")
        return render_template('incorrect.html', score=[0,0])
