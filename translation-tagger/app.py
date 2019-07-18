from flask import Flask, request, Response, render_template, flash, redirect, url_for, jsonify
from nltk.tag import StanfordPOSTagger
from nltk.tokenize import word_tokenize
from nltk.tag import map_tag
import requests
import json

from google.cloud import translate
import os
from html import unescape

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="translateKey.json"

translate_client = translate.Client()

jar = 'C:/Users/Cathal/Documents/stanford-postagger-full-2018-10-16/stanford-postagger-full-2018-10-16/stanford-postagger-3.9.2.jar'
french_model = 'C:/Users/Cathal/Documents/stanford-postagger-full-2018-10-16/stanford-postagger-full-2018-10-16/models/french.tagger'
spanish_model = 'C:/Users/Cathal/Documents/stanford-postagger-full-2018-10-16/stanford-postagger-full-2018-10-16/models/spanish.tagger'
english_model = 'C:/Users/Cathal/Documents/stanford-postagger-full-2018-10-16/stanford-postagger-full-2018-10-16/models/english-bidirectional-distsim.tagger'

java_path = "C:/Program Files/Java/jdk-11.0.1/bin/java.exe"
os.environ['JAVAHOME'] = java_path


from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)
app.secret_key = "MY_SECRET_KEY"

pos_tagger_french = StanfordPOSTagger(french_model, jar, encoding='utf8' )
pos_tagger_spanish = StanfordPOSTagger(spanish_model, jar, encoding='utf8' )
pos_tagger_english = StanfordPOSTagger(english_model, jar, encoding='utf8' )

@app.route('/getPhraseTranslation', methods=['GET', 'POST'])
def getPhraseTranslation():
    phrase = request.form['phrase']
    language = request.form['language']
    translatedPhrase = get_translation(phrase, language)

    res_french = pos_tagger_french.tag(word_tokenize(translatedPhrase))
    res_english = pos_tagger_english.tag(word_tokenize(phrase))

    print(res_french)

    simplified_pos_tags_english = [(word, map_tag('en-ptb', 'universal', tag)) for word, tag in res_english]
    simplified_pos_tags_french = map_french_tag_to_universal(res_french)

    print(simplified_pos_tags_french)
    print(simplified_pos_tags_english)

    data = {"taggedPhrase":simplified_pos_tags_english, "taggedTranslation":simplified_pos_tags_french}

    return jsonify(data)

@app.route('/getPhraseTranslation1', methods=['GET', 'POST'])
def getPhraseTranslation1():
    phrase = request.form['phrase']
    language = request.form['language']

    translatedPhrase = get_translation_free(phrase, language)


    res_english = pos_tagger_english.tag(word_tokenize(phrase))
    simplified_pos_tags_english = [(word, map_tag('en-ptb', 'universal', tag)) for word, tag in res_english]
    simplified_pos_tags_translated = []
    if language == "fr":
        res_french = pos_tagger_french.tag(word_tokenize(translatedPhrase))
        print(res_french, res_english)
        simplified_pos_tags_translated = map_french_tag_to_universal(res_french)

    elif language == "es":
        res_spanish = pos_tagger_spanish.tag(word_tokenize(translatedPhrase))
        simplified_pos_tags_translated = map_spanish_tag_to_universal(res_spanish)


    taggedPhrase = ['_'.join(str(i) for i in tup) for tup in simplified_pos_tags_english]
    taggedTranslatedPhrase = ['_'.join(str(i) for i in tup) for tup in simplified_pos_tags_translated]
    taggedPhrase.append("NEWLINE")
    taggedPhrase = taggedPhrase + taggedTranslatedPhrase
    data = {"taggedText":taggedPhrase}
    print(data)
    return jsonify(data)

def get_translation_free(phrase, language):

    phrase = phrase.split()
    phrase = "+".join(phrase)
    r = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + language +  "&dt=t&q=" + phrase)
    content = json.loads(str(r.content, 'utf-8'))
    translatedPhrase = content[0][0][0]

    return translatedPhrase




def get_translation(phrase, language):
    result = translate_client.translate(
        phrase, target_language=language)
    return unescape(result['translatedText'])


'''NLTK 3.0 offers map_tag, which maps the Penn Treebank Tag Set to the Universal Tagset, a course tag set with the following 12 tags:

VERB - verbs (all tenses and modes)
NOUN - nouns (common and proper)
PRON - pronouns
ADJ - adjectives
ADV - adverbs
ADP - adpositions (prepositions and postpositions)
CONJ - conjunctions
DET - determiners
NUM - cardinal numbers
PRT - particles or other function words
X - other: foreign words, typos, abbreviations
. - punctuation
'''


def create_french_to_universal_dict():
    '''this function creates the dict we'll call below when we map french pos tags to the universal tag set'''
    french_to_universal = {}
    french_to_universal[u"ADJ"]    = u"ADJ"
    french_to_universal[u"ADJWH"]  = u"ADJ"
    french_to_universal[u"ADV"]    = u"ADV"
    french_to_universal[u"ADVWH"]  = u"ADV"
    french_to_universal[u"CC"]     = u"CONJ"
    french_to_universal[u"CLO"]    = u"PRON"
    french_to_universal[u"CLR"]    = u"PRON"
    french_to_universal[u"CLS"]    = u"PRON"
    french_to_universal[u"CS"]     = u"CONJ"
    french_to_universal[u"DET"]    = u"DET"
    french_to_universal[u"DETWH"]  = u"DET"
    french_to_universal[u"ET"]     = u"X"
    french_to_universal[u"NC"]     = u"NOUN"
    french_to_universal[u"N"] = u"NOUN"
    french_to_universal[u"NPP"]    = u"NOUN"
    french_to_universal[u"P"]      = u"ADP"
    french_to_universal[u"PUNC"]   = u"."
    french_to_universal[u"PRO"]    = u"PRON"
    french_to_universal[u"PROREL"] = u"PRON"
    french_to_universal[u"PROWH"]  = u"PRON"
    french_to_universal[u"V"]      = u"VERB"
    french_to_universal[u"VIMP"]   = u"VERB"
    french_to_universal[u"VINF"]   = u"VERB"
    french_to_universal[u"VPP"]    = u"VERB"
    french_to_universal[u"VPR"]    = u"VERB"
    french_to_universal[u"VS"]     = u"VERB"
    #nb, I is not part of the universal tagset--interjections get mapped to X
    french_to_universal[u"I"]      = u"X"
    return french_to_universal

def create_spanish_to_universal_dict():
    f = open("spanish_tags.txt", "r")
    lines = f.readlines()
    f.close()
    tag_dict = {}
    for line in lines:
        line = line.strip().split()
        tag_dict[line[0].lower()] = line[1]
    return tag_dict

french_to_universal_dict = create_french_to_universal_dict()
spanish_to_universal_dict = create_spanish_to_universal_dict()

def map_spanish_tag_to_universal(list_of_spanish_tag_tuples):
    '''this function reads in a list of tuples (word, pos) and returns the same list with pos mapped to universal tagset'''
    return [ (tup[0], spanish_to_universal_dict[ tup[1][:2] ]) for tup in list_of_spanish_tag_tuples ]

def map_french_tag_to_universal(list_of_french_tag_tuples):
    '''this function reads in a list of tuples (word, pos) and returns the same list with pos mapped to universal tagset'''
    return [ (tup[0], french_to_universal_dict[ tup[1] ]) for tup in list_of_french_tag_tuples ]

#app.run(port=5001)