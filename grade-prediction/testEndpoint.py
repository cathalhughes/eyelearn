import requests
import json

r = requests.post("http://localhost:5006/getAveragePrediction", json={'dataArray': [1,2,3,4,5,6,7,8,9]})
response = json.loads(r.content)
print(response["username"] + "'s predicted avergae for the next week: " + str(response["prediction"]))