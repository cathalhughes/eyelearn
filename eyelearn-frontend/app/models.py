from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
import sqlalchemy as sqla
import os
from collections import defaultdict
import numpy as np
import time
import json


# db.drop_all()




@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(64))
    current_class = db.Column(db.String(64), db.ForeignKey('class.class_id'))
    classes = db.relationship('Class', secondary='teacher_class', backref=db.backref('users', lazy='dynamic'))
    activities = db.relationship('Activity_Results', secondary='student_activity', backref=db.backref('users', lazy='dynamic'))


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return (self.user_id)

    def get_current_user_role(self):
        return self.role

    def get_activities(self, class_id):
        return Activity_Results.query.join(Student_Activity, (Student_Activity.activity_instance_id == Activity_Results.activity_instance_id)).filter(Student_Activity.student_id == self.user_id, Activity_Results.class_id == class_id).order_by(Activity_Results.score)

    def get_daily_average(self, class_id):
        #query = Daily_Average.query.filter_by(class_id=class_id, user_id=self.user_id).order_by(Daily_Average.date)
        query = Daily_Average.query.join(Class_Daily_Average, (Class_Daily_Average.average_id == Daily_Average.average_id)).join(Student_Daily_Average, (Student_Daily_Average.average_id == Daily_Average.average_id)).filter(Class_Daily_Average.class_id == class_id, Student_Daily_Average.user_id == self.user_id).order_by(Daily_Average.date)
        daily_averages = query.all()
        daily_average_data = {"averages": [x.average for x in daily_averages],
                              "dates": [datetime.strptime(str(x.date.date()), '%Y-%m-%d').strftime('%d/%m/%y') for x in
                                        daily_averages]}
        return daily_average_data

    def get_daily_prediction(self, classcode):
        return db.session.query(Predicted_Average.prediction).join(Class_Predicted_Average, (Class_Predicted_Average.average_id == Predicted_Average.average_id)).join(Student_Predicted_Average, (Student_Predicted_Average.average_id == Predicted_Average.average_id)).filter(Class_Predicted_Average.class_id == classcode, Student_Predicted_Average.user_id == self.user_id).order_by(sqla.desc(Predicted_Average.date)).first()

    def get_current_level(self):
        config = Class_Configs.query.filter_by(class_id=self.current_class).first()
        first_level_activities, first_level_unlock_data = json.loads(config.layout_data)['2'], json.loads(config.unlock_data)['1']
        second_level_activities, second_level_unlock_data = json.loads(config.layout_data)['3'], json.loads(config.unlock_data)['2']
        third_level_activities, third_level_unlock_data = json.loads(config.layout_data)['4'], json.loads(config.unlock_data)['3']

        activities_in_class = self.get_activities(self.current_class).all()
        print("First Unlock Data")
        print(first_level_unlock_data)
        tools = ["Object Translator", "Speech Translator", "Your New Words", "Phrase Translator & Tagger"]
        # return 4
        print(activities_in_class)
        if activities_in_class is None:
            return 1
        activity_names = []

        for activity in activities_in_class:
            activity_name = Activity.query.filter_by(activity_id=activity.activity_id).first().name
            if activity_name not in tools:
                activity_names.append(activity_name)
        print("names")
        print(activity_names)
        print(first_level_activities)
        for activity in first_level_activities:
            count = activity_names.count(activity)
            if activity in tools:
                continue
            if count < int(first_level_unlock_data):
                return 1
        for activity in second_level_activities:
            count = activity_names.count(activity)
            if activity in tools:
                continue
            if count < int(second_level_unlock_data):
                return 2
        for activity in third_level_activities:
            count = activity_names.count(activity)
            if activity in tools:
                continue
            if count < int(third_level_unlock_data):
                return 3

        return 4

    def get_active_level(self):
        level = Student_Class_Level.query.filter(Student_Class_Level.user_id == self.user_id, Student_Class_Level.class_id == self.current_class).all()
        return level[0].level

    def update_level(self, update):
        level = Student_Class_Level.query.filter(Student_Class_Level.user_id == self.user_id,
                                                 Student_Class_Level.class_id == self.current_class).all()
        level[0].level = update
        db.session.commit()

    def get_frozen_stats(self, level, class_id):
        stats = Stats.query.join(Student_Stats, (Stats.stats_id == Student_Stats.stats_id)).join(Class_Stats, (Class_Stats.stats_id ==  Stats.stats_id)).filter(Stats.level == level, Class_Stats.class_id == class_id, self.user_id == Student_Stats.student_id).all()

        if stats == []:
            return None
        return stats[0]

    def get_completed_courses_in_class(self, class_id):
        stats = Stats.query.join(Student_Stats, (Stats.stats_id == Student_Stats.stats_id)).join(Class_Stats, (
                    Class_Stats.stats_id == Stats.stats_id)).filter(Class_Stats.class_id == class_id, self.user_id == Student_Stats.student_id).all()
        return stats

    def get_high_low_average_activities(self, activities):
        activityScores = defaultdict(list)
        for activity in activities:
            activityScores[activity.activity.name].append(activity.score)
        activityAverages = defaultdict(int)
        for activity in activityScores:
            activityAverages[activity] = sum(activityScores[activity]) / len(activityScores[activity])
        sortedActivities = [(k, activityAverages[k]) for k in
                            sorted(activityAverages, key=activityAverages.get, reverse=True)]

        jsonData = {"data": [], "labels": []}
        for activity in sortedActivities:
            jsonData["data"].append(activity[1])
            jsonData["labels"].append(activity[0])

        return sortedActivities[0], sortedActivities[-1], jsonData



    def get_teachers_classes(self):
        return Class.query.join(Teacher_Class, (Teacher_Class.class_id == Class.class_id)).filter(Class.role == "Class", Teacher_Class.user_id == self.user_id).order_by(Class.year)

    def get_student_classes(self):
        return Class.query.join(Student_Class, (Student_Class.class_id == Class.class_id)).filter(Class.role == "Class", Student_Class.user_id == self.user_id).order_by(Class.year)

    def get_students_new_vocab(self, class_id):
        return Student_Vocab.query.join(User, (User.user_id == Student_Vocab.user_id)).filter(Student_Vocab.class_id == class_id, self.user_id == Student_Vocab.user_id).order_by(Student_Vocab.vocab_id.desc())

    def get_user_practice_areas(self):
        return Class.query.join(Student_Class, (Student_Class.class_id == Class.class_id)).filter(Class.role == "Practice", Student_Class.user_id == self.user_id).order_by(Class.year)

    def get_student_overall_average_score(self, completedActvities):
        score = 0
        for activity in completedActvities:
            score += activity.score
        if len(completedActvities) == 0:
            return 0
        return score // len(completedActvities)

    def rank_activities_for_student(self, completedActivities):
        activityOcurrences = defaultdict(int)
        for activity in completedActivities:
            activityOcurrences[activity.activity.name] += 1

        sortedActivities = [(k, activityOcurrences[k]) for k in sorted(activityOcurrences, key=activityOcurrences.get, reverse=True)]

        jsonData = {"data": [], "labels": []}
        for activity in sortedActivities:
            jsonData["data"].append(activity[1])
            jsonData["labels"].append(activity[0])
        return sortedActivities, jsonData

    def freeze_stats(self):
        activities = self.get_activities(self.current_class).all()
        num_activities = len(activities)
        avg_score = int(self.get_student_overall_average_score(activities))
        ranked_activities, pieData = self.rank_activities_for_student(activities)
        print(ranked_activities)
        highest, lowest, barData = self.get_high_low_average_activities(activities)
        highest = json.dumps(highest)
        lowest = json.dumps(lowest)
        print(highest, lowest)
        selectedClass = Class.query.filter_by(class_id=self.current_class).first_or_404()
        studentsInClass = selectedClass.get_all_students_in_class().all()
        students_with_averages, class_average = selectedClass.get_students_with_average(studentsInClass)
        rank = selectedClass.get_student_rank_in_class(students_with_averages, self)
        rank = rank[0]
        print(rank)
        newVocab = self.get_students_new_vocab(self.current_class).all()
        vocabData = [(vocab.english, vocab.translation) for vocab in newVocab]
        vocabData = vocabData[:4]
        print(vocabData)
        new_vocab_learnt = len(newVocab)
        misspelledWords = self.get_misspelled_words(self.current_class).all()
        misspelledWordsData = [(vocab.word, vocab.translated_word, vocab.count) for vocab in misspelledWords]
        misspelledWordsData = misspelledWordsData[:4]
        level = self.get_active_level()
        world_rank = self.get_world_ranking()
        prediction = self.get_daily_prediction(self.current_class)
        stats = Stats(level=level, rank=rank, highest=highest, lowest=lowest, world_rank=world_rank, prediction=prediction, new_vocab=json.dumps(vocabData), problem_words=json.dumps(misspelledWordsData), most=json.dumps(ranked_activities[0]), least=json.dumps(ranked_activities[-1]), activities_played=num_activities, num_new_words=new_vocab_learnt, average=avg_score)
        db.session.add(stats)
        db.session.commit()
        student_stats = Student_Stats(student_id=self.user_id, stats_id=stats.stats_id)
        db.session.add(student_stats)
        db.session.commit()
        class_stats = Class_Stats(class_id=self.current_class, stats_id=stats.stats_id)
        db.session.add(class_stats)
        db.session.commit()

    def get_world_ranking(self):
        a = Activity_Results()
        ranked_list = sorted(a.get_all_averages_for_every_student_in_every_class().all(), key=lambda x: x[0], reverse=True)
        personal_rank = [i for i, tupl in enumerate(ranked_list) if tupl[2] == self.user_id]
        for index in personal_rank:
            if ranked_list[index][1] == self.current_class:
                return index + 1

    def get_student_language(self):
        selectedClass = Class.query.filter_by(class_id=self.current_class).first_or_404()
        return selectedClass.get_language()

    def get_incorrect_letters(self, class_id):
        return db.session.query(Incorrect_Character.correct_letter, Incorrect_Character.incorrect_letter, db.func.count(Incorrect_Character.correct_letter).label("count")).filter(Incorrect_Character.class_id == class_id, Incorrect_Character.user_id == self.user_id).group_by(Incorrect_Character.correct_letter).order_by(db.func.count(Incorrect_Character.correct_letter))

    def get_misspelled_words(self, class_id):
        return db.session.query(Misspelled_Word.word, Misspelled_Word.translated_word, db.func.count(Misspelled_Word.word).label("count")).filter(Misspelled_Word.class_id == class_id, self.user_id == Misspelled_Word.user_id).group_by(Misspelled_Word.word).order_by(db.func.count(Misspelled_Word.word))

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_doodles(self):
        return Doodles.query.join(Student_Doodles, (Student_Doodles.doodle_id == Doodles.doodle_id)).join(Class_Doodles, (Class_Doodles.doodle_id == Doodles.doodle_id)).filter(self.user_id == Student_Doodles.user_id, self.current_class == Class_Doodles.class_id)

    def get_task_in_progress(self):
        return Task.query.join(User_Task, (User_Task.task_id == Task.task_id)).filter(self.user_id == User_Task.task_id, Task.complete == False).first()

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Class(db.Model):
    __tablename__ = 'class'
    class_id = db.Column(db.String(64), primary_key=True, autoincrement=False)
    class_name = db.Column(db.String(64), index=True)
    year = db.Column(db.String(64))
    language = db.Column(db.String(64))
    role = db.Column(db.String(64))
    # year = db.Column(db.DateTime, nullable=False, default=datetime.strftime(datetime.today(), "%Y"))

    def __init__(self, class_id, class_name, year, language, role):
        self.class_id = class_id
        self.class_name = class_name
        self.year = year
        self.language = language
        self.role = role

    def check_for_custom_game(self, category):
        return Model.query.join(Class_Model, (Class_Model.model_id == Model.model_id)).filter(self.class_id == Class_Model.class_id, Model.category == category).first()

    def get_custom_games(self):
        return Model.query.join(Class_Model, (Class_Model.model_id == Model.model_id)).filter(
            self.class_id == Class_Model.class_id).all()

    def get_all_students_in_class(self):
        return User.query.join(Student_Class, (Student_Class.user_id == User.user_id)).filter(Student_Class.class_id == self.class_id).order_by(User.username)

    def get_class_daily_averages(self):
        #query =  Daily_Class_Average.query.filter_by(class_id=self.class_id).order_by(Daily_Class_Average.date)
        query = Daily_Class_Average.query.join(Class_Average,
                                         (Class_Average.average_id == Daily_Class_Average.average_id)).filter(
            Class_Average.class_id == self.class_id).order_by(
            Daily_Class_Average.date)
        daily_averages = query.all()
        daily_average_data = {"averages": [x.average for x in daily_averages], "dates": [datetime.strptime(str(x.date.date()), '%Y-%m-%d').strftime('%m/%d/%y') for x in daily_averages]}
        return daily_average_data


    def get_class_average(self, students):
        if len(students) == 0:
            return 0
        score = 0
        for student in students:
            score += student.get_student_overall_average_score()

        return score / len(students)

    def get_daily_class_prediction(self):
        #return db.session.query(Predicted_Class_Average.prediction).filter_by(class_id=self.class_id, time_frame="Daily").order_by(sqla.desc(Predicted_Class_Average.date)).first()
        return db.session.query(Predicted_Class_Average.prediction).join(Class_Prediction, (Class_Prediction.average_id == Predicted_Class_Average.average_id)).filter(Class_Prediction.class_id == self.class_id).order_by(sqla.desc(Predicted_Class_Average.date)).first()

    def get_class_new_vocab(self):
        query = Student_Vocab.query.join(Class, (Class.class_id == Student_Vocab.class_id)).filter(Student_Vocab.class_id == self.class_id).order_by(Student_Vocab.vocab_id.desc())
        words = query.all()
        words_student = []
        for word in words:
            student = User.query.filter_by(user_id=word.user_id).first()
            words_student.append((word, student.username))

        return words_student





    def get_language(self):
        return self.language

    def get_activity_scores_in_class(self):
        return Activity_Results.query.join(Student_Activity, (
                    Student_Activity.activity_instance_id == Activity_Results.activity_instance_id)).join(Student_Class, (Student_Activity.student_id == Student_Class.user_id)).filter(Student_Class.class_id == self.class_id)

    def get_activity_averages_in_class(self, activities):
        activityScores = defaultdict(list)
        for activity in activities:
            activityScores[activity.activity.name].append(activity.score)
        activityAverages = defaultdict(int)
        for activity in activityScores:
            activityAverages[activity] = sum(activityScores[activity]) / len(activityScores[activity])
        sortedActivities = [(k, activityAverages[k]) for k in
                            sorted(activityAverages, key=activityAverages.get, reverse=True)]

        jsonData = {"data": [], "labels": []}
        for activity in sortedActivities:
            jsonData["data"].append(activity[1])
            jsonData["labels"].append(activity[0])

        return sortedActivities[0], sortedActivities[-1], jsonData

    def get_class_distribution_chart(self, student_averages):
        averages = []
        for student_average in student_averages:
            averages.append(student_average[1])
        averages1 = np.array(averages)
        # graph = sns.distplot(averages1, rug=False)
        timestr = time.strftime("%Y%m%d")
        filename = self.class_id + timestr + ".png"
        location = "static/distributions/"
        # plt.savefig(location + filename)
        return filename, averages



    def get_students_with_average(self, students):
        students_averages = []
        class_score = 0
        for student in students:
            student_activities = student.get_activities(self.class_id).all()
            student_average = student.get_student_overall_average_score(student_activities)
            students_averages.append((student, student_average))
            class_score += student_average
        if class_score == 0: # new change
            return None, None
        return students_averages, class_score / len(students_averages)

    def get_student_rank_in_class(self, students_averages, student):
        sortedStudents = sorted(students_averages, key=lambda tup: tup[1], reverse=True)
        rank = 1
        for sortedStudent in sortedStudents:
            if student.username == sortedStudent[0].username:
                print(rank, len(sortedStudents))
                return rank, len(sortedStudents), sortedStudents
            rank += 1
        print(rank, len(sortedStudents))
        return rank, len(sortedStudents), sortedStudents

    def get_games_played_by_class(self, students):
        activityOcurrences = defaultdict(int)
        for student in students:
            student_activities = student.get_activities(self.class_id).all()
            for activity in student_activities:
                activityOcurrences[activity.activity.name] += 1

        sortedActivities = [(k, activityOcurrences[k]) for k in
                            sorted(activityOcurrences, key=activityOcurrences.get, reverse=True)]
        jsonData = {"data": [], "labels":[]}
        for activity in sortedActivities:
            jsonData["data"].append(activity[1])
            jsonData["labels"].append(activity[0])
        return sortedActivities, jsonData

    def get_incorrect_letters_by_students(self):
        return db.session.query(Incorrect_Character.correct_letter, Incorrect_Character.incorrect_letter, User.username, db.func.count(Incorrect_Character.correct_letter).label("count")).join(User, (User.user_id == Incorrect_Character.user_id)).filter(Incorrect_Character.class_id == self.class_id).group_by(Incorrect_Character.user_id).group_by(Incorrect_Character.correct_letter).having(db.func.count(Incorrect_Character.correct_letter > 2))

    def get_misspelled_words(self):
        return db.session.query(Misspelled_Word.word, Misspelled_Word.translated_word,
                                db.func.count(Misspelled_Word.word).label("count")).filter(
            Misspelled_Word.class_id == self.class_id).group_by(
            Misspelled_Word.word).order_by(db.func.count(Misspelled_Word.word))


class Activity(db.Model):
    __tablename__ = 'activity'
    activity_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    activity_results = db.relationship('Activity_Results', backref=db.backref('activity_results'))

    def populate_table(self):
        activity1 = Activity(activity_id=1, name="Spelling")
        activity2 = Activity(activity_id=2, name="Numbers")
        activity3 = Activity(activity_id=3, name="Sports")
        activity4 = Activity(activity_id=4, name="Vehicles")
        activity5 = Activity(activity_id=5, name="Animals")
        activity6 = Activity(activity_id=6, name="Scramble")
        activity7 = Activity(activity_id=7, name="Listen Up!")
        activity8 = Activity(activity_id=8, name="Speak Up!")
        activity9 = Activity(activity_id=9, name="Swipe Sports")
        activity10 = Activity(activity_id=10, name="Swipe Vehicles")
        #activity11 = Activity(activity_id=11, name="Swipe Emojis")
        activity12 = Activity(activity_id=12, name="Swipe Animals")
        activity13 = Activity(activity_id=13, name="Doodle")
        activity14 = Activity(activity_id=14, name="New Words")
        activity15 = Activity(activity_id=15, name="Find Me")
        activity16 = Activity(activity_id=16, name="Doing What?")
        activity17 = Activity(activity_id=17, name="Speech Translator")
        activity18 = Activity(activity_id=18, name="Speech Translator")
        activity19 = Activity(activity_id=19, name="Phrase Translator & Tagger")
        activity20 = Activity(activity_id=20, name="Your New Words")
        activity21 = Activity(activity_id=21, name="Custom Find Me")
        activity22 = Activity(activity_id=22, name="Custom Find Activities")
        activity23 = Activity(activity_id=23, name="Custom Swipe Activities")

        activities = [activity1, activity2, activity3, activity4, activity5, activity6, activity7, activity8, activity9, activity10, activity12, activity13, activity14, activity15, activity16, activity17, activity18, activity19, activity20, activity21, activity22, activity23]
        for activity in activities:
            db.session.add(activity)
            db.session.commit()

    def delete_all_rows(self):
        num_rows_deleted = db.session.query(Activity).delete()
        db.session.commit()


    def get_id(self):
        return (self.activity_id)

class Activity_Results(db.Model):
    __tablename__ = 'activity_results'
    activity_instance_id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, index=True)
    activity_id = db.Column('activity_id', db.ForeignKey('activity.activity_id'))
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    activity = db.relationship("Activity", backref="activity")

    def get_id(self):
        return (self.activity_instance_id)

    def get_average_in_class_for_every_student(self, time):
        return db.session.query(db.func.avg(Activity_Results.score), Activity_Results.class_id, Student_Activity.student_id).join(Student_Activity, (Student_Activity.activity_instance_id == Activity_Results.activity_instance_id)).filter(Activity_Results.date > time).group_by(Activity_Results.class_id, Student_Activity.student_id)

    def get_average_for_class(self, time):
        return db.session.query(db.func.avg(Activity_Results.score), Activity_Results.class_id).filter(Activity_Results.date > time).group_by(Activity_Results.class_id)

    def get_all_averages_for_every_student_in_every_class(self):
        return db.session.query(db.func.avg(Activity_Results.score), Activity_Results.class_id, Student_Activity.student_id).join(Student_Activity, (Student_Activity.activity_instance_id == Activity_Results.activity_instance_id)).group_by(Activity_Results.class_id, Student_Activity.student_id)



class Student_Activity(db.Model):
    __tablename__ = 'student_activity'
    student_id = db.Column('student_id', db.ForeignKey('user.user_id'), primary_key=True)
    activity_instance_id = db.Column('activity_instance_id', db.ForeignKey('activity_results.activity_instance_id'), primary_key=True)
    #activity_results = db.relationship('Activity_Results', backref=db.backref('activity_results'))


class Teacher_Class(db.Model):
    __tablename__ = 'teacher_class'
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)

    def __init__(self, user_id, class_id):
        self.user_id = user_id
        self.class_id = class_id



class Student_Class(db.Model):
    __tablename__ = 'student_class'
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)

    def __init__(self, user_id, class_id):
        self.user_id = user_id
        self.class_id = class_id


class Student_Vocab(db.Model):
    __tablename__ = 'student_vocab'
    vocab_id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(120), index=True)
    translation = db.Column(db.String(120), index=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'))
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'))
    activity_id = db.Column('activity_id', db.ForeignKey('activity.activity_id'))


class Student_Daily_Average(db.Model):
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    average_id = db.Column('average_id', db.ForeignKey('daily_averages.average_id'), primary_key=True)

class Class_Daily_Average(db.Model):
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    average_id = db.Column('average_id', db.ForeignKey('daily_averages.average_id'), primary_key=True)


class Daily_Average(db.Model):
    __tablename__ = 'daily_averages'
    average_id = db.Column(db.Integer, primary_key=True)
    average = db.Column(db.Integer)
    date = db.Column(db.DateTime)

class Class_Average(db.Model):
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    average_id = db.Column('average_id', db.ForeignKey('daily_class_averages.average_id'), primary_key=True)

class Daily_Class_Average(db.Model):
    __tablename__ = 'daily_class_averages'
    average_id = db.Column(db.Integer, primary_key=True)
    average = db.Column(db.Integer)
    date = db.Column(db.DateTime)

class Student_Predicted_Average(db.Model):
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    average_id = db.Column('average_id', db.ForeignKey('predicted_averages.average_id'), primary_key=True)

class Class_Predicted_Average(db.Model):
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    average_id = db.Column('average_id', db.ForeignKey('predicted_averages.average_id'), primary_key=True)


class Predicted_Average(db.Model):
    __tablename__ = 'predicted_averages'
    average_id = db.Column(db.Integer, primary_key=True)
    prediction = db.Column(db.Integer)
    time_frame = db.Column(db.String(120))
    date = db.Column(db.DateTime)

class Class_Prediction(db.Model):
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    average_id = db.Column('average_id', db.ForeignKey('predicted_class_averages.average_id'), primary_key=True)

class Predicted_Class_Average(db.Model):
    __tablename__ = 'predicted_class_averages'
    average_id = db.Column(db.Integer, primary_key=True)
    prediction = db.Column(db.Integer)
    time_frame = db.Column(db.String(120))
    date = db.Column(db.DateTime)

class Incorrect_Character(db.Model):
    __tablename__ = 'incorrect_characters'
    incorrect_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'))
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'))
    correct_letter = db.Column(db.String(1))
    incorrect_letter = db.Column(db.String(1))

class Misspelled_Word(db.Model):
    __tablename__ = 'misspelled_words'
    misspelled_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'))
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'))
    word = db.Column(db.String(30))
    translated_word = db.Column(db.String(30))

class Class_Configs(db.Model):
    __tablename__ = 'class_configs'
    config_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'))
    layout_data = db.Column(db.String(500))
    vocab_data = db.Column(db.String(3000))
    unlock_data = db.Column(db.String(500))

####------

class Student_Stats(db.Model):
    __tablename__ = 'student_stats'
    student_id = db.Column('student_id', db.ForeignKey('user.user_id'), primary_key=True)
    stats_id = db.Column('stats_id', db.ForeignKey('stats.stats_id'), primary_key=True)

class Class_Stats(db.Model):
    __tablename__ = 'class_stats'
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    stats_id = db.Column('stats_id', db.ForeignKey('stats.stats_id'), primary_key=True)

class Stats(db.Model):
    __tablename__ = 'stats'
    stats_id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer)
    rank = db.Column(db.Integer)
    highest = db.Column(db.String(200))
    lowest = db.Column(db.String(200))
    world_rank = db.Column(db.Integer)
    prediction = db.Column(db.String(50))
    new_vocab = db.Column(db.String(2000))
    problem_words = db.Column(db.String(2000))
    most = db.Column(db.String(200))
    least = db.Column(db.String(200))
    activities_played = db.Column(db.Integer)
    average = db.Column(db.Integer)
    num_new_words = db.Column(db.Integer)

class Student_Class_Level(db.Model):
    __tablename__ = 'student_class_level'
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    level = db.Column(db.Integer)

class Student_Doodles(db.Model):
    __tablename__ = 'student_doodles'
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    doodle_id = db.Column('doodle_id', db.ForeignKey('doodles.doodle_id'), primary_key=True)

class Class_Doodles(db.Model):
    __tablename__ = 'class_doodles'
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    doodle_id = db.Column('doodle_id', db.ForeignKey('doodles.doodle_id'), primary_key=True)

class Doodles(db.Model):
    __tablename__ = 'doodles'
    doodle_id = db.Column(db.Integer, primary_key=True)
    foreign_answer = db.Column(db.String(50))
    foreign_guess = db.Column(db.String(50))
    location = db.Column(db.String(200))

class Find_Me_Configurations(db.Model):
    __tablename__ = "find_me_configurations"
    find_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'))
    items = db.Column(db.String(8000))
    eng_loc = db.Column(db.String(200))
    for_loc = db.Column(db.String(200))


class Task(db.Model):
    __tablename__ = "task"
    task_id = db.Column(db.Integer, primary_key=True)
    complete = db.Column(db.Boolean, default=False)

class User_Task(db.Model):
    user_id = db.Column('user_id', db.ForeignKey('user.user_id'), primary_key=True)
    task_id = db.Column('task_id', db.ForeignKey('task.task_id'), primary_key=True)

class Model(db.Model):
    model_id = db.Column(db.Integer, primary_key=True)
    model_loc = db.Column(db.String(300))
    category = db.Column(db.String(50))
    eng_loc = db.Column(db.String(300))
    for_loc = db.Column(db.String(300))

class Class_Model(db.Model):
    class_id = db.Column('class_id', db.ForeignKey('class.class_id'), primary_key=True)
    model_id = db.Column('model_id', db.ForeignKey('model.model_id'), primary_key=True)















#Activity.populate_table()

basedir = os.path.abspath(os.path.dirname(__file__))

engine = sqla.create_engine('sqlite:///' + os.path.join(basedir, 'app.db'))
#
#
#Student_Class.__table__.create(engine)



#Activity.__table__.create(engine)

# a = Activity()
# a.populate_table()
# User_Task.__table__.drop(engine)
# Task.__table__.create(engine)
# User_Task.__table__.create(engine)
# Class_Model.__table__.drop(engine)
# Model.__table__.drop(engine)
# Class_Model.__table__.create(engine)
# Model.__table__.create(engine)
#
# Predicted_Average.__table__.create(engine)
# Student_Predicted_Average.__table__.create(engine)
# Class_Predicted_Average.__table__.create(engine)
# Class_Prediction.__table__.create(engine)
# Class_Predicted_Average.__table__.create(engine)
# Stats.__table__.create(engine)
# Doodles.__table__.create(engine)
# Student_Doodles.__table__.create(engine)
# Class_Doodles.__table__.create(engine)
# Daily_Class_Average.__table__.drop(engine)
#Task.__table__.drop(engine)
#
# a = Activity()
# a.populate_table()

# Student_Class_Level.__table__.drop(engine)
# Stats.__table__.drop(engine)
# Class_Stats.__table__.drop(engine)
# Student_Stats.__table__.drop(engine)
#
# Student_Class_Level.__table__.create(engine)
# Stats.__table__.create(engine)
# Class_Stats.__table__.create(engine)
# Student_Stats.__table__.create(engine)