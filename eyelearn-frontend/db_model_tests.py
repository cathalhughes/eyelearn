import unittest
from app import create_app, db
from app.models import User, Teacher_Class, Student_Daily_Average, Class_Daily_Average, Class_Average, Doodles, Student_Doodles, Class_Doodles, Misspelled_Word, Student_Vocab, Incorrect_Character, Student_Class, Student_Class_Level, Class, Student_Activity, Activity, Activity_Results, Daily_Average, Daily_Class_Average
import datetime
app = create_app('app.config.TestConfig')

class ModelTestCases(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.app_context().push()
        db.create_all()
        return app

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        #pass

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_user_role(self):
        u = User(username='test', email='test@test.com', role="Teacher")
        self.assertEqual(u.role, "Teacher")

    def test_get_user_classes(self):
        u = User(username='test1', email='test1@test1.com', role="Teacher")
        newClass = Class("test", "test", 2019, "French", "Class")
        db.session.add_all([u, newClass])
        db.session.commit()
        teacher_class = Teacher_Class(u.user_id, newClass.class_id)
        db.session.add(teacher_class)
        db.session.commit()
        teacher_classes = u.get_teachers_classes().all()
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        db.session.add(u)
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        student_classes = u.get_student_classes().all()
        self.assertGreater(len(student_classes), 0)
        self.assertGreater(len(teacher_classes), 0)
        self.assertEqual(student_classes[0].class_id, "test")
        self.assertEqual(teacher_classes[0].class_id, "test")


    def test_get_student_activities_and_stats(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id, student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        activities = u.get_activities("test").all()
        avg_score = u.get_student_overall_average_score(activities)
        ranked_activities, pieData = u.rank_activities_for_student(activities)
        highest, lowest, barData = u.get_high_low_average_activities(activities)
        studentsInClass = newClass.get_all_students_in_class().all()
        students_with_averages, class_average = newClass.get_students_with_average(studentsInClass)
        rank = newClass.get_student_rank_in_class(students_with_averages, u)
        self.assertEqual(avg_score, 50)
        self.assertEqual(len(ranked_activities), 1)
        self.assertEqual(highest, lowest)
        self.assertEqual(len(studentsInClass), 1)
        self.assertEqual(class_average, 50)
        self.assertEqual(rank[0], 1)
        self.assertEqual(rank[1], 1)
        self.assertEqual(len(rank[2]), 1)
        self.assertEqual(len(activities), 1)

    def test_get_user_practice_areas(self):
        u = User(username='test1', email='test1@test1.com', role="Teacher")
        newClass = Class("test", "test", 2019, "French", "Practice")
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, newClass.class_id)
        db.session.add(student_class)
        db.session.commit()
        teacher_practice_areas = u.get_user_practice_areas().all()
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test1", "test", 2019, "French", "Practice")
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test1")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        student_practice_areas = u.get_user_practice_areas().all()
        self.assertGreater(len(student_practice_areas), 0)
        self.assertGreater(len(teacher_practice_areas), 0)
        self.assertEqual(student_practice_areas[0].class_id, "test1")
        self.assertEqual(teacher_practice_areas[0].class_id, "test")


    def test_get_user_language(self):
        u = User(username='test1', email='test1@test1.com', role="Teacher")
        newClass = Class("test", "test", 2019, "French", "Practice")
        u.current_class = "test"
        db.session.add_all([u, newClass])
        db.session.commit()
        langauge = u.get_student_language()
        self.assertEqual(langauge, "French")

    def test_get_daily_average(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id,
                                            student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        current_time = datetime.datetime.utcnow()
        one_day_ago = current_time - datetime.timedelta(days=1)
        a = Activity_Results()
        students_daily_averages = a.get_average_in_class_for_every_student(time=one_day_ago).all()
        for student in students_daily_averages:
            daily_average = Daily_Average(average=student[0], date=current_time)
            db.session.add(daily_average)
            db.session.commit()
            student_daily_average = Student_Daily_Average(user_id=student[2], average_id=daily_average.average_id)
            class_daily_average = Class_Daily_Average(class_id=student[1], average_id=daily_average.average_id)
            db.session.add_all([student_daily_average, class_daily_average])
            db.session.commit()

        class_daily_averages = a.get_average_for_class(time=one_day_ago).all()
        for classx in class_daily_averages:
            daily_class_average = Daily_Class_Average(average=classx[0], date=current_time)
            db.session.add(daily_class_average)
            db.session.commit()
            class_average = Class_Average(class_id=classx[1], average_id=daily_class_average.average_id)
            db.session.add(class_average)
            db.session.commit()
        student_avgs = u.get_daily_average("test")
        class_avgs = newClass.get_class_daily_averages()

        self.assertEqual(len(student_avgs), 2)
        self.assertEqual(len(student_avgs['averages']), 1)
        self.assertEqual(student_avgs['averages'][0], 50)
        self.assertEqual(len(class_avgs), 2)
        self.assertEqual(len(class_avgs['averages']), 1)
        self.assertEqual(class_avgs['averages'][0], 50)

    def test_get_daily_prediction(self):
        pass

    def test_get_current_level(self):
        pass

    def test_get_active_level(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student", current_class="test")
        db.session.add(u)
        db.session.commit()
        level = Student_Class_Level(user_id=u.user_id, class_id=u.current_class, level=1)
        db.session.add(level)
        db.session.commit()
        u_level = u.get_active_level()
        self.assertEqual(u_level, 1)

    def test_update_level(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student", current_class="test")
        db.session.add(u)
        db.session.commit()
        level = Student_Class_Level(user_id=u.user_id, class_id=u.current_class, level=1)
        db.session.add(level)
        db.session.commit()
        u.update_level(2)
        u_level = u.get_active_level()
        self.assertEqual(u_level, 2)

    def test_freeze_stats(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id,
                                            student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        level = Student_Class_Level(user_id=u.user_id, class_id=u.current_class, level=1)
        db.session.add(level)
        db.session.commit()
        u.freeze_stats()
        frozen_stats = u.get_frozen_stats(1, u.current_class)
        self.assertEqual(frozen_stats.activities_played, 1)
        self.assertEqual(frozen_stats.level, 1)

    def test_get_completed_courses_in_class(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id,
                                            student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        level = Student_Class_Level(user_id=u.user_id, class_id=u.current_class, level=1)
        db.session.add(level)
        db.session.commit()
        u.freeze_stats()
        completed_course = u.get_completed_courses_in_class(u.current_class)#
        self.assertEqual(len(completed_course), 1)

    def test_get_students_new_vocab(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student", current_class="test")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        newVocab = Student_Vocab(english="hello", translation="bonjour", user_id=u.user_id,
                                 class_id=u.current_class, activity_id=14)
        db.session.add(newVocab)
        db.session.commit()
        vocab = u.get_students_new_vocab(u.current_class).all()
        class_vocab = newClass.get_class_new_vocab()
        self.assertEqual(len(vocab), 1)
        self.assertEqual(len(class_vocab), 1)

    def test_get_incorrect_letters(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student", current_class="test")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        for guessChar, wordChar in zip("hillo", "hello"):
            if guessChar != wordChar:
                incorrect_character = Incorrect_Character(class_id=u.current_class,
                                                          user_id=u.user_id,
                                                          incorrect_letter=guessChar, correct_letter=wordChar)
                db.session.add(incorrect_character)
                db.session.commit()
        incorrect = u.get_incorrect_letters(u.current_class).all()
        self.assertEqual(len(incorrect), 1)
        self.assertEqual(len(newClass.get_incorrect_letters_by_students().all()), 1)


    def test_get_misspelled_words(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student", current_class="test")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        misspelled_word = Misspelled_Word(class_id=u.current_class, user_id=u.user_id,
                                          word="Hello", translated_word="Bonjour")
        db.session.add(misspelled_word)
        db.session.commit()
        user_mispelled = u.get_misspelled_words(u.current_class).all()
        class_mispelled = newClass.get_misspelled_words().all()
        self.assertEqual(len(user_mispelled), 1)
        self.assertEqual(len(class_mispelled), 1)

    def test_get_all_students_in_class(self):
        u = User(username='test1', email='test1@test1.com', role="Teacher")
        newClass = Class("test", "test", 2019, "French", "Practice")
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, newClass.class_id)
        db.session.add(student_class)
        db.session.commit()
        students_in_class = newClass.get_all_students_in_class().all()
        self.assertEqual(len(students_in_class), 1)
        self.assertEqual(students_in_class[0], u)

    def test_get_activity_scores_in_class(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id, student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        activities = newClass.get_activity_scores_in_class().all()
        students = newClass.get_all_students_in_class().all()
        language = newClass.get_language()
        games_class = newClass.get_games_played_by_class(students)
        self.assertEqual(len(games_class), 2)
        self.assertEqual("French", language)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0], activity_result)

    def test_class_stats(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        score = 50
        activity_id = 2
        activity_result = Activity_Results(activity_id=activity_id, score=score, class_id=u.current_class)
        db.session.add(activity_result)
        db.session.commit()
        student_activity = Student_Activity(activity_instance_id=activity_result.activity_instance_id,
                                            student_id=u.user_id)
        db.session.add(student_activity)
        db.session.commit()
        studentsInClass = newClass.get_all_students_in_class().all()
        students_with_averages, class_average = newClass.get_students_with_average(studentsInClass)
        activities = newClass.get_activity_scores_in_class().all()
        highest_activity, lowest_activity, barData = newClass.get_activity_averages_in_class(activities)
        filename, averages = newClass.get_class_distribution_chart(students_with_averages)
        self.assertEqual(class_average, 50)
        self.assertEqual(highest_activity[0], "Numbers")
        self.assertEqual(lowest_activity[0], "Numbers")
        self.assertEqual(highest_activity[1], 50)
        self.assertEqual(lowest_activity[1], 50)
        self.assertEqual(len(averages), 1)
        self.assertEqual(averages[0], 50)

    def test_populate_table(self):
        a = Activity()
        a.populate_table()
        number_of_rows = db.session.query(Activity).count()
        self.assertEqual(number_of_rows, 21)

    def test_get_doodles(self):
        u = User(username='teststudent', email='test2@test2.com', role="Student")
        newClass = Class("test", "test", 2019, "French", "Class")
        a = Activity()
        a.populate_table()
        db.session.add_all([u, newClass])
        db.session.commit()
        student_class = Student_Class(u.user_id, "test")
        u.current_class = "test"
        db.session.add(student_class)
        db.session.commit()
        doodle = Doodles(foreign_answer="test", foreign_guess="test", location="location")
        db.session.add(doodle)
        db.session.commit()
        student_doodle = Student_Doodles(user_id=u.user_id, doodle_id=doodle.doodle_id)
        class_doodle = Class_Doodles(class_id=u.current_class, doodle_id=doodle.doodle_id)
        db.session.add_all([student_doodle, class_doodle])
        db.session.commit()
        doodles = u.get_doodles().all()
        self.assertTrue(len(doodles) == 1)




if __name__ == '__main__':
    unittest.main(verbosity=2)