from flask import render_template, request, make_response, redirect, url_for, flash, send_from_directory, jsonify
from app.doodle import bp
import random
import io
from app.models import Task, User_Task, Class, Class_Model, Model
import json
from flask_login import login_user, logout_user, current_user, login_required
from app import db
import os
from PIL import Image
from socket import error as SocketError
import errno
import requests
from ssl import CertificateError
import socket
socket.setdefaulttimeout(30)
from http.client import RemoteDisconnected
import urllib.request
from urllib.error import URLError, HTTPError
import random
from threading import Thread

from azure.cognitiveservices.search.imagesearch import ImageSearchAPI
from msrest.authentication import CognitiveServicesCredentials
import datetime
subscription_key = "456aa06c006041b787e834923e7ee183"
client = ImageSearchAPI(CognitiveServicesCredentials(subscription_key))

languages = {"French":"fr", "Spanish":"es"}

@bp.route("/sendDataForTraining", methods=['POST'])
@login_required
def sendDataForTraining():
    data = request.form['data']
    data = json.loads(data)
    data["user_id"] = current_user.user_id
    class_id = data['classname']
    classLanguage = Class.query.filter_by(class_id=class_id).first().language
    data['language'] = classLanguage
    ##table entry for user fro create classifier.
    # task = current_user.get_task_in_progress()
    # if task is not None:
    #     flash("You currently have a model training. A user can only train one model at a time.")
    #     return redirect(url_for('user_management.user', username=current_user.username))

    print(data)
    task = Task()
    db.session.add(task)
    db.session.commit()
    user_task = User_Task(user_id=current_user.user_id, task_id=task.task_id)
    db.session.add(user_task)
    db.session.commit()
    r = requests.post("https://create.eyelearn.club/trainModel", data=json.dumps(data))
    response = r.content.decode("utf-8")
    flash(response)
    # r = requests.post("http://127.0.0.1:5002/trainModel", data=json.dumps(data))
    # response = r.content.decode("utf-8")
    # flash(response)
    return redirect(url_for('user_management.user', username=current_user.username))

@bp.route("/finishedTraining", methods=['POST'])
def finishedTraining():
    ##store model location in db
    ##add to models table
    data = request.get_data(as_text=True)
    data = json.loads(data)
    user_id = data['user_id']
    class_id = data['class_id']
    model_loc = data['model_path']
    category = data['category']
    task_id = User_Task.query.filter_by(user_id=user_id).first().task_id
    task = Task.query.filter_by(task_id=task_id).first()
    task.complete = True
    db.session.commit()
    model = Model(model_loc=model_loc, eng_loc=model_loc + '/output_labels.txt', for_loc=model_loc + '/for_labels.txt', category=category)
    db.session.add(model)
    db.session.commit()
    class_model = Class_Model(class_id=class_id, model_id=model.model_id)
    db.session.add(class_model)
    db.session.commit()

    return "Model Stored in DB"

@bp.route('/customGame/<class_id>/<category>', methods=['POST', 'GET']) ##/<class_id>/<category>
def customGame(class_id, category):
    if current_user.current_class != class_id:
        flash("You do not have access to this page!")
        return redirect(url_for("main.diff"))
    selectedClass = Class.query.filter_by(class_id=class_id).first()
    customGame = selectedClass.check_for_custom_game(category)
    if customGame is None:
        flash("Your teacher has not yet created this game!")
        return redirect(url_for("main.diff"))
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    print(active_activity)
    #languageIndex = int(request.cookies.get("languageIndex"))
    language = languages[selectedClass.language]
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    dir = customGame.model_loc
    print(dir)
    print(dir)
    if word == " ":
        wordForGame, word = getCustomGameWord(category, class_id)
    else:
        wordForGame = findCustomGameWord(word, category, class_id)
    dir = "../../" + customGame.model_loc
    print(dir)
    location = dir + '/for_labels.txt'
    modelLoc = dir
    scramble = wordForGame
    print(scramble, word)
    print(scramble)
    resp = make_response(
        render_template('findCategory.html', scramble=scramble, language=language, answer=word, location=location,
                        modelLoc=modelLoc, path="/customGame/" + class_id + '/' + category))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)

    return resp


@bp.route("/customGameImages/<class_id>/<category>", methods=['POST', 'GET'])
def customGameImages(class_id, category):
    #if current_user.current_class != class_id:
     #   flash("You do not have access to this page!")
      #  return redirect(url_for("main.diff"))
    selectedClass = Class.query.filter_by(class_id=class_id).first()
    customGame = selectedClass.check_for_custom_game(category)
    if customGame is None:
        flash("Your teacher has not yet created this game!")
        return redirect(url_for("user_management.user", username=current_user.username))
    f = open('app/' + customGame.eng_loc, "r")
    words = f.readlines()
    f.close()
    words = [word.strip() for word in words]
    random.shuffle(words)
    images = {}
    print(category)
    for word in words:
        random_index = random.randint(0, 9)
        image_results = client.images.search(query=word, count=10)
        image = image_results.value[random_index].content_url
        r = requests.head(image)
        if r.status_code != 200:
            image = image_results.value[random_index - 1].content_url
        images[word] = image
    forPrint = json.dumps(images)
    return render_template("customFindMe.html", config=images, category=category, forPrint=forPrint, custom=True, class_id=class_id)


@bp.route('/printCustomGamesImages/<class_id>/<category>', methods=['GET', 'POST'])  ##use class id to find config
def printCustomGamesImages(category, class_id):
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
    classname = Class.query.filter_by(class_id=class_id).first().class_name
    return render_template("printCustomGame.html", pages=forPrint, date=date, category=category, classname=classname)

@bp.route('/customSwipeGame/<class_id>/<category>', methods=['POST', 'GET']) ##/<class_id>/<category>
def customSwipeGame(class_id, category):
    if current_user.current_class != class_id:
        flash("You do not have access to this page!")
        return redirect(url_for("main.diff"))
    selectedClass = Class.query.filter_by(class_id=class_id).first()
    customGame = selectedClass.check_for_custom_game(category)
    if customGame is None:
        flash("Your teacher has not yet created this game!")
        return redirect(url_for("main.diff"))
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    if active_activity != "":
        activity_id = active_activity
    else:
        activity_id = request.form["activity_id"]
    dir = customGame.model_loc
    print(dir)
    print(dir)
    if word == " ":
        wordForGame, word = getCustomGameWord(category, class_id)
    else:
        wordForGame = findCustomGameWord(word, category, class_id)
    dir = "../../" + customGame.model_loc
    print(dir)
    location = dir + '/for_labels.txt'
    modelLoc = dir
    scramble = {"Your word is....": " ".join(wordForGame)}
    print(scramble, word)
    print(scramble)
    resp = make_response(render_template('swipeClient.html', scramble=scramble, location=location, modelLoc=modelLoc, class_id=class_id, category=category, word=wordForGame))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)

    return resp

@bp.route('/getImages/<class_id>/<category>')
def getImages(class_id, category):
    paths = []
    for i in range(0, 5):
        paths.append(random.choice(["/".join(os.path.join('static/models/' + category + "_" + class_id + "_saved_model_web/images", x).split("\\")) for x in os.listdir('app/static/models/' + category + "_" + class_id + "_saved_model_web/images")
                       if os.path.isfile(os.path.join('app/static/models/' + category + "_" + class_id + "_saved_model_web/images", x))]))
    print(paths)
    response = {'data': paths[:]}
    return jsonify(response)

def findCustomGameWord(word, category, class_id):

    f = open('app/static/models/' + category + '_' + class_id + '_saved_model_web' '/output_labels.txt', "r")
    words = f.readlines()
    f.close()
    print(words)
    words = [word.strip() for word in words]
    index = words.index(word)
    fname = 'app/static/models/' + category + '_' + class_id + '_saved_model_web' '/for_labels.txt'
    f = io.open(fname, "r", encoding='utf-8')
    foreignWords = f.readlines()[1:]
    print(foreignWords)
    f.close()
    return foreignWords[index].strip()

def getCustomGameWord(category, class_id):
    f = io.open('app/static/models/' + category + '_' + class_id + '_saved_model_web' '/for_labels.txt', "r", encoding='utf-8')
    foreignWords = f.readlines()[1:]
    print(foreignWords)
    f.close()
    f = open('app/static/models/' + category + '_' + class_id + '_saved_model_web' '/output_labels.txt')
    words = f.readlines()
    f.close()
    print(words)
    index = random.randint(0, len(words) - 1) #len(words)
    print(foreignWords[index].strip(), words[index].strip())
    return foreignWords[index].strip(), words[index].strip()

@bp.route("/updateImages")
def updateImages():
    Thread(target=updateImagesForSwipe).start()
    return "Downloading Commenced"

def updateImagesForSwipe():
    models = os.listdir('app/static/models')
    for model in models:
        print("next folder")
        if not os.path.exists('app/static/models/' + model + "/images"):
            os.makedirs('app/static/models/' + model + "/images")
        else:
            deleteImages('app/static/models/' + model + "/images")
        f = open('app/static/models/' + model + "/output_labels.txt")
        words = f.readlines()
        f.close()
        words = [word.strip() for word in words]
        image_dict = queryApi(words)

        image_dict = getUrlsForImages(image_dict)
        urls = shuffleUrls(image_dict)
        downloadImages(urls, 'app/static/models/' + model + "/images")
        removeBrokenImages('app/static/models/' + model + "/images")


    print("done")

def deleteImages(path):
    for the_file in os.listdir(path):
        file_path = os.path.join(path, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

def shuffleUrls(dict):
    urls = []
    for key in dict:
        urls += dict[key]
        random.shuffle(urls)

    return urls


def queryApi(search_terms):
    dict = {}
    for search_term in search_terms:
        offset = 0
        results = []
        while len(results) < 10:
            image_results = client.images.search(query=search_term, offset=offset, count=10)

            results += image_results.value
            print(len(results))
            offset += 10
        dict[search_term] = results
    return dict

def getUrlsForImages(dict):
    for key in dict.keys():
        urls = []
        for url in dict[key]:
            if int(url.content_size.split()[0]) / 1000000 < 4: #less than 4mb
                if not url.content_url.endswith('.gif'):
                    urls.append(url.content_url)
        dict[key] = urls
    return dict

def downloadImages(urls, folder):
    count = 0
    print(urls)
    for url in urls:
        try:
            urllib.request.urlretrieve(url, folder + "/image_" + str(count) + '.jpg')
        except (URLError, HTTPError, CertificateError, RemoteDisconnected) as error:
            continue
        except socket.timeout as e:
            continue
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise  # Not error we are looking for
            continue
        count += 1
        print(count)

def removeBrokenImages(dir):
    files = os.listdir(dir)
    print(files)
    for file in files:
        try:
            img = Image.open(dir + '/' + file)
            img.verify()
        except (IOError, SyntaxError) as e:
            os.remove(dir + '/' + file)