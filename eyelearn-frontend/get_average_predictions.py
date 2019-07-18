import requests
import json
from app import db
from app.models import Daily_Average, Predicted_Average, Student_Predicted_Average, Class_Predicted_Average, Class_Prediction, Daily_Class_Average, Predicted_Class_Average, Student_Class, User, Class
import datetime


# r = requests.post("http://localhost:5006/getAveragePrediction", json={'dataArray': [1,2,3,4,5,6,7,8,9]})
# response = json.loads(r.content)
# print(response["username"] + "'s predicted avergae for the next week: " + str(response["prediction"]))

def get_user_predictions():
    current_time = datetime.datetime.utcnow()
    tomorrow = current_time + datetime.timedelta(days=1)
    user_ids_class_ids = [(x.user_id, x.class_id) for x in Student_Class.query.all()]
    average_data = []
    print(user_ids_class_ids)
    noData = []
    for user_id in user_ids_class_ids:
        user = User.query.filter_by(user_id=user_id[0]).first()
        data = user.get_daily_average(user_id[1])['averages']
        if data is None or data == []:
            noData.append(user_id)
        else:
            average_data.append(data)

    r = requests.post("https://grade.eyelearn.club/getAveragePrediction", json={'dataArray': average_data})
    response = json.loads(r.content)
    predictions = response["predictions"]

    for user_id in noData:
        user_ids_class_ids.remove(user_id)

    print(predictions, user_ids_class_ids)
    for i in range(len(user_ids_class_ids)):
        if predictions[i] > 100:
            predictions[i] = 100
        predicted_average = Predicted_Average(prediction=predictions[i], time_frame="Daily", date=tomorrow)
        db.session.add(predicted_average)
        db.session.commit()
        student_predicted_average = Student_Predicted_Average(user_id=user_ids_class_ids[i][0], average_id=predicted_average.average_id)
        class_predicted_average = Class_Predicted_Average(class_id=user_ids_class_ids[i][1], average_id=predicted_average.average_id)
        db.session.add_all([student_predicted_average, class_predicted_average])
        db.session.commit()

def get_class_predictions():
    current_time = datetime.datetime.utcnow()
    tomorrow = current_time + datetime.timedelta(days=1)
    class_ids = [x.class_id for x in Class.query.all()]
    average_data = []
    noData = []
    for class_id in class_ids:
        classx = Class.query.filter_by(class_id=class_id).first()
        data = classx.get_class_daily_averages()['averages']
        if data is None or data == []:
            noData.append(class_id)
        else:
            average_data.append(data)
    r = requests.post("https://grade.eyelearn.club/getAveragePrediction", json={'dataArray': average_data})
    response = json.loads(r.content)
    predictions = response["predictions"]
    for class_id in noData:
        class_ids.remove(class_id)
    print("classes")
    print(predictions, class_ids)

    for i in range(len(class_ids)):
        if predictions[i] > 100:
            predictions[i] = 100
        predicted_class_average = Predicted_Class_Average(prediction=predictions[i], time_frame="Daily", date=tomorrow)
        db.session.add(predicted_class_average)
        db.session.commit()
        class_prediction = Class_Prediction(class_id=class_ids[i], average_id=predicted_class_average.average_id)
        db.session.add(class_prediction)
        db.session.commit()
    print("finished Predictions")

#get_user_predictions()
# get_class_predictions()