"""
这个文件存放共用的工具函数，该文件兼容pypy3

"""

import json,os,re,traceback,array

from urllib.request import urlopen
from urllib.parse import urlencode
from copy import deepcopy

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
          "ORG":"NR",
          "BAD":""
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

# EXEMPT={"经济技术开发区","高新技术开发区","开发区","高新区","保税区","市","县","区","自治区"}

COMMAS=",，、"
STOPS="。；？！?!"

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

def med(a,b):
    """
    Minimum edit distance algorithm(Levenshtein) implementation using dynamic programming

    :param a: str a
    :param b: str b
    :return: minimum edit distance
    """
    lena,lenb=(len(a),len(b))
    memo=array.array('l',[-1 for i in range((lena+1)*(lenb+1))])

    for i in range(0,lena+1):
        for j in range(0,lenb+1):
            # if i*lenb+j==3:
            #     print("!",i,j)
            if i==0:
                memo[i*(lenb+1)+j]=j
            elif j==0:
                memo[i*(lenb+1)+j] = i
            else:
                memo[i*(lenb+1)+j]=min(memo[(i-1)*(lenb+1)+j]+1,
                                       memo[i*(lenb+1)+(j-1)]+1,
                                       memo[(i-1)*(lenb+1)+(j-1)]+(2 if a[i-1]!=b[j-1] else 0))

    # for i in range(lena+1):
    #     print("\n")
    #     for j in range(lenb+1):
    #         print(" %d(%d:%d,%d)"%(memo[i * (lenb+1) + j],i * (lenb+1) + j,i,j),end=" ")
    # print("\n")
    return memo[(lena+1)*(lenb+1)-1]

def lcs(str1,str2,minimum_len=0):
    """
    Longest common substring algorithm implementation using dynamic programming
    :param str1:
    :param str2:
    :param minimum_len:
    :return:
    """
    m = len(str1)
    n = len(str2)
    counter=array.array("l",[0 for i in range((n+1)*(m+1))])
    longest = 0
    current_lcs=""
    for i in range(m):
        for j in range(n):
            if str1[i] == str2[j]:
                c = counter[i*j] + 1
                counter[(i+1)*(j+1)] = c
                if c > longest and c>=minimum_len:
                    result=str1[i-c+1:i+1]
                    longest=c
                    current_lcs=result
                    # if result.upper() not in ENG_STR_NOT_A_GAME:
                    #     longest = c
                    #     lcs=result
                elif c == longest:
                    pass
                    # lcs_set.add(S[i-c+1:i+1])
    return current_lcs
    # if lcs:
    #     if longest-lcs.count(u"_")>=minimum_len:
    #         return lcs
    #     else:
    #         return
    # else:
    #     return

def related_med_score(s1,s2):
    lens1,lens2=len(s1),len(s2)
    lcstring=lcs(s1,s2)
    # if lcstring in EXEMPT:
    len_lcs=len(lcstring)

    if lcs:
        lcs_start_s1 = s1.find(lcstring)
        lcs_start_s2 = s2.find(lcstring)
        if lcs_start_s1 > 0 and lcs_start_s1 + len_lcs == lens1 and \
           lcs_start_s2 > 0 and lcs_start_s2 + len_lcs == lens2:
                s1,s2=s1.replace(lcstring,""),s2.replace(lcstring,"")

    # print(s1,s2)
    return med(s1,s2)/max(1,min(len(s1),len(s2)))

def get_wiki(value):
    try:
        JSON=json.loads(urlopen("https://zh.wikipedia.org/w/api.php?%s"%urlencode({"action":"query",
                                                                "prop":"revisions",
                                                                "rvprop":"content",
                                                                "format":"json",
                                                                "titles":value,                                                                                                  "converttitles":"",
                                                                "redirects":""})).read())
    except:
        return ""
    else:
        # print(JSON)
        if "query" in JSON and "redirects" in JSON['query']:
            return JSON['query']["redirects"][0]['to']
        else:
            return ""

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

def get_local_settings(conf="local_settings"):
    with open(conf,"r",encoding="utf8") as cfile:
        lines=cfile.readlines()

    conf_dict={}

    for line in lines:
        idx=0
        try:
            while not line[idx]:idx+=1
        except:
            continue # empty line
        if line[idx]=="#":
            continue # first not-null character is #

        try:
            key,value,_=re.split("\s+",line)
        except:
            try:
                key, value= re.split("\s+", line)
            except:
                continue #bad line
        try:
            conf_dict[key]=int(value)
        except:
            conf_dict[key]=value
    return conf_dict


def make_feature(relation,commas,tokens,stops=None):
    max_idx = max((int(relation[k]['idx']) for k in relation if ((k not in ("pattern", "id")) and ('idx' in relation[k] and int(relation[k]['idx'])>0))))
    min_idx = min((int(relation[k]['idx']) for k in relation if ((k not in ("pattern", "id")) and ('idx' in relation[k] and int(relation[k]['idx'])>0))))

    has_comma = False
    for comma in commas:
        if int(comma) > int(min_idx) and int(comma) < int(max_idx):
            has_comma = True
            break

    if stops is None:
        stops=[]

    has_stop=False
    for stop in stops:
        if int(stop) > int(min_idx) and int(stop) < int(max_idx):
            has_stop = True
            break

    return (pos2i(tokens[relation['a']['idx']]['lac_pos']),
                         pos2i(tokens[relation['r']['idx']]['lac_pos'] if 'idx' in relation['r'] else "None"),
                         pos2i(tokens[relation['b']['idx']]['lac_pos']),
                         abs(int(relation['r']['idx']) - int(relation['a']['idx'])) if 'idx' in relation['r'] and int(relation['r']['idx']) > 0 else 0,
                         1 if 'idx' in relation['r'] and int(relation['r']['idx']) - int(relation['a']['idx'])>0 else -1,
                         abs(int(relation['b']['idx']) - int(relation['r']['idx'])) if 'idx' in relation['r'] and int(relation['r']['idx']) > 0 else 0,
                         1 if 'idx' in relation['r'] and int(relation['b']['idx']) - int(relation['r']['idx']) > 0 else -1,
                         abs(int(relation['b']['idx']) - int(relation['a']['idx'])),
                         1 if int(relation['b']['idx']) - int(relation['a']['idx']) > 0 else -1,
                         comma_marker["comma" if has_comma else "no_comma"],
                        1 if has_stop else -1),11

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

def word2vec_sentence_generator(fns,encoding='utf8'):
    for fn in fns:
        jf = open(fn, encoding=encoding)
        while True:
            line = jf.readline()
            if line:
                if line[-1] == "\n":
                    line = line[:-1]


                yield [i['word'] for i in json.loads(line)['cut']]
            else:
                break

def pos2i(pos):
    try:
        return lac2int[pos]
    except KeyError:
        # print("unknown pos tag %s"%pos)
        return lac2int["OTHER"]

def call_stanford(tagged,host="http://localhost:9001/stanford"):
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

def lac_to_penn_pos(t):
    return lac2penn[t]

def make_word_repr(x,tokenDict):
    return ("%s(%s%s%s->%s)" % (
                x['prefix']+">>"+x['word'], x['index'], x['pos'], x['lac_pos'],
                tokenDict[x['head']]['word'] if x['head'] in tokenDict else "PUNC"))

def lac_cut(article,addr="localhost",port=18080):
    result = urlopen("http://%s:%d/lac"%(addr,port),
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    print(result)

    words = result.split("\t")

    a=[]
    for word in words:
        word = word.split(" ")
        if len(word)!=4:continue
        # if "一宗" in word[0]:
        #     print("fuck",repr(word[0]))
        #     print("。" in word[0])
        if len(word[0])>1 and "。" in word[0]:
            before,after=word[0].split("。")
            # print("before after",before,after)
            if before:
                a.append({"word": before, "type": word[1], "start": word[2], "length": len(before)})
            a.append({"word": "。", "type": "w", "start": str(int(word[2])+len(before)), "length": "1"})
            if after:
                a.append({"word": after, "type": "BAD", "start": str(int(word[2])+len(before)+1), "length": len(after)})
        else:
            a.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})

    return a

def tokenized_repr(wordlist):
    return (" ".join(map(lambda w:w['word'],wordlist)))


def lac_cut_break(article):
    result = urlopen("http://localhost:18080/lac",
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
    result = urlopen("http://localhost:18080/lac",
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

if __name__=="__main__":
    print(med("盘县","六盘水市"))