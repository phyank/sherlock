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

PATTERN_MIN_FREQ=10

lac2penn={"n":"NN",
     "nr":"NR",
     "nz":"NR",
     "a":"JJ",#?? VA
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
     "vd":"VV",#??d
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
    "[D:LEGAL_NOUN]":"NN",
"[D:NR]":"NR",
          "ORG":"NR"
     }

lac2int={
    "n":0,
     "nr":1,
     "nz":2,
     "a":3,#?? JJ
     "m":4,#??
     "c":5,
     "PER":6,
     "f":7,
     "ns":8,
     "v":9,
     "ad":10,
     "q":11,
     "u":12,#????? DEC DEG DER DEV SP AS ETC MSP
     "LOC":13,
     "s":14,#??处所名词
     "nt":15,
     "vd":16,#??动副词
     "an":17,#??名形词
      "r":18,
     "xc":19,#??其他虚词
     "t":20,
     "nw":21,
     "vn":22,
     "d":23,
     "p":24,
     "w":25,
     "TIME":26,
     "[D:PROSECUTOR]":27,
         "ORG":28,
         "None":29,
"[D:LEGAL_NOUN]":30,
"[D:NR]":30,
         "OTHER":99
     }

comma_marker={"comma":1,
              "no_comma":0}

CLASS={"Y":1,
       "N":0}

CLASS_LIT={1:"Y",
           0:"N"}

ACTION=0
OBJECT=1
ENV=2
IF_REVERSE=3

STANFORD_ROOT = 'D:\\stanford-parser\\stanford-parser-full-2018-10-17\\stanford-parser-full-2018-10-17\\'
PARSER_PATH = STANFORD_ROOT + 'stanford-parser.jar'
MODEL_PATH= STANFORD_ROOT + 'stanford-parser-3.9.2-models.jar'
CHN_MODEL_PATH= STANFORD_ROOT + 'stanford-chinese-corenlp-2018-10-05-models.jar'

PCFG_PATH="edu/stanford/nlp/models/lexparser/chinesePCFG.ser.gz"

PASSWORD='rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i'

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

def pos2i(pos):
    try:
        return lac2int[pos]
    except KeyError:
        print("unknown pos tag %s"%pos)
        return lac2int["OTHER"]


def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def async_run_draw(sentence_repr,daemon=True):
    drawThread = Thread(target=run_draw, args=((sentence_repr,)))
    drawThread.daemon = daemon
    drawThread.start()
    print("start")

def call_stanford(tagged,host="http://127.0.0.1:9001/stanford"):
    sentences=[]
    sentence = []
    tokenDict={}
    for w in tagged:
        if lac2penn[w['type']]:
            sentence.append(w['word'] + "/" + lac2penn[w['type']])
        else:
            sentence.append(w['word'])

        if w['word'] in "。；？！……":
            sentences.append(sentence)
            sentence=[]
        #I want to break the paragraph into sentences but the Parser still cut as a paragraph

    last_index=0
    for s in sentences:
        tmp_token_dict={}
        line_index=0
        result=urlopen(host,data=urlencode({"sentence":" ".join(s) +"\n",
                                 "passwd":PASSWORD}).encode('utf8')).read().decode("utf8")
    # print(result)
        for token in result.split("\n"):
            # print(repr(token))
            try:
                line_index, word, lemma, ctag, tag, feats, head, rel, _, _ =token.split("\t")
            except ValueError:
                continue
            else:
                line_index,head=last_index+int(line_index),(last_index+int(head) if int(head)!=0 else 0)

                tokenDict[line_index]={
                    "index": line_index,
                    "word": word,
                    "pos": tag,
                    "lac_pos": tagged[line_index-1]['type'],
                    "characterOffsetBegin": int(tagged[line_index-1]['start']),
                    "characterOffsetEnd": int(tagged[line_index-1]['start']) + int(tagged[line_index-1]['length']) - 1,
                    "ref": {
                        "dep": rel,
                        "governor": head,
                        "governorGloss": "",
                        "dependentGloss": word
                    }
                }
        last_index=line_index

    tokenDict[0]={"word":"[ROOT]","ref":{"governorGloss":"","governor":0}}
    for tokenIndex in tokenDict:
        tokenDict[tokenIndex]['ref']["governorGloss"]=tokenDict[tokenDict[tokenIndex]['ref']["governor"]]['word']

    return tokenDict

def lac_cut(article,port=18080):
    result = urlopen("http://127.0.0.1:%d/lac"%port,
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    print(result)

    words = result.split("\t")

    a=[]
    for word in words:
        word = word.split(" ")
        if len(word)!=4:continue
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