from app import create_app, db
from app.models import Activity_Results, Daily_Average, Daily_Class_Average, Student_Daily_Average,  Class_Daily_Average, Class_Average
import datetime
import requests

app = create_app()
with app.app_context():
    db.init_app(app)

def get_daily_averages():
    print("in here")
    current_time = datetime.datetime.utcnow()
    one_day_ago = current_time - datetime.timedelta(days=1)
    print(one_day_ago)
    a = Activity_Results()
    students_daily_averages = a.get_average_in_class_for_every_student(time=one_day_ago).all()
    print(students_daily_averages)
    for student in students_daily_averages:

        daily_average = Daily_Average(average=student[0], date=current_time)
        db.session.add(daily_average)
        db.session.commit()
        student_daily_average = Student_Daily_Average(user_id=student[2], average_id=daily_average.average_id)
        class_daily_average = Class_Daily_Average(class_id=student[1], average_id=daily_average.average_id)
        db.session.add_all([student_daily_average, class_daily_average])
        db.session.commit()

    class_daily_averages = a.get_average_for_class(time=one_day_ago).all()
    print(class_daily_averages)
    for classx in class_daily_averages:
        daily_class_average = Daily_Class_Average(average=classx[0], date=current_time)
        db.session.add(daily_class_average)
        db.session.commit()
        class_average = Class_Average(class_id=classx[1], average_id=daily_class_average.average_id)
        db.session.add(class_average)
        db.session.commit()

    print("Added daily Averages")





