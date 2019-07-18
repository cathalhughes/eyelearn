import requests
import json



data = {"classname": "test", "user_id": 'tester', 'language': 'French', "category": 'food', 'items' : ["bread", "cheese", "meat", "chicken"], 'classname': 'testclass'}

data = json.dumps(data)

#response = requests.post("https://create.eyelearn.club/", data=data)
response = requests.post("http://127.0.0.1:5002/trainModel", data=data)

assert response.status_code == 200

print(response)