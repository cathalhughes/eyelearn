import requests
import json
from html import unescape

r = requests.post("https://imagenet.eyelearn.club/translateObject", files={'image1': open('object.png', 'rb')}, data={'language':'fr'})

t = json.loads(r.content)
r = t["predictions"]
for l in r:
    print(l)