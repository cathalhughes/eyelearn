import requests

data = {"phrase":"She is running very fast ", "language": "es"}
r = requests.post("https://postagger.eyelearn.club/getPhraseTranslation1", data=data)
print(r.content)