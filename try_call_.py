import requests,json

from nltk.parse import stanford

from nltk.parse.dependencygraph import DependencyGraph

import networkx as nx
import matplotlib.pyplot as plt

from corenlp import CoreNLPClient

from tools import *

lac2penn={"n":"NN",
     "nr":"NR",
     "nz":"NR",
     "a":"",#"JJ",#?? VA
     "m":"",#"CD",#??
     "c":"CC",
     "PER":"NR",
     "f":"LC",
     "ns":"NR",
     "v":"VV",
     "ad":"AD",
     "q":"M",
     "u":"",#"DEG",#????? DEC DEG DER DEV SP AS ETC MSP
     "LOC":"NR",
     "s":"",#"NR",#??处所名词
     "nt":"NR",
     "vd":"",#"VV",#??动副词
     "an":"",#"NN",#??名形词
      "r":"PN",
     "xc":"",#"MSP",#??其他虚词
     "t":"NT",
     "nw":"NR",
     "vn":"NN",
     "d":"AD",
     "p":"P",
     "w":"PU",
     "TIME":"NT",
     "[D:PROSECUTOR]":"NR",
"[D:NOUN_LEGAL]":"NN",
          "ORG":"NR"
     }

STANFORD_ROOT = 'D:\\stanford-parser\\stanford-parser-full-2018-10-17\\stanford-parser-full-2018-10-17\\'
PARSER_PATH = STANFORD_ROOT + 'stanford-parser.jar'
MODEL_PATH= STANFORD_ROOT + 'stanford-parser-3.9.2-models.jar'
CHN_MODEL_PATH= STANFORD_ROOT + 'stanford-chinese-corenlp-2018-10-05-models.jar'
PCFG_PATH="edu/stanford/nlp/models/lexparser/chinesePCFG.ser.gz"

def call_api(data,url="http://localhost:9001",encoding='utf8'):

    default_properties = {
        'outputFormat': 'json',
        'annotators': "tokenize,ssplit,pos,lemma,ner,parse,depparse",#tokenize,pos,lemma,ssplit',
        'tokenize.whitespace':'true',
        'pos.tagSeparator':'/',
        'tagSeparator':'/',
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

# print(call_api('你/NN 好/VV 啊/VV\n'))

parser=stanford.StanfordDependencyParser(path_to_jar=PARSER_PATH,path_to_models_jar=CHN_MODEL_PATH,model_path=PCFG_PATH)

# for i in parser.tagged_parse_sents([[("你","NN"),("好","VV")]]):
#     for j in i:
#         print(j)
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
g = line_generator("final_all_data/first_stage/train.json")

def build_token_dict(dep_parser_result,lac_tagged):
    tokenDict={}

    lac_tagged=[{'word':"[ROOT]","type":"[ROOT]",'start':0,'length':0}]+lac_tagged

    for DepGraph in dep_parser_result:
            # nx.draw(DepGraph.nx_graph())
    #             # plt.show()
            for nodeIndex in [k for k in DepGraph.nodes]:
                # print(DepGraph.nodes[nodeIndex]['word'],lac_tagged[nodeIndex]['word'])
                # if nodeIndex>0:
                #         assert DepGraph.nodes[nodeIndex]['word']==lac_tagged[nodeIndex]['word']
                tokenDict[nodeIndex]={
                    "index":nodeIndex,
                    "word":DepGraph.nodes[nodeIndex]['word'],
                    "pos":DepGraph.nodes[nodeIndex]['tag'],
                    "lac_pos":lac_tagged[nodeIndex]['type'],
                    "characterOffsetBegin":int(lac_tagged[nodeIndex]['start']),
                    "characterOffsetEnd":int(lac_tagged[nodeIndex]['start'])+int(lac_tagged[nodeIndex]['length'])-1,
                    "ref":{
                        "dep":DepGraph.nodes[nodeIndex]['rel'],
                        "governor":DepGraph.nodes[nodeIndex]['head'],
                        "governorGloss":DepGraph.nodes[DepGraph.nodes[nodeIndex]['head']]['word'],
                        "dependentGloss":DepGraph.nodes[nodeIndex]['word']
                    }
                }

    return tokenDict

# i=0
# articles=[]
# taggeds=[]
while True:
    try:
        articleJSON = json.loads(g.__next__())
    except StopIteration:
        break

    tagged=lac_cut(articleJSON['fact'])
    print(call_stanford(tagged))
#
#     tagged=lac_cut(articleJSON['fact'])
#     sentence=[]
#     for w in tagged:
#         if lac2penn[w['type']]:
#             sentence.append((w['word'],lac2penn[w['type']]))
#         else:
#             sentence.append((w['word'],))
#
#     articles.append(sentence)
#     taggeds.append(tagged)
#
#     if i>10:break
#     else:i+=1
#
# dep_result=parser.tagged_parse_sents(articles)
# for articleIndex in range(len([i for i in dep_result])):
#     print (build_token_dict(dep_result[articleIndex],taggeds[articleIndex]))



    # for i in dep_result:
    #     for j in i:
    #             print(j)
    #
    #
    # break

