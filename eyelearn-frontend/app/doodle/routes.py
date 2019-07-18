from flask import render_template, request, make_response, redirect, url_for, flash
from app.doodle import bp
import random
import io
import re
import base64
import json
from flask_login import login_user, logout_user, current_user, login_required
import time
from app.models import Doodles, Class_Doodles, Student_Doodles
from app import db
import os
from google.cloud import translate
from html import unescape
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="translateKey.json"

translate_client = translate.Client()

languages = {0: "fr", 1:"es"}

f1 = open('app/static/model1/class_names1.txt', "r")
words1 = f1.readlines()
words1 = [word.strip() for word in words1]
f1.close()

f2 = open('app/static/model2/class_names1.txt', "r")
words2 = f2.readlines()
words2 = [word.strip() for word in words2]
f2.close()

f3 = open('app/static/model3/class_names.txt', "r")
words3 = f3.readlines()
words3 = [word.strip() for word in words3]
f3.close()

f4 = open('app/static/model4/class_names.txt', "r")
words4 = f4.readlines()
words4 = [word.strip() for word in words4]
f4.close()




#f1 = open('static/model3/class_names.txt', "r")

@bp.route("/doodle", methods=['GET', 'POST'])
@login_required
def doodle():
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    languageIndex = int(request.cookies.get("languageIndex"))
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    if word == " ":
        randomModel = random.randint(1,2)
        wordForGame, word = getWordForDoodle(languageIndex, randomModel)
    else:
        wordForGame, randomModel = findWordForDoodle(word, languageIndex)

    language = getLanguage(languageIndex)


    scramble = wordForGame
    print(scramble, word)

    resp = make_response(render_template('gameview.html', scramble=scramble, model=str(randomModel), language=language, answer=word))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp

@bp.route('/saveDoodle', methods=['POST'])
def saveDoodle():
    imgPost = request.get_data(as_text=True)
    data = json.loads(imgPost)

    foreignGuess = data['guess'].strip()
    translated, model = findWordForDoodle(data['answer'].strip(), 0)
    foreignAnswer = translated

    filename = convertDoodleImage(data['doodle'], current_user.username)
    doodle = Doodles(foreign_answer=foreignAnswer, foreign_guess=foreignGuess, location=filename)
    db.session.add(doodle)
    db.session.commit()
    student_doodle = Student_Doodles(user_id=current_user.user_id, doodle_id=doodle.doodle_id)
    class_doodle = Class_Doodles(class_id=current_user.current_class, doodle_id=doodle.doodle_id)
    db.session.add_all([student_doodle, class_doodle])
    db.session.commit()
    return "saved"

@bp.route('/viewDoodles')
def viewDoodles():
    userDoodles = current_user.get_doodles().all()
    if userDoodles == []:
        flash("You have not yet completed any doodles in this class yet!")
        return redirect(url_for('user_management.user', username=current_user.username))
    translations = [[doodle.foreign_answer, doodle.foreign_guess] for doodle in userDoodles]
    translations = get_translation(translations)
    canPrint = len(userDoodles) > 3
    print(translations)
    return render_template("doodlegall1.html",  doodles=zip(userDoodles, translations), doodles1=userDoodles, doodles2=userDoodles, canPrint=canPrint)

@bp.route('/printDoodles', methods=['POST'])
def printDoodles():
    userDoodles = current_user.get_doodles().all()
    if userDoodles == []:
        flash("You have not yet completed any doodles in this class yet!")
        return redirect(url_for('user_management.user', username=current_user.username))
    while (len(userDoodles) % 4 != 0):
        userDoodles.pop()
    if userDoodles == []:
        flash("You have not yet completed enough doodles!")
        return redirect(url_for('user_management.user', username=current_user.username))
    translations = [[doodle.foreign_answer, doodle.foreign_guess] for doodle in userDoodles]
    translations = get_translation(translations)

    userDoodles = list(zip(*[iter(userDoodles)] * 4))
    translations = list(zip(*[iter(translations)] * 4))



    date = datetime.datetime.now()
    date = date.strftime("%d %B %Y")
    return render_template("printDoodleGallery.html",  username=current_user.username, date=date, doodlePages=zip(userDoodles, translations))

def get_translation(foreignList):
    englishList = []
    for foreign in foreignList:
        result = translate_client.translate(
            foreign, target_language="en")
        english = []
        for res in result:
            english.append(res['translatedText'])
        englishList.append(english)
    return englishList

def convertDoodleImage(imgData, username):
    imgStr = re.search(r'base64,(.*)',imgData)
    if imgStr != None:
        imgStr = imgStr.group(1)
    else:
        imgStr = imgData

    #print(imgStr)
    filename = 'doodles/' + str(username) + time.strftime("%Y%m%d-%H%M%S") + ".png"
    with open('app/static/' + filename,'wb') as output:
        output.write(base64.b64decode(imgStr))

    return filename

def getWordForDoodle(languageIndex, randomModel):
    language = getLanguage(languageIndex)
    f = io.open("app/static/model" + str(randomModel) + "/class_names_" + language + "1.txt", "r", encoding='utf-8')
    foreignWords = f.readlines()
    f.close()
    f = open("app/static/model" + str(randomModel) + "/class_names1.txt")
    words = f.readlines()
    f.close()
    index = random.randint(0,len(words) - 1)
    return " ".join(foreignWords[index].strip().split("_")), " ".join(words[index].strip().split("_"))

def findWordForDoodle(word, languageIndex):
    word = "_".join(word.split())
    language = getLanguage(languageIndex)
    if word in words1:
        index = words1.index(word)
        fname = 'app/static/model1/class_names_' + language +  '1.txt'
        model = 1
    elif word in words2:
        index = words2.index(word)
        fname = 'app/static/model2/class_names_' + language + '1.txt'
        model = 2
    elif word in words3:
        index = words3.index(word)
        fname = 'app/static/model3/class_names_' + language + '.txt'
        model = 3
    else:
        index = words4.index(word)
        fname = 'app/static/model4/class_names_' + language + '.txt'
        model = 4
    f = io.open(fname, "r", encoding='utf-8')
    foreignWords = f.readlines()
    f.close()
    return " ".join(foreignWords[index].strip().split("_")), model


def getLanguage(languageIndex):

    return languages[languageIndex]

