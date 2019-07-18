from flask import Flask, request, Response, render_template, flash, redirect, url_for
from azure.cognitiveservices.search.imagesearch import ImageSearchAPI
from msrest.authentication import CognitiveServicesCredentials
import os
import urllib.request
from urllib.error import URLError, HTTPError
from PIL import Image
import subprocess
from threading import Thread
import shutil
import json
from socket import error as SocketError
import errno
import requests
from google.cloud import translate
from html import unescape
from ssl import CertificateError
import socket

socket.setdefaulttimeout(30)
from http.client import RemoteDisconnected
import tensorflow as tf

app = Flask(__name__)
app.secret_key = "MY_SECRET_KEY"

subscription_key = "456aa06c006041b787e834923e7ee183"
client = ImageSearchAPI(CognitiveServicesCredentials(subscription_key))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "translateKey.json"

translate_client = translate.Client()

languages = {"French": "fr", "Spanish": "es"}


@app.route('/trainModel', methods=['GET', 'POST'])
def trainModel():
    print("here")
    data = request.get_data(as_text=True)
    data = json.loads(data)
    category_name = data['category']
    search_terms = data['items']
    class_name = data['classname']
    user_id = data["user_id"]
    language = data['language']
    language = languages[language]
    Thread(target=downloadImagesAndTrainClassifier,
           args=(category_name, search_terms, class_name, user_id, language,)).start()
    return "We will notify you when your model is trained!"


def downloadImagesAndTrainClassifier(category_name, search_terms, class_name, user_id, language):
    print(category_name, search_terms)
    category_name = "_".join(category_name.split(" "))
    if not os.path.exists(category_name + "_images"):
        os.makedirs(category_name + "_images")

    print("querying Api")
    dict = queryApi(search_terms)

    print("getting urls")
    dict = getUrlsForImages(dict)

    print("starting download")
    downloadImages(dict, category_name)

    print("deleting broken images")
    removeBrokenImages(category_name + "_images/")

    print("deleting broken images with tf")
    removeBrokenImagesUsingTf(category_name + "_images/")

    print("starting training")
    output_dir = train(category_name + "_images", category_name)

    print("converting model")
    convertModelToTfjs(output_dir, category_name, class_name, language)

    print("get Images for client")
    getImagesForClient(category_name + "_images/", category_name, output_dir + "/" + category_name + "_" + class_name + "_saved_model_web/")

    print("transfer files")
    transferFiles(output_dir + "/" + category_name + "_" + class_name + "_saved_model_web/")

    print("sending completion notification")
    sendCompletionData(category_name, class_name, user_id)


def queryApi(search_terms):
    dict = {}
    for search_term in search_terms:
        offset = 0
        results = []
        while len(results) < 100:
            image_results = client.images.search(query=search_term, offset=offset, count=100)

            results += image_results.value
            print(len(results))
            offset += 100
        dict[search_term] = results
    return dict


def getUrlsForImages(dict):
    for key in dict.keys():
        urls = []
        for url in dict[key]:
            if int(url.content_size.split()[0]) / 1000000 < 4:  # less than 4mb
                if not url.content_url.endswith('.gif'):
                    urls.append(url.content_url)
        dict[key] = urls
    return dict


def downloadImages(dict, category_name):
    for key in dict.keys():
        keyFile = "_".join(key.split())
        if not os.path.exists(category_name + "_images/" + keyFile):
            os.makedirs(category_name + "_images/" + keyFile)
        print(key)
        count = 0

        for url in dict[key]:
            try:
                urllib.request.urlretrieve(url, category_name + "_images/" + keyFile + '/' + keyFile + '_' + str(
                    count) + '.jpg')
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
    for key in os.listdir(dir):
        files = os.listdir(dir + key)
        print(files)
        for file in files:
            try:
                img = Image.open(dir + key + '/' + file)
                img.verify()
            except (IOError, SyntaxError) as e:
                os.remove(dir + key + '/' + file)


def removeBrokenImagesUsingTf(dir):
    for key in os.listdir(dir):
        files = os.listdir(dir + key)
        print(files)
        for file in files:
            try:
                image_string = tf.gfile.FastGFile(dir + key + '/' + file, 'rb').read()
                with tf.Session() as sess:
                    sess.run(tf.image.decode_jpeg(image_string, channels=3))
            except tf.errors.InvalidArgumentError as e:
                os.remove(dir + key + '/' + file)
                print("REMOVED-----------------------")


def train(images_dir, category_name):
    output = category_name + "_output"
    if not os.path.exists(output):
        os.makedirs(output)

    cmd = 'python3 retrain.py --image_dir  ./' + images_dir + ' --how_many_training_steps=4000 --eval_step_interval=100 --architecture mobilenet_0.25_224 --output_graph ./' + output + '/graph.pb --summaries_dir ./' + output + '/summaries --output_labels ./' + output + '/output_labels.txt --bottleneck_dir ./' + output + '/bottleneck/ --intermediate_store_frequency 1000 --intermediate_output_graphs_dir ./' + output + '/intermediate --saved_model_dir ./' + output + '/saved_model'

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    return output


def convertModelToTfjs(model_loc, category, class_name, language):
    cmd = "python3 -m tensorflowjs.converters.converter --input_format=tf_saved_model --output_node_names='final_result' --saved_model_tags=serve " + model_loc + "/saved_model/ " + model_loc + "/" + category + "_" + class_name + "_saved_model_web/"

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    translateLabels(model_loc + '/output_labels.txt',
                    model_loc + '/' + category + '_' + class_name + '_saved_model_web/for_labels.txt', language,
                    category)

    newPath = shutil.copy(model_loc + '/output_labels.txt',
                          model_loc + '/' + category + '_' + class_name + '_saved_model_web')


def translateLabels(output_loc, for_loc, language, category):
    f = open(output_loc, "r")
    lines = f.readlines()
    f.close()
    lines = [line.strip() for line in lines]
    lines = [category.strip()] + lines
    result = translate_client.translate(
        lines, target_language=language)
    f = open(for_loc, "w")
    results = [unescape(res['translatedText']) for res in result]
    f.write("\n".join(results))
    f.write("\n")
    f.close()


def getImagesForClient(dir, category_name, saved_model_dir):
    output = saved_model_dir
    if not os.path.exists(output + "/images"):
        os.makedirs(output + "/images")
    for key in os.listdir(dir):
        files = os.listdir(dir + key)
        print(files)
        for i in range(1, 10):
            f = dir + key + "/" + files[i]
            shutil.copy(f, output + "/images")


def transferFiles(loc):
    cmd = "scp -i key.pem -r " + loc + " rsa-key-20190215@35.196.192.111:~/eyelearn-frontend/app/static/models"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()


def sendCompletionData(category, class_name, user_id):
    model_path = "static/models/" + category + "_" + class_name + "_saved_model_web"
    data = {'class_id': class_name,
            'model_path': model_path,
            'user_id': user_id,
            'category': category}
    data = json.dumps(data)
    print("done")
    requests.post('https://eyelearn.club/finishedTraining', data=data)

#app.run(port=5002)

# transferFiles()