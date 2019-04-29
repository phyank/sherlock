import json,os,multiprocessing,re,traceback

from urllib.request import urlopen
from urllib.parse import urlencode
from threading import Thread
from copy import deepcopy
import requests

import jieba
import jieba.posseg as pseg
from nltk.parse import stanford,corenlp
import nltk.sem
from nltk.tree import Tree

import py2neo

from definitions import *

PATTERN_MIN_FREQ=10

lac2penn={"n":"NN",
     "nr":"NR",
     "nz":"NR",
     "a":"",#?? VA JJ
     "m":"",#??CD
     "c":"CC",
     "PER":"NR",
     "f":"",
     "ns":"NR",
     "v":"VV",
     "ad":"",
     "q":"M",
     "u":"",#????? DEC DEG DER DEV SP AS ETC MSP
     "LOC":"NR",
     "s":"",#??处所名词
     "nt":"NR",
     "vd":"",#??d VV
     "an":"",#??名形词
      "r":"PN",
     "xc":"",#??其他虚词
     "t":"NT",
     "nw":"NR",
     "vn":"",
     "d":"AD",
     "p":"P",
     "w":"PU",
     "TIME":"NT",
     "[D:PROSECUTOR]":"NR",
    "[D:LEGAL_NOUN]":"NN",
"[D:NOUN_LEGAL]":"NN",
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
"[D:LEGAL_NOUN]":30,
"[D:NOUN_LEGAL]":30,
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

def first(s):
    for i in s:
        return i

def first_N(s,n=1):
    result=[]
    for i in s:
        result.append(i)
        if len(result)==n:
            break
    return result

def new_token(index,word,pos,lac_pos,dep,head,begin,end,prefix=""):
    return {
            "index":str(index),
            "word":word,
            "pos":pos,
            "lac_pos":lac_pos,
            "dep":dep,
            "head":str(head),
            "prefix":prefix,
            "begin":begin,
            "end":end,
            "ver":"new",
            "_type":"StandardWordToken"
        }

def new_sentence_repr(index,tokenDict,manual_relations=tuple()):
    return {
        "index":str(index),
        "tokens":tokenDict,
        "manual_relations":manual_relations,
        "_type": "StandardSentenceRepr"
    }

def old_word_token_to_new(old):
    if "ver" in old and old['ver']=="new":
        return old
    else:
        return {
            "index":old['index'],
            "word":old['word'],
            "pos":old['pos'],
            "lac_pos":old['lac_pos'],
            "dep":old["ref"]["dep"],
            "head":old["ref"]["governor"],
            "prefix":old['prefix'],
            "begin":old["characterOffsetBegin"],
            "end":old['characterOffsetEnd'],
                "ver":"new"
        }

def print_local_when_exception(func):
    def inner(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            print(e.__class__.__name__)
            print(traceback.format_exc())
            localShot=deepcopy(locals())
            for k in localShot:
                if k not in ('__builtins__', 'sys', 'os', '__warningregistry__'):
                    print("%s   :   %s"%(k,repr(localShot[k])))
            raise Exception
    return inner

def line_generator(fn,encoding='utf8'):
    jf = open(fn,encoding=encoding)
    while True:
        line=jf.readline()
        if line:
            if line[-1]=="\n":
                line=line[:-1]
            yield line
        else:
            return

def pos2i(pos):
    try:
        return lac2int[pos]
    except KeyError:
        # print("unknown pos tag %s"%pos)
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

        if w['word'] in "。？！……":
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
                line_index,head=str(int(last_index)+int(line_index)),str(int(last_index)+int(head) if int(head)!=0 else 0)
                tokenDict[line_index] =new_token(index=line_index,
                                                 word=word,
                                                 pos=tag,
                                                 lac_pos=tagged[int(line_index)-1]['type'],
                                                 begin=int(tagged[int(line_index)-1]['start']),
                                                 end=int(tagged[int(line_index)-1]['start']) + int(tagged[int(line_index)-1]['length']) - 1,
                                                 dep=rel,
                                                 head=head)
        last_index=line_index

    tokenDict['0']=new_token(index='0',word="[ROOT]",pos=None,lac_pos=None,dep=None,head=None,begin=None,end=None)

    for k in special_r:
        tokenDict[str(k)]=new_token(index=str(k),word=special_r[k],pos=None,lac_pos=None,dep=None,head=None,begin=None,end=None)
    # print(tokenDict)
    return tokenDict

def make_word_repr(x,tokenDict):
    return ("%s(%s%s%s->%s)" % (
                x['prefix']+">>"+x['word'], x['index'], x['pos'], x['lac_pos'],
                tokenDict[x['head']]['word'] if x['head'] in tokenDict else "PUNC"))

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

    return generate_sentence_repr_from_corenlp_result(rj['sentences'])#Tree.fromstring(rj['sentences'][0]['parse']),rj['sentences'][0]['enhancedPlusPlusDependencies']

def generate_sentence_repr_from_corenlp_result(sentences):
    index=0
    standard_sentences=[]
    for sentence in sentences:
        thisTokenDict=build_token_dict_from_corenlp_output(sentence)
        standard_sentences.append(new_sentence_repr(index=index,
                                                    tokenDict=thisTokenDict))

    return standard_sentences


def build_token_dict_from_corenlp_output(sentence):
    tokenDict={}
    for word in sentence['tokens']:
        tokenDict[word['index']] = word
        word['fullname'] = \
            word['word']

        word['prefix'] = \
            ''


    ranked_tokens = {}
    for idx in sorted([i['index'] for i in sentence['tokens']], reverse=True):
        ranked_tokens[idx] = new_token(index=idx,
                                       word=tokenDict[idx],
                                       pos=tokenDict[idx]['pos'],
                                       lac_pos="Not filled",
                                       begin=tokenDict[idx]["characterOffsetBegin"],
                                       end=tokenDict[idx]["characterOffsetEnd"],
                                       dep=tokenDict[idx]["ref"]['dep'],
                                       head=tokenDict[idx]["ref"]['governor']
                                       )

    for word_index in ranked_tokens:
        word = ranked_tokens[word_index]
        if word['head'] != 0 and tokenDict[word['head']]['pos'] in ("NN", "NR") and \
                tokenDict[word['index']]['pos'] not in ("PU"):

            tokenDict[word['head']]['prefix'] = \
                word['word'] + "|" + tokenDict[word['head']]['prefix']

    return ranked_tokens