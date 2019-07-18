from flask import render_template, request, make_response,jsonify, redirect, url_for, flash
from app.tiles import bp
from app.models import User
from flask_login import current_user, login_required
import random


@bp.route("/tiles", methods=['GET', 'POST'])
@login_required
def tiles():
    newVocab = current_user.get_students_new_vocab(current_user.current_class).all()
    if newVocab == []:
        flash('You have not learned any new words yet!')
        return redirect(url_for('main.diff'))
    return render_template("tiles.html")

@bp.route("/tilesGame", methods=['GET', 'POST'])
@login_required
def tilesGame():
    newVocab = current_user.get_students_new_vocab(current_user.current_class).all()[:30]
    if newVocab == []:
        flash('You have not learned any new words yet!')
        return redirect(url_for('main.diff'))
    english = [vocab.english for vocab in newVocab]
    translation = [vocab.translation for vocab in newVocab]
    word = request.cookies.get('word')
    active_activity = request.cookies.get("activity_id")
    if active_activity != "":
        activity_id = active_activity
    else:
        print("from form")
        activity_id = request.form["activity_id"]
    print(active_activity, activity_id)
    print(word)
    if word == " ":
        randomNumber = random.randint(0, len(translation) - 1)

        word = english[randomNumber]
        # wordForGame = english[randomNumber]
    else:
        index = translation.index(word)
        wordForGame = english[index]


    scramble = {"Your word is....": word}

    resp = make_response(render_template('tilesgame.html', scramble=scramble))
    resp.set_cookie('word', word)
    resp.set_cookie('activity_id', activity_id)
    return resp



@bp.route("/getWordsForTiles")
def getWordsForTiles():
    newVocab = current_user.get_students_new_vocab(current_user.current_class).all()
    vocabData = {"english": [vocab.english for vocab in newVocab],
                 "translation": [vocab.translation for vocab in newVocab]}
    return jsonify(vocabData)

