import json,os,multiprocessing,re

from urllib.request import urlopen
from urllib.parse import urlencode

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



def jieba_cut_sentences(article):
    lastSentence=[]
    for word in jieba.cut(article):
        if word in "。；？！?!":
            yield " ".join(lastSentence)
            lastSentence=[]
        else:
            lastSentence.append(word)

def run_parser(limit=5,skip=1,num=0,name='result',write_file=True):
    g = line_generator("final_all_data/restData/rest_data.json")
    parser=stanford.StanfordParser(path_to_jar=PARSER_PATH,path_to_models_jar=CHN_MODEL_PATH,model_path=PCFG_PATH)
    # parser=corenlp.CoreNLPParser(url="http://localhost:9001")
    with open(name+str(num),'w') as output:

        loop=-1
        while True:
            loop+=1
            if loop%10==1:
                print("Process %d parsed %d records."%(num,loop))
            articleJSON=g.__next__()
            if not articleJSON:break
            if limit and loop>limit:break
            if skip!=1:
                if loop%skip!=num:
                    continue
            articleJSON = json.loads(articleJSON)
            article=articleJSON['fact']
            factCut=[]
            for sentence in lac_cut(article):#jieba_cut_sentences(article):
                for line in parser.raw_parse(sentence):
                    # print(Tree.fromstring(line.pformat()))
                    # if not write_file:
                    #line=call_api(sentence)
                    print(get_relations(line))
                    # nltk.sem.extract_rels("NR","NN",line,corpus='')
                    line.draw()
                    factCut.append(line.pformat())
            # print(factCut)
            articleJSON['fact_cut']=factCut

            if write_file:
                output.writelines((json.dumps(articleJSON,ensure_ascii=False),))
            else:
                print("factCut:%s"%factCut)

        print("Parse %d records finished."%(loop+1))

def run_depparser(limit=5,skip=1,num=0,name='result',write_file=True):
    g = line_generator("final_all_data/restData/rest_data.json")
    # parser=corenlp.CoreNLPParser(url="http://localhost:9001")
    with open(name+str(num),'w') as output:

        loop=-1
        while True:
            loop+=1
            if loop%10==1:
                print("Process %d parsed %d records."%(num,loop))
            articleJSON=g.__next__()
            if not articleJSON:break
            if limit and loop>limit:break
            if skip!=1:
                if loop%skip!=num:
                    continue
            articleJSON = json.loads(articleJSON)
            article=articleJSON['fact']
            factCut=[]
            for sentence in lac_cut(article):#jieba_cut_sentences(article):
                tree,dep=call_api(sentence)
                print(type(dep))
                # for line in parser.raw_parse(sentence):
                    # print(Tree.fromstring(line.pformat()))
                    # if not write_file:
                    #line=call_api(sentence)
            #         print(get_relations(line))
            #         # nltk.sem.extract_rels("NR","NN",line,corpus='')
            #         line.draw()
            #         factCut.append(line.pformat())
            # # print(factCut)
            # articleJSON['fact_cut']=factCut
            #
            # if write_file:
            #     output.writelines((json.dumps(articleJSON,ensure_ascii=False),))
            # else:
            #     print("factCut:%s"%factCut)

        print("Parse %d records finished."%(loop+1))
#
# def get_leave_str(t):
#     return " ".join(t.leaves())
#
# def parse_IP(t):
#     relations=[]
#     pending_action=None
#     pending_subject=None
#     pending_object=None
#     for child in t:
#         label=child.label()
#         if label=="IP":
#             relations.extend(parse_IP(child))
#         elif label in "NP":
#             if pending_action:
#                 pending_object=get_leave_str(child)
#             else:
def token_repr(t):
    return " ".join(t.leaves())

def parse_NP(t):
    p_noun=None

    ntime=None

    nouns=[]

    noun_adjacent=False
    for child in t:
        child_label=child.label()

        if child_label in ("CC" , "PU"):
            noun_adjacent=False
        elif child_label=="NP":
            if not noun_adjacent:
                n,t=parse_NP(child)
                nouns.extend(n)
                if t:ntime=t
            else:
                p_noun = (p_noun if p_noun else "") + token_repr(child)
        elif child_label in ("NN","NR"):
            if noun_adjacent:
                p_noun=(p_noun if p_noun else "")+token_repr(child)
            else:
                if p_noun:
                    nouns.append(p_noun)
                p_noun=token_repr(child)

            noun_adjacent=True
        elif child_label=="NT":
            ntime=token_repr(child)
        elif child_label=="QP":
            p_noun=(p_noun if p_noun else "")+token_repr(child)

        else:
            print("NP jump label %s"%child_label)
    if p_noun:
        nouns.append(p_noun)

    print("np get",nouns)
    return nouns,ntime

def parse_PP(t):
    p_P=None
    p_other=''

    for child in t:
        child_label=child.label()
        if child_label=="P":
            p_P=token_repr(child)
        else:
            p_other+=token_repr(child)

    print("pp get ",p_P,p_other)
    return ((p_P,p_other))



def parse_VP(t):
    relations=[]
    actions=[]
    reverse=False

    p_actions=[]
    p_action=None
    p_object=[]
    p_env=[]


    verb_adjacent=False
    for child in t:
        child_label=child.label()
        if child_label in ("VV","VE","VA","VC"):
            if p_action:
                if not verb_adjacent:
                        actions.append((p_action,p_object,p_env,False))
                        p_action=" ".join(child.leaves())
                else:
                    p_action+=" ".join(child.leaves())
            # p_action=" ".join(child.leaves())
            else:
                p_action = " ".join(child.leaves())
            verb_adjacent=True
        elif child_label=="VP":
            if not verb_adjacent:
                if p_action:
                    actions.append((p_action,p_object,p_env,False))
                    p_action=None
                if p_actions:
                    for action in p_actions:
                        action[ENV].extend(p_env)
                        actions.append((action[ACTION], action[OBJECT], action[ENV], action[IF_REVERSE]))
                    p_actions=[]

            if len(child)==1:
                p_action=" ".join(child.leaves())
            else:
                child_actions,child_relations=parse_VP(child)
                p_actions=child_actions
                relations.extend(child_relations)
        elif child_label=="NP":
            nouns,ntime=parse_NP(child)
            p_object.extend(nouns)
        elif child_label in ("PU","CC"):
            verb_adjacent=False

        elif child_label=="QP":
            p_object.append(token_repr(child))
        elif child_label=="ADVP":
            p_env.append(token_repr(child))
        elif child_label=="PP":
            p_env.append(parse_PP(child))
        elif child_label=="P":
            if "被" in "".join(child.leaves()):
                reverse=True
        # elif child_label=="BA":
        #     if "将" in "".join(child.leaves()):
        #         reverse=True
        elif child_label=="IP":
            if len(child)>1:
                child_relations=get_relations(child)
                p_object=Fact(root=child,relations=child_relations)
                relations.extend(child_relations)
            else:
                for childchild in child:
                    cc_label=childchild.label()
                    if cc_label=="VP":
                        a,r=parse_VP(childchild)
                        p_actions.extend(a)
                        relations.extend(r)
                    elif cc_label=="NP":
                        nouns, ntime = parse_NP(childchild)
                        p_object.extend(nouns)
                    else:
                        print("pv skip %s"%cc_label)

    for action in p_actions:
        action[ENV].extend(p_env)
        actions.append((action[ACTION],action[OBJECT],action[ENV],action[IF_REVERSE]))
    if p_action:
        actions.append((p_action,p_object,p_env,reverse))

    print("vp get ",actions)
    return actions,relations
#R=(A,R,B,C,Reverse)
#C=(p,N)

class Fact:
    def __init__(self,relations=None,root=None):
        self.root=root
        self.name=" ".join(root.leaves())
        self.relations=relations
    def __repr__(self):
        return "FACT: %s"%self.name

def get_relations(t):
    print("walk to %s"%t.label())
    relations=[]
    pending_subject=None
    pending_actions=[]
    pending_env=[]
    for child in t:
        if child.label() in ("IP","ROOT"):
            relations.extend(get_relations(child))
        elif child.label()=="NP":
            pending_subject=(" ".join(child.leaves()))
        elif child.label()=="VP":
            pending_actions,child_relations=parse_VP(child)
            relations.extend(child_relations)
        elif child.label()=="PP":
            pending_env.append(parse_PP(child))

    for action in pending_actions:
        action[ENV].extend(pending_env)
        if action[IF_REVERSE]:
            relations.append((action[OBJECT],action[ACTION],pending_subject,action[ENV]))
        else:
            relations.append((pending_subject, action[ACTION],action[OBJECT] , action[ENV]))
    return relations

class ParserStatus:
    def __init__(self):
        self.lastNoun=None
        self.lastU=None
        self.lastLocation=None
        self.lastAction={"action":None,"object":[],"prefix":[]}

        self.pendingNoun = None
        self.pendingPerson = None
        self.pendingLocation = None
        self.pendingAction = {"action": None, "object": [], "prefix": []}

        self.fact = {"prosecutor": None,
                 "time": [],
                 "location": [],
                 "subject": None,
                 "action2object": []}

    def set_last_noun(self,word):

        self.lastNoun=word
        self.lastU=None
        self.lastAction={"action":None,"object":[],"prefix":[]}
        self.lastLocation=None

    def set_last_u(self, word):
        self.lastNoun = None
        self.lastU = word
        self.lastAction = {"action": None, "object": [], "prefix": []}
        self.lastLocation = None

    def set_last_location(self,word):
        self.lastNoun = None
        self.lastU = None
        self.lastAction = {"action": None, "object": [], "prefix": []}
        self.lastLocation = word

    def set_last_action(self,action=None,object=None,prefix=None):
        if action:
            self.lastAction['action']=action
        if object:
            self.lastAction['object'].append(object)
        if prefix:
            self.lastAction['prefix'].append(prefix)

        self.lastNoun = None
        self.lastU = None
        self.lastLocation = None

    def clean_last(self):
        self.lastNoun = None
        self.lastU = None
        self.lastLocation = None
        self.lastAction = {"action": None, "object": [], "prefix": []}

    def write_fact(self,time=None,location=None,subject=None,a2o=None,prosecutor=None):
        if prosecutor:
            self.fact["prosecutor"]=prosecutor
        if time:
            self.fact['time'].append(time)
        if location:
            self.fact['location'].append(location)
        if subject:
            if self.fact['subject']:
                print("WARNING: overwrite subject %s to %s"%(self.fact['subject']['word'],subject['word']))
            if self.pendingAction:
                self.pendingAction={"action": None, "object": [], "prefix": []}
            self.fact['subject']=subject
        if a2o:
            self.fact['action2object'].append(a2o)

    def set_pending_action(self, action=None, object=None, prefix=None):
        if action:
            if self.pendingAction['action']:
                if self.fact['subject']:
                    self.fact["action2object"].append(self.pendingAction)
            self.pendingAction['action'] = action
        if object:
            self.pendingAction['object'].append(object)
        if prefix:
            self.pendingAction['prefix'].append(prefix)

def lac_cut(article):
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
        yield(" ".join(map(lambda w:w['word'],sentence)))

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

            # line.draw()


def test_stanford():
    workers = 1
    process = []
    for i in range(workers):
        subprocess = multiprocessing.Process(target=run_parser, args=(20, workers, i,'r',False))
        subprocess.daemon = True
        subprocess.start()
        process.append(subprocess)
    for p in process:
        p.join()

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

    return Tree.fromstring(rj['sentences'][0]['parse']),rj['sentences'][0]['enhancedPlusPlusDependencies']

def test_oie():
    g = line_generator("final_all_data/first_stage/train.json")
    for i in range(5):
        line = json.loads(g.__next__())

        result=call_api(line['fact'])
        # print(result)
        for s in result['sentences']:
            print("________________________________")
            print(s['openie'])
            print(s['tokens'])

def test_lac():
    g = line_generator("final_all_data/first_stage/train.json")
    for i in range(1):
        line = json.loads(g.__next__())

        result=urlopen("http://127.0.0.1:18080/lac",urlencode({"passwd":'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                                 "sentence": line['fact']}).encode('utf8')).read().decode('utf8')

        print(result)

        words=result.split("\t")

        sentences=[]
        sentence=[]
        for word in words:
            word=word.split(" ")
            if word[1]=="w" and word[0] in "。！？":
                sentences.append(sentence)
                sentence=[]
            else:
                sentence.append({"word":word[0],"type":word[1],"start":word[2],"length":word[3]})
        for s in sentences:
            print(s)

            status=ParserStatus()
            for word in s:

                if "PROSECUTOR" in word['type']:
                    status.write_fact(prosecutor=word['word'])
                elif word['type']=="TIME":
                    status.write_fact(time=word)
                    status.clean_last()
                    continue
                elif word['type']=="LOC":
                    if status.lastLocation:
                        status.lastLocation['word']+=word['word']
                        status.set_last_location(status.lastLocation)
                        continue
                    else:
                        status.write_fact(location=word)
                        status.set_last_location(word)
                        continue
                else:
                    if word['type']=="PER":
                        if not status.fact['subject']:
                            subject=word['word']
                            if status.lastNoun:
                                subject=status.lastNoun['word']+subject
                            status.write_fact(subject=subject)

                            status.set_last_noun(word)
                            continue
                        elif status.pendingAction['action']:
                            if not status.pendingAction['object']:
                                status.set_pending_action(object=word)
                                status.clean_last()
                                continue
                            else:
                                status.pendingPerson=word

                                status.clean_last()
                                continue
                    elif re.search("^n",word['type']):
                        if status.lastLocation:
                            status.lastLocation['word']=status.lastLocation['word']+word['word']

                            status.set_last_location(status.lastLocation)
                            continue
                        elif status.lastNoun:
                            if status.lastU:
                                word['word']=status.lastNoun['word']+status.lastU['word']+word['word']
                            else:
                                word['word'] =status.lastNoun['word']+ word['word']
                            status.set_last_noun(word)
                            continue
                        elif status.pendingPerson:
                            if status.lastU:
                                word['word']=status.pendingPerson['word']+status.lastU['word']+word['word']
                            else:
                                word['word'] = status.pendingPerson['word'] +  word['word']

                            status.set_last_noun(word)
                            continue
                        elif status.pendingAction['action']:
                            status.set_pending_action(object=word)

                            status.set_last_noun(word)
                            continue
                    elif word['type']=='w':
                        if status.pendingAction['action']:
                            status.set_pending_action(object=status.lastNoun)
                            status.write_fact(a2o=status.pendingAction)
                            status.pendingAction={"action": None, "object": [], "prefix": []}
                        status.clean_last()
                        continue
                    elif re.search("^v",word['type']):
                        if status.lastAction['action']:
                            word['word']=status.lastAction['action']['word']+word['word']
                            status.set_pending_action(action=word)

                            status.set_last_action(word)
                            continue
                        else:
                            status.set_last_action(action=word)
                            status.set_pending_action(action=word)
                            continue
                    elif word['type']=='u':
                        status.set_last_u(word)
                    else:
                        print("missing:%s"%word['type'])

                        status.clean_last()
                        continue

            print(status.fact)




if __name__=="__main__":
    # test_stanford()
    #test_oie()
    run_parser(200,5,0,'r',False)
    # for s in lac_cut(w):
    #     r=call_api(s)
    #     print(r)