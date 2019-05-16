"""
这个文件存放共用的工具函数，nltk等库仅支持cpython
导入该文件也会导入tools_general.py

"""

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

from tools_general import *

def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def async_run_draw(sentence_repr,daemon=True):
    drawThread = Thread(target=run_draw, args=((sentence_repr,)))
    drawThread.daemon = daemon
    drawThread.start()
    print("start")



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

