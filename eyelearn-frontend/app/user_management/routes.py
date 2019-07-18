from flask import render_template, redirect, url_for, flash, request
from app import db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateClassForm, JoinClassForm
from app.models import User, Teacher_Class, Class, Student_Class, Class_Configs, Student_Class_Level, Student_Vocab, Find_Me_Configurations
from flask_login import login_user, logout_user, current_user, login_required
from app.user_management import bp
import secrets
import json
from google.cloud import translate
import os
from html import unescape

langDict = {"French": "fr", "Spanish":"es"}

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="translateKey.json"

translate_client = translate.Client()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('user_management.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('user_management.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        print(form.is_teacher.data)
        user = User(username=form.username.data, email=form.email.data)
        if form.is_teacher.data:
            user.role = "Teacher"
        else:
            user.role = "Student"
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.index'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/user/<username>', methods=['POST', 'GET'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_class = Class.query.filter_by(class_id=current_user.current_class).first()
    if user.role == "Student":
        # activities = user.get_activities().all()
        # avg_score = user.get_student_overall_average_score(activities)
        # ranked_activities, pieData = user.rank_activities_for_student(activities)
        # highest, lowest, barData = user.get_high_low_average_activities(activities)
        # print(activities)
        classes = user.get_student_classes().all()
        practiceAreas = user.get_user_practice_areas().all()
        selectedClass = Class.query.filter_by(class_id=current_user.current_class).first()
        customGames = selectedClass.get_custom_games()
        return render_template('user.html', user=user, classes=classes, practiceAreas=practiceAreas, current_class=current_class, customGames=customGames)
        #return render_template('user.html', user=user, activities=activities, average=avg_score, ranked=ranked_activities, highest=highest, lowest=lowest, pieData=pieData, barData=barData)
    else:
        classes = user.get_teachers_classes().all()
        classCustoms = {}
        for classx in classes:
            classCustoms[classx] = classx.get_custom_games()
        practiceAreas = user.get_user_practice_areas().all()
        configs = [] ## Todo get find me configs
        for classname in classes:
            config = Find_Me_Configurations.query.filter_by(class_id=classname.class_id).first()
            if config is not None:
                configs.append(classname)
        customs = []
        for custom in list(classCustoms.values()):
            customs += custom
        print(customs)
        return render_template('teacher.html', user=user, classes=classes, practiceAreas=practiceAreas, configs=configs, current_class=current_class, modalClasses=classes, classCustoms=classCustoms, customs=customs)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user_management.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/createpracticearea', methods=['GET', 'POST'])
def createPracticeArea():
    form = CreateClassForm()
    if form.validate_on_submit():
        print(type(form.class_id.data), type(form.name.data), type(form.year.data))
        newClass = Class(form.class_id.data, form.name.data, form.year.data, form.language.data, "Practice")
        db.session.add(newClass)
        db.session.commit()
        current_user.current_class = newClass.class_id
        student_class = Student_Class(current_user.user_id, newClass.class_id)
        db.session.add(student_class)
        db.session.commit()
        flash('You have successfully created a practice area.')
        return redirect(url_for('main.index', username=current_user.username))
    elif request.method == 'GET':
        form.class_id.data = current_user.username + "-PracticeArea"
        form.name.data = current_user.username + "'s " + "Practice Area"
    return render_template('createclass.html', title='Create a Practice Area',
                           form=form)


@bp.route('/createclass', methods=['GET', 'POST'])
@login_required
def createClass():
    form = CreateClassForm()
    if form.validate_on_submit():
        print(type(form.class_id.data), type(form.name.data), type(form.year.data))
        newClass = Class(form.class_id.data, form.name.data, form.year.data, form.language.data, "Class")
        db.session.add(newClass)
        db.session.commit()
        teacher_class = Teacher_Class(current_user.user_id, newClass.class_id)
        db.session.add(teacher_class)
        db.session.commit()
        flash('You have successfully created a new class, you now must create a configuration for it.')
        return redirect(url_for('user_management.createClassConfiguration', class_id=newClass.class_id))
    elif request.method == 'GET':
        form.class_id.data = secrets.token_hex(6)
    return render_template('createclass.html', title='Create a Class',
                           form=form)

@bp.route('/classconfig/<class_id>', methods=['GET', 'POST'])
@login_required
def createClassConfiguration(class_id):
    config = Class_Configs.query.filter_by(class_id=class_id).first()
    if config is None:
        return render_template("classconfig.html", config={}, class_id=class_id)
    else:
        configData = {'layout': json.loads(config.layout_data), 'data': json.loads(config.vocab_data), 'unlock_data': json.loads(config.unlock_data)}
        print(configData)
        return render_template("classconfig.html", config=configData, class_id=class_id)


@bp.route('/processConfiguration/<class_id>', methods=['GET', 'POST'])
@login_required
def processConfiguration(class_id):
    data = request.form["config"]
    data = json.loads(data)
    language = Class.query.filter_by(class_id=class_id).first().language
    data['data'] = get_translation(data['data'], language) #new
    config = Class_Configs.query.filter_by(class_id=class_id).first()
    if config is None:
        classConfig = Class_Configs(class_id=class_id, layout_data=json.dumps(data['layout']), vocab_data=json.dumps(data['data']), unlock_data=json.dumps(data['unlock_data']))
        db.session.add(classConfig)
        db.session.commit()
        flash("You have successfully created a configuration for class: " + class_id)
        return redirect(url_for('user_management.user', username=current_user.username))
    else:
        config.layout_data = json.dumps(data['layout'])
        config.vocab_data = json.dumps(data['data'])
        config.unlock_data = json.dumps(data['unlock_data'])
        db.session.commit()
        updateVocabForStudentsInClass(class_id, data['data']) #new
        flash("You have successfully updated the configuration for class: " + class_id)
        return redirect(url_for('user_management.user', username=current_user.username))


def updateVocabForStudentsInClass(class_id, vocab_data):
    selectedClass = Class.query.filter_by(class_id=class_id).first()
    studentsInClass = selectedClass.get_all_students_in_class().all()
    for student in studentsInClass:
        for key in vocab_data:
            for english in vocab_data[key]:

                if check_if_word_in_table_for_user_in_class(student.user_id, class_id, english) == []:
                    newVocab = Student_Vocab(english=english, translation=vocab_data[key][english],
                                             user_id=student.user_id,
                                             class_id=class_id, activity_id=14)
                    db.session.add(newVocab)
                    db.session.commit()

def updateVocabForStudentInClass(class_id):
    config = Class_Configs.query.filter_by(class_id=class_id).first()
    data = json.loads(config.vocab_data)
    print(data)
    for key in data:
        for english in data[key]:

            if check_if_word_in_table_for_user_in_class(current_user.user_id, class_id, english) == []:
                newVocab = Student_Vocab(english=english, translation=data[key][english], user_id=current_user.user_id,
                                         class_id=class_id, activity_id=14)
                db.session.add(newVocab)
                db.session.commit()

def check_if_word_in_table_for_user_in_class(user_id, class_id, word):
    return Student_Vocab.query.filter_by(user_id=user_id, class_id=class_id, english=word).all()

def get_translation(dict, language):
    language = get_translation_language_key(language)
    for key in dict:
        wordList = dict[key]
        print(wordList)
        result = translate_client.translate(
            wordList, target_language=language)
        translation_dict = {}
        for res in result:
            translation_dict[res['input']] = unescape(res['translatedText'])
        dict[key] = translation_dict
    return dict

@bp.route('/updateConfiguration', methods=['GET', 'POST'])
@login_required
def updateClassConfiguration():
    classes = current_user.get_teachers_classes().all()
    print(classes)
    return render_template('changeclass.html', user=user, classes=[], practiceAreas=[], teacherClasses=classes)

@bp.route('/joinclass', methods=['GET', 'POST'])
@login_required
def joinClass():
    form = JoinClassForm()
    if form.validate_on_submit():
        #print(type(form.class_id.data))
        student_class = Student_Class(current_user.user_id, form.class_id.data)
        student_class_level = Student_Class_Level(user_id=current_user.user_id, class_id=form.class_id.data, level=1) ##new
        current_user.current_class = form.class_id.data
        db.session.add(student_class)
        db.session.add(student_class_level)
        db.session.commit()
        updateVocabForStudentInClass(current_user.current_class) #new
        flash('You have successfully joined a class.')
        return redirect(url_for('user_management.user', username=current_user.username))
    return render_template('joinclass.html', title='Join a Class',
                           form=form)

@bp.route('/changeclass', methods=['GET', 'POST'])
@login_required
def changeClass():
    if current_user.role == "Student":
        classes = current_user.get_student_classes().all()
        practiceAreas = current_user.get_user_practice_areas().all()
        return render_template('changeclass.html', user=user, classes=classes, practiceAreas=practiceAreas)
    else:
        practiceAreas = current_user.get_user_practice_areas().all()
        return render_template('changeclass.html', user=user, classes=[], practiceAreas=practiceAreas)

@bp.route('/completedCourses/<username>')
@login_required
def statsFromCompletedCourses(username):
    if username != current_user.username:
        flash("You do not have access to this page!")
        return redirect(url_for('user_management.user', username=current_user.username))
    classes = current_user.get_student_classes().all()
    print(classes)
    if classes == []:
        flash("You have not joined any classes yet!")
        return redirect(url_for('user_management.user', username=current_user.username))
    class_courses = {}
    completedCourses = []
    for classDetails in classes:
        courses = current_user.get_completed_courses_in_class(classDetails.class_id)
        class_courses[classDetails] = courses
        completedCourses += courses
    print(class_courses)
    if completedCourses == []:
        flash("You have not yet completed any courses!")
        return redirect(url_for('user_management.user', username=current_user.username))

    return render_template('classCourses.html', username=username, class_courses=class_courses)

@bp.route('/updateCurrentClass/<classcode>', methods=['GET', 'POST'])
@login_required
def updateCurrentClass(classcode):
    current_user.current_class = classcode
    db.session.commit()
    return redirect(url_for('user_management.user', username=current_user.username))

def get_translation_language_key(language):
    lang = langDict[language]
    return lang
