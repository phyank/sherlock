import json,os,multiprocessing,re

from urllib.request import urlopen
from urllib.parse import urlencode
from threading import Thread

import requests

import jieba
import jieba.posseg as pseg
from nltk.parse import stanford,corenlp
import nltk.sem
from nltk.tree import Tree

import py2neo

lac2penn={"n":"NN",
     "nr":"NR",
     "nz":"NR",
     "a":"VA",#?? JJ
     "m":"CD",#??
     "c":"CC",
     "PER":"NR",
     "f":"LC",
     "ns":"NR",
     "v":"VV",
     "ad":"AD",
     "q":"M",
     "u":"DEG",#????? DEC DEG DER DEV SP AS ETC MSP
     "LOC":"NR",
     "s":"NR",#??处所名词
     "nt":"NR",
     "vd":"VV",#??动副词
     "an":"NN",#??名形词
      "r":"PN",
     "xc":"MSP",#??其他虚词
     "t":"NT",
     "nw":"NR",
     "vn":"NN",
     "d":"AD",
     "p":"P",
     "w":"PU",
     "TIME":"NT",
     "[D:PROSECUTOR]":"NR",
          "ORG":"NR"
     }

ACTION=0
OBJECT=1
ENV=2
IF_REVERSE=3

STANFORD_ROOT = 'D:\\stanford-parser\\stanford-parser-full-2018-10-17\\stanford-parser-full-2018-10-17\\'
PARSER_PATH = STANFORD_ROOT + 'stanford-parser.jar'
MODEL_PATH= STANFORD_ROOT + 'stanford-parser-3.9.2-models.jar'
CHN_MODEL_PATH= STANFORD_ROOT + 'stanford-chinese-corenlp-2018-10-05-models.jar'

PCFG_PATH="edu/stanford/nlp/models/lexparser/chinesePCFG.ser.gz"

JAVA_HOME = os.environ.get("JAVA_HOME")
if not JAVA_HOME:
    JAVA_HOME = 'C:\\PROGRA~1\\Java\\JDK-10~1.2'

def line_generator(fn,encoding='utf8'):
    jf = open(fn,encoding=encoding)
    while True:
        line=jf.readline()
        if line:
            yield line
        else:
            return

def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def async_run_draw(sentence_repr,daemon=True):
    drawThread = Thread(target=run_draw, args=((sentence_repr,)))
    drawThread.daemon = daemon
    drawThread.start()
    print("start")

def lac_cut(article):
    result = urlopen("http://127.0.0.1:18080/lac",
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    print(result)

    words = result.split("\t")

    a=[]
    for word in words:
        word = word.split(" ")

        a.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})

    return a

def tokenized_repr(wordlist):
    return (" ".join(map(lambda w:w['word'],wordlist)))


def lac_cut_break(article):
    result = urlopen("http://127.0.0.1:18080/lac",
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    print(result)

    words = result.split("\t")

    sentences = []
    sentence = []
    for word in words:
        word = word.split(" ")
        if word[1] == "w" and word[0] in "。！？":
            sentence.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})
            sentences.append(sentence)
            sentence = []
        else:
            sentence.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})

    for sentence in sentences:
        yield (" ".join(map(lambda w:w['word'],sentence)))

def lac_cut_pos(article):
    result = urlopen("http://127.0.0.1:18080/lac",
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    print(result)

    words = result.split("\t")

    sentences = []
    sentence = []
    for word in words:
        word = word.split(" ")
        if word[1] == "w" and word[0] in "。！？":
            sentence.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})
            sentences.append(sentence)
            sentence = []
        else:
            sentence.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})

    for sentence in sentences:
        s=[]
        for w in sentence:
            s.append((w['word'],lac_to_penn_pos(w['type'])))
        yield s

def lac_to_penn_pos(t):
    return lac2penn[t]

def jieba_poseg_cut():
    g = line_generator("final_all_data/first_stage/train.json")
    for i in range(50):
        line = json.loads(g.__next__())
        print(" ".join([word + "\\" + label for word, label in pseg.cut(line['fact'])]))

def call_api(data,url="http://localhost:9001",encoding='utf8'):

    default_properties = {
        'outputFormat': 'json',
        'annotators': "tokenize,ssplit,pos,lemma,ner,parse,depparse",#tokenize,pos,lemma,ssplit',
        'tokenize.whitespace':'true',
    }

    default_properties.update({})
    session=requests.Session()
    response =session.post(
        url,
        params={'properties': json.dumps(default_properties)},
        data=data.encode(encoding),
        timeout=60,
    )
    rj=response.json()

    return rj#Tree.fromstring(rj['sentences'][0]['parse']),rj['sentences'][0]['enhancedPlusPlusDependencies']

def build_token_dict(sentence):
    tokenDict={}
    for word in sentence['tokens']:
        tokenDict[word['index']] = word
        word['ref']['fullname'] = \
            word['word']

        word['prefix'] = \
            ''


    ranked_tokens = {}
    for idx in sorted([i['index'] for i in sentence['tokens']], reverse=True):
        ranked_tokens[idx] = tokenDict[idx]

    for word_index in ranked_tokens:
        word = ranked_tokens[word_index]
        if word['ref']['governor'] != 0 and tokenDict[word['ref']['governor']]['pos'] in ("NN", "NR") and \
                tokenDict[word['ref']['dependent']]['pos'] not in ("PU"):
            # print(word)
            # print("%s PING %s"%(tokenDict[word['ref']['governor']]['ref']['fullname'],word['word']))
            tokenDict[word['ref']['governor']]['ref']['fullname'] = \
                word['word'] + "|" + tokenDict[word['ref']['governor']]['ref']['fullname']
            tokenDict[word['ref']['governor']]['prefix'] = \
                word['word'] + "|" + tokenDict[word['ref']['governor']]['prefix']

    return ranked_tokens