from flask import render_template, request, make_response, jsonify, url_for, flash, redirect
from app.everyday_object_classification import bp
import random
import io
import json
from azure.cognitiveservices.search.imagesearch import ImageSearchAPI
from msrest.authentication import CognitiveServicesCredentials
from app.models import Find_Me_Configurations, Class
from flask_login import current_user, login_required
from app import db
from google.cloud import translate
from html import unescape
import os
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= "translateKey.json"

translate_client = translate.Client()

subscription_key = "456aa06c006041b787e834923e7ee183"
client = ImageSearchAPI(CognitiveServicesCredentials(subscription_key))

languages = {0: "fr", 1:"es"}

f1 = open('app/static/find_model/class_names1.txt', "r")

words1 = f1.readlines()
words1 = [word.strip() for word in words1]
f1.close()

@bp.route("/find", methods=['GET', 'POST'])
@login_required
def find():
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    if word == " ":
        wordForGame, word = getWord(languageIndex)
    else:
        wordForGame = findWord(word, languageIndex)

    language = getLanguage(languageIndex)

    scramble = wordForGame
    print(scramble, word)
    print(scramble)
    resp = make_response(render_template('find.html', scramble=scramble, language=language, answer=word, path="/find"))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/createFindMeConfiguration/<class_id>', methods=['GET', 'POST'])
@login_required
def createFindMeConfiguration(class_id):
    config = Find_Me_Configurations.query.filter_by(class_id=class_id).first()
    if config is None:
        return render_template("createFindMeConfiguration.html", config={}, class_id=class_id)
    configData = json.loads(config.items)
    return render_template("createFindMeConfiguration.html", class_id=class_id, config=configData)

@bp.route('/searchForImages', methods=['POST'])
@login_required
def searchForImages():
    dataFromClient = request.get_data(as_text=True)
    data = json.loads(dataFromClient)

    search_term = data['search_term'].strip()
    image_results = client.images.search(query=search_term)
    urls = [image_result.content_url for image_result in image_results.value]
    response = {"image_urls": urls}

    return jsonify(response)

@bp.route('/saveFindMeConfiguration/<class_id>', methods=['POST'])
def saveFindMeConfiguration(class_id):
    data = request.form["config"]
    data = json.loads(data)
    print(data)
    config = Find_Me_Configurations.query.filter_by(class_id=class_id).first()
    foreignLoc, englishLoc = createTextFiles(data, class_id)
    if config is None:

        config = Find_Me_Configurations(class_id=class_id, items=json.dumps(data), eng_loc=englishLoc, for_loc=foreignLoc)
        db.session.add(config)
        db.session.commit()
        flash("You have successfully created a Find Me Configuration!")
    else:
        config.items = json.dumps(data)
        db.session.commit()
        flash("You have successfully updated a Find Me Configuration!")
    return redirect(url_for("user_management.user", username=current_user.username))

@bp.route('/displayFindMeConfiguration/<class_id>', methods=['GET', 'POST']) ##use class id to find config
def displayFindMeConfiguration(class_id):
    config = Find_Me_Configurations.query.filter_by(class_id=class_id).first()
    if config is None:
        flash("You have not created a custom 'Find Me' Configuration!")
        return redirect(url_for("user_management.user", username=current_user.username))
    configData = json.loads(config.items)
    return render_template("customFindMe.html", config=configData, class_id=class_id)

@bp.route('/printFindMeConfiguration/<class_id>', methods=['GET', 'POST']) ##use class id to find config
def printFindMeConfiguration(class_id):
    config = Find_Me_Configurations.query.filter_by(class_id=class_id).first()
    if config is None:
        flash("You have not created a custom 'Find Me' Configuration!")
        return redirect(url_for("user_management.user", username=current_user.username))
    configData = json.loads(config.items)
    urls = list(configData.values())
    random.shuffle(urls)

    forPrint = [urls[i:i + 4] for i in range(0, len(urls), 4)]
    if len(forPrint[-1]) != 4:
        while len(forPrint[-1]) != 4:
            forPrint[-1].append(random.choice(urls))

    date = datetime.datetime.now()
    date = date.strftime("%d %B %Y")
    classname = Class.query.filter_by(class_id=class_id).first().class_name
    return render_template("printCustomFindMe.html", pages=forPrint, date=date, classname=classname)

@bp.route('/findMeConfiguration', methods=['GET', 'POST'])
@login_required
def findMeConfiguration():
    classes = current_user.get_teachers_classes().all()
    if classes == []:
        flash("You currently do not have any classes!")
        return redirect(url_for("user_management.user", username=current_user.username))
    print(classes)
    return render_template('changeclass.html', user=[], classes=[], practiceAreas=[], teacherClasses=[], findMe=classes)


@bp.route("/customFind", methods=['GET', 'POST'])
@login_required
def customFind():
    config = Find_Me_Configurations.query.filter_by(class_id=current_user.current_class).first()
    if config is None:
        flash("Your teacher has yet to create a custom Find Me Configuration!")
        return redirect(url_for("main.diff"))
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    if word == " ":
        wordForGame, word = getCustomWord(config.for_loc, config.eng_loc)
    else:
        wordForGame = findCustomWord(word, config.for_loc, config.eng_loc)

    language = getLanguage(languageIndex)

    scramble = wordForGame
    print(scramble, word)
    print(scramble)
    resp = make_response(render_template('find.html', scramble=scramble, language=language, answer=word, path="/customFind"))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp


def getWord(languageIndex):
    language = getLanguage(languageIndex)
    f = io.open("app/static/find_model/class_names_" + language + "1.txt", "r", encoding='utf-8')
    foreignWords = f.readlines()
    f.close()
    f = open("app/static/find_model/class_names1.txt")
    words = f.readlines()
    f.close()
    index = random.randint(0, len(words) - 1) #len(words)
    return foreignWords[index].strip(), words[index].strip()

def getCustomWord(foreignFilename, englishFilename):
    f = io.open(foreignFilename, "r", encoding='utf-8')
    foreignWords = f.readlines()
    f.close()
    f = open(englishFilename)
    words = f.readlines()
    f.close()
    index = random.randint(0, len(words) - 1) #len(words)
    return foreignWords[index].strip(), words[index].strip()

def findWord(word, languageIndex):
    language = getLanguage(languageIndex)
    index = words1.index(word)
    fname = 'app/static/find_model/class_names_' + language +  '1.txt'


    f = io.open(fname, "r", encoding='utf-8')
    foreignWords = f.readlines()
    f.close()
    return foreignWords[index].strip()

def findCustomWord(word, foreignFilename, englishFilename):
    f = open(englishFilename, "r")
    words = f.readlines()
    f.close()
    words = [word.strip() for word in words]
    index = words.index(word)
    fname = foreignFilename
    f = io.open(fname, "r", encoding='utf-8')
    foreignWords = f.readlines()
    f.close()
    return foreignWords[index].strip()

def createTextFiles(data, class_id):
    selectedClass = Class.query.filter_by(class_id=class_id).first()
    classname = str(class_id)
    language = translateLangauge(selectedClass.language)
    words = [key for key in data.keys()]
    result = translate_client.translate(
        words, target_language=language)
    foreignWords = [unescape(res["translatedText"]) for res in result]
    englishFilename = "app/static/custom_find/" + classname + "_eng.txt"
    foreignFilename = "app/static/custom_find/" + classname + "_for.txt"
    f = open(englishFilename, "w")
    f.write("\n".join(words))
    f.close()
    f = open(foreignFilename, "w", encoding="UTF-8")
    f.write("\n".join(foreignWords))
    f.close()
    return foreignFilename, englishFilename

def translateLangauge(language):
    if language == "French":
        return "fr"
    return "es"

def getLanguage(languageIndex):

    return languages[languageIndex]

