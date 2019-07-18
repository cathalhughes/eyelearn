from flask import render_template, redirect, url_for, flash
from app.models import User, Class, Activity_Results
from flask_login import current_user, login_required
import json
from app.user_analytics import bp
import datetime
from get_averages import get_daily_averages
from get_average_predictions import get_user_predictions, get_class_predictions

@bp.route('/class/<classcode>', methods=['GET', 'POST'])
@login_required
def classStats(classcode):
    if not hasAccessToClass(classcode):
        flash("You do not have access to this page!")
        return redirect(url_for("user_management.user", username=current_user.username))
    selectedClass = Class.query.filter_by(class_id=classcode).first_or_404()
    studentsInClass = selectedClass.get_all_students_in_class().all()
    if studentsInClass == []:
        flash("There are no students in " + selectedClass.class_name)
        return redirect(url_for("user_management.user", username=current_user.username))
    students_with_averages, class_average = selectedClass.get_students_with_average(studentsInClass)
    if students_with_averages == None:
        flash("Your students in class " + selectedClass.class_name + " have yet to complete any tasks")
        return redirect(url_for("user_management.user", username=current_user.username))
    class_average = round(class_average)
    ranked_activities, jsonData = selectedClass.get_games_played_by_class(studentsInClass)
    activity_scores = selectedClass.get_activity_scores_in_class().all()
    #print(activity_scores[0].score, activity_scores[1].score)
    highest_activity, lowest_activity, barData = selectedClass.get_activity_averages_in_class(activity_scores)
    filename, averages = selectedClass.get_class_distribution_chart(students_with_averages)
    data = {"classcode": classcode, "data": averages}
    #print(data)
    newVocab = selectedClass.get_class_new_vocab()
    vocabData = {"english": [vocab[0].english for vocab in newVocab],
                 "translation": [vocab[0].translation for vocab in newVocab],
                 "students": [vocab[1] for vocab in newVocab]}
    daily_class_averages = selectedClass.get_class_daily_averages()
    dailyPredictionData = selectedClass.get_daily_class_prediction()
    incorrect_letters = selectedClass.get_incorrect_letters_by_students().all()
    incorrectCharacterData = {"correct": [correct.correct_letter for correct in incorrect_letters],
                              "incorrect": [incorrect.incorrect_letter for incorrect in incorrect_letters],
                              "students": [student.username for student in incorrect_letters],
                              "counts": [count.count for count in incorrect_letters]}

    misspelledWords = selectedClass.get_misspelled_words().all()
    misspelledWordsData = {"words": [word.word for word in misspelledWords],
                           "translated_words": [translated.translated_word for translated in misspelledWords],
                           "counts": [count.count for count in misspelledWords]}
    print(incorrectCharacterData)
    print(incorrect_letters)
    if dailyPredictionData != None:
        dailyPredictionData = dailyPredictionData.prediction
    print(dailyPredictionData)
    #print(daily_class_averages)
    #print(highest_activity, lowest_activity)
    #print(studentsInClass)
    return render_template("class1.html", selectedClass=selectedClass, pieData=jsonData, barData=barData, data=data, students=students_with_averages, ranked=ranked_activities, highest=highest_activity, lowest=lowest_activity, classAverage=class_average, classcode=classcode, newVocab=newVocab[:5], vocabData=vocabData, lineData=daily_class_averages, dailyPredictionData=dailyPredictionData, incorrectLetters=incorrect_letters[:5], incorrectCharacterData=incorrectCharacterData, misspelledWords=misspelledWords, misspelledWordsData=misspelledWordsData)

@bp.route('/class/<classcode>/<username>', methods=['GET', 'POST'])
@login_required
def userStats(classcode, username):
    if not hasAccess(classcode, username):
        flash("You do not have access to this page!")
        return redirect(url_for("user_management.user", username=current_user.username))
    user = User.query.filter_by(username=username).first_or_404()
    selectedClass = Class.query.filter_by(class_id=classcode).first_or_404()
    activities = user.get_activities(classcode).all()
    if activities == []:
        flash("You have not completed any activities in " + selectedClass.class_name)
        return redirect(url_for("user_management.user", username=username))
    scores = [activity.score for activity in activities]
    data = {"classcode": classcode + ", " + username, "data": scores}
    print(data)
    avg_score = user.get_student_overall_average_score(activities)
    avg_score = round(avg_score)
    ranked_activities, pieData = user.rank_activities_for_student(activities)
    highest, lowest, barData = user.get_high_low_average_activities(activities)
    studentsInClass = selectedClass.get_all_students_in_class().all()
    print(studentsInClass)
    students_with_averages, class_average = selectedClass.get_students_with_average(studentsInClass)
    print(students_with_averages)
    rank = selectedClass.get_student_rank_in_class(students_with_averages, user)
    print(rank)
    rankJson = {"data":[x[1] for x in rank[2]], "rank": rank[0], "username": user.username}
    print(activities)
    lineData = user.get_daily_average(classcode)
    newVocab = user.get_students_new_vocab(classcode).all()
    vocabData = {"english": [vocab.english for vocab in newVocab], "translation": [vocab.translation for vocab in newVocab]}
    dailyPredictionData = user.get_daily_prediction(classcode)
    incorrect_letters = user.get_incorrect_letters(classcode).all()
    incorrectCharacterData = {"correct": [correct.correct_letter for correct in incorrect_letters],
                              "incorrect": [incorrect.incorrect_letter for incorrect in incorrect_letters],
                              "counts": [count.count for count in incorrect_letters]}
    misspelledWords = user.get_misspelled_words(classcode).all()
    misspelledWordsData = {"words": [word.word for word in misspelledWords],
                           "translated_words": [translated.translated_word for translated in misspelledWords],
                           "counts": [count.count for count in misspelledWords]}

    print(incorrect_letters)
    if dailyPredictionData != None:
        dailyPredictionData = dailyPredictionData.prediction

    print()
    return render_template('userStats1.html', user=user, data=data, selectedClass=selectedClass, activities=activities, average=avg_score, ranked=ranked_activities, highest=highest, lowest=lowest, pieData=pieData, barData=barData, rank=rankJson, newVocab=newVocab[:5], vocabData=vocabData, lineData=lineData, dailyPredictionData=dailyPredictionData, incorrectLetters=incorrect_letters[:5], incorrectCharacterData=incorrectCharacterData, misspelledWords=misspelledWords, misspelledWordsData=misspelledWordsData)


@bp.route('/summary/<class_id>/<username>/<level>', methods=['GET', 'POST'])
@login_required
def summary(class_id, username, level):
    print(current_user.username, username)
    if current_user.username != username:
        flash("You do not have access to this page!")
        return redirect(url_for("user_management.user", username=current_user.username))
    level = int(level)
    stats = current_user.get_frozen_stats(level, class_id)
    print(stats)
    if stats is None:
        flash("You have yet to complete Course " + str(level) + "!")
        return redirect(url_for("user_management.user", username=current_user.username))
    date = datetime.datetime.now()
    date = date.strftime("%d %B %Y")
    print(stats.new_vocab)
    #print(json.loads(stats.new_vocab))
    print(json.loads(stats.highest))
    print(json.loads(stats.lowest))
    print(json.loads(stats.most))
    print(stats.least)
    print(json.loads(stats.problem_words))

    return render_template("courseSummary.html", class_id=class_id, date=date, user=current_user, username=username, rank=stats.rank, level=stats.level, numActivities=stats.activities_played, numNewWords=stats.num_new_words, average=stats.average, highest=json.loads(stats.highest), lowest=json.loads(stats.lowest), dailyPredictionData=stats.prediction, newVocab=json.loads(stats.new_vocab), misspelledWords=json.loads(stats.problem_words), worldRank=stats.world_rank, css=getLevelCSS(level), most=json.loads(stats.most), least=json.loads(stats.least))

@bp.route('/printSummary/<class_id>/<username>/<level>', methods=['POST'])
@login_required
def printSummary(class_id, username, level):
    print(current_user.username, username)
    if current_user.username != username:
        flash("You do not have access to this page!")
        return redirect(url_for("user_management.user", username=current_user.username))
    level = int(level)
    stats = current_user.get_frozen_stats(level, class_id)
    print(stats)
    if stats is None:
        flash("You have yet to complete Course " + str(level) + "!")
        return redirect(url_for("user_management.user", username=current_user.username))
    date = datetime.datetime.now()
    date = date.strftime("%d %B %Y")
    return render_template("printCourseSummary.html", date=date, user=current_user, username=username, rank=stats.rank, level=stats.level, numActivities=stats.activities_played, numNewWords=stats.num_new_words, average=stats.average, highest=json.loads(stats.highest), lowest=json.loads(stats.lowest), dailyPredictionData=stats.prediction, newVocab=json.loads(stats.new_vocab), misspelledWords=json.loads(stats.problem_words), worldRank=stats.world_rank, css=getLevelCSS(level), most=json.loads(stats.most), least=json.loads(stats.least))


@bp.route('/cert/<class_id>/<username>', methods=['GET', 'POST'])
@login_required
def cert(class_id, username):
    if current_user.username != username:
        flash("You do not have access to this page!")
        return redirect(url_for("user_management.user", username=current_user.username))
    user = User.query.filter_by(username=username).first()
    print(type(user.get_active_level()))
    print(user.get_active_level())
    if user.get_active_level() == 4:
        classname = Class.query.filter_by(class_id=class_id).first().class_name
        date = datetime.datetime.now()
        date = date.strftime("%d %B %Y")
        return render_template("cert.html", username=username, classname=classname, date=date)
    flash("You have not yet completed all the courses in this class!")
    return redirect(url_for("user_management.user", username=current_user.username))

def getLevelCSS(level):
    css = []
    for i in range(1, 5):
        if i <= level:
            css.append("done")
        else:
            css.append("todo")
    return css

def hasAccess(classcode, username):
    if current_user.username == username:
        return True
    if current_user.role == "Teacher":
        classes = current_user.get_teachers_classes()
        for teacherClass in classes:
            if teacherClass.class_id == classcode:
                return True
    return False

def hasAccessToClass(classcode):
    if current_user.role == "Teacher":
        classes = current_user.get_teachers_classes()
        for teacherClass in classes:
            if teacherClass.class_id == classcode:
                return True
    return False

@bp.route('/updateDailyAverages', methods=['POST'])
def updateDailyAverages():
    get_daily_averages()
    return "done"

@bp.route('/updatePredictions', methods=['POST'])
def updatePredictions():
    get_user_predictions()
    get_class_predictions()
    return "done"
