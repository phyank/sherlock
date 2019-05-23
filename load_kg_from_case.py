"""
这个文件中记录的方法可以从法律文书加载、导入图谱。可以从已标注的法律文书载入，也可以从新的法律文书载入
"""
import traceback
from copy import deepcopy
from tools_cpython import *
from threading import Thread

from nltk.tree import Tree

from definitions import *
from relation_walker import *
from kg import *

USE="STANFORD"

VERBOSE=False

LOC_BLACK_LIST=["县"]

conf_dict=get_local_settings()

s={
    "窃得":"盗窃",
"窃":"盗窃",
"窃取":"盗窃",
    "近亲属":"亲属"
}

def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def load_kg_from_new_article(draw_tree=False):
    graph = Graph(uri=conf_dict['neo4j_address'], auth=(conf_dict['neo4j_user'], conf_dict['neo4j_pass']))

    location_patterns={}

    for i in graph.run("match (n:Location) where n._subgraph='baike' return n.name,n.short"):
        if i['n.name'] and i['n.name'] not in LOC_BLACK_LIST:
            location_patterns[i['n.name']]=i['n.name']
        if i['n.short'] and i['n.short'] not in LOC_BLACK_LIST:
            location_patterns[i['n.short']]=i['n.name']

    for label in ("LegalCase", "Keyword", "Location", "Person", "Organization", "Time", "Item", "Entity","Action"):
        graph.run("CREATE INDEX ON :%s(name)" % label)

    with open("critical","r",encoding="utf8") as pfile:
        lines=pfile.readlines()

    regExractor=RegExtractor(patterns=lines)

    g = line_generator("final_all_data/first_stage/train.json")

    train_pattern_classifier()

    with open("dependencyRelationPattern.json", 'r') as infile:
        patterns0 = json.load(infile)

        patterns = []
        for i in patterns0:
            if i['frequency'] >= PATTERN_MIN_FREQ:
                patterns.append(i['pattern'])

    with open("classifiers.json", 'r') as infile:
        clfsb64 = json.load(infile)

    clfs = {}

    for pattern in clfsb64:
        clfs[pattern] = pickle.loads(base64.b64decode(clfsb64[pattern].encode('ascii')))

    index=1
    last=""
    jump=96
    for i in range(1000):
        final_sentences = []

        articleJSON = json.loads(g.__next__())
        if jump:
            index+=1
            jump-=1
            continue
        assert articleJSON!=last
        last=articleJSON

        print("NEXT",index)
        # print(articleJSON)
        wordlist = lac_cut(articleJSON["fact"].replace("\r\n","").replace("\n",""),
                           addr=conf_dict['lac_addr'],
                           port=conf_dict['lac_port'])
        # print("wordlist")
        # print(wordlist)

        lac_result={}
        i=1
        for word in wordlist:
            lac_result[i]=word
            i+=1
        if USE=="CORENLP":
            sentences=call_api(tokenized_repr(wordlist))
        else:# USE=="STANFORD":
            sentences=[]
            sentence=[]
            sentenceIndex=0
            for w in wordlist:
                sentence.append(w)
                if w['word'] in "。？！":
                    sentences.append(new_sentence_repr(index=sentenceIndex,
                                                       tokenDict=call_stanford(sentence,host="http://%s:%d/stanford"%(conf_dict['corenlp_host'],conf_dict['corenlp_port']))))
                    sentence=[]
        # print("sentences")
        # print(sentences)

        articleJSON['sentences']=sentences

        for sentence in sentences:
            ranked_tokens=sentence['tokens']

            for k in special_r:
                ranked_tokens[str(k)] = new_token(index=str(k), word=special_r[k], pos=None, lac_pos=None, dep=None,
                                              head=None, begin=None, end=None)

            commas=set()
            last_index='0'
            for wordidx in ranked_tokens:
                if int(wordidx) > 0:##build prefix
                    word=ranked_tokens[wordidx]
                    # print(ranked_tokens.keys())
                    try:
                        if int(word['head'])>0 and ranked_tokens[word['head']]['pos'] in ("NN","NR") and word['pos'] not in ("PU"):
                            ranked_tokens[word['head']]['prefix']= \
                            word['word']+"|"+ranked_tokens[word['head']]['prefix']
                    except KeyError:
                        print("head not found:word %s head %s"%(word['word'],word['head']))
                        continue
                        # sentence['enhancedPlusPlusDependencies'].remove(word)

                if int(wordidx)-int(last_index)>1:
                    commas.update(map(lambda x:str(x),range(int(last_index)+1,int(wordidx)))) #for conll2007 output no commas in dict

                if ranked_tokens[wordidx]['word'] in ",，；;、":
                    commas.add(ranked_tokens[wordidx]['index'])# for corenlp server

                last_index=wordidx


            # if draw_tree:
            #     async_run_draw(sentence['parse'])
            # print(patterns)
            auto_relations0=find_relation_by_pattern(patterns,ranked_tokens,print_result=False,draw=False)

            # print("auto0",auto_relations0)

            auto_relations=[]
            for r in auto_relations0:
                thisPattern=r['pattern']
                if 'idx' not in r['r']:
                    thisPattern+="?"+r['r']['w']
                try:
                    clf=clfs[thisPattern]
                except KeyError:
                    print("Pattern classifier not found : %s"%thisPattern)
                    auto_relations.append(r)
                else:
                    this_feature,n_features=make_feature(r,commas=commas,tokens=ranked_tokens)
                    result=clf.predict(np.ndarray(shape=(1,n_features),dtype='int',buffer=np.array(this_feature)))[0]
                    if result==1:
                        auto_relations.append(r)
                    else:
                        print("flitered %s %s %s"%(r['a']['w'],r['r']['w'],r['b']['w']))
                        print(this_feature)

            wordFormatted=[]
            for x in [ranked_tokens[idx] for idx in ranked_tokens if int(idx)>0]:
                wordFormatted.append(make_word_repr(x,ranked_tokens))
            print("".join(wordFormatted))



            relations=[]

            for possible in auto_relations:
                try:
                    r = int(possible['r']['idx'])
                except:
                    try:
                        r = special[possible['r']['w']]
                    except:
                        print("Unknown relation %s, Aborted"%repr(possible['r']))
                        continue
                r=str(r)
                try:
                    a, b = possible['a']['idx'], possible['b']['idx']
                    if a in default_character:
                        a = str(default_character[a])
                    else:
                        a = (possible['a']['idx'])
                    if b in default_character:
                        b = str(default_character[b])
                    else:
                        b = (possible['b']['idx'])
                except Exception as e:
                    continue
                else:
                    relations.append((a, r, b))




            for a,r,b in relations:
                print("%s,%s,%s"%(ranked_tokens[a]['word'],
                                  ranked_tokens[r]['word'],
                                  ranked_tokens[b]['word']))
            sentence['manual_relations']=relations
            final_sentences.append(sentence)
        # print(final_sentences)

        add_case(graph,final_sentences,article=articleJSON["fact"],case_index=index,reg_extractor=regExractor,location_patterns=location_patterns)

        index+=1

def  load_kg_from_tagged():
    g = line_generator("tagged.json")

    conf_dict = get_local_settings()

    graph = Graph(uri=conf_dict['neo4j_address'], auth=(conf_dict['neo4j_user'], conf_dict['neo4j_pass']))

    location_patterns={}

    for i in graph.run("match (n:Location) where n._subgraph='baike' return n.name,n.short"):
        location_patterns[i['n.name']]=i['n.name']
        location_patterns[i['n.short']]=i['n.name']


    for label in ("LegalCase", "Keyword", "Location", "Person", "Organization", "Time", "Item", "Entity", "Action"):
        graph.run("CREATE INDEX ON :%s(name)" % label)

    with open("critical", "r", encoding="utf8") as pfile:
        lines = pfile.readlines()

    regExractor = RegExtractor(patterns=lines)

    index = 0
    while True:
        try:
            articleJSON = json.loads(g.__next__())
        except StopIteration:
            break
        else:

            add_case(graph, articleJSON['sentences'], articleJSON['fact'], index, regExractor,location_patterns)
            index += 1

def build_test():
    load_kg_from_new_article()
    # load_kg_from_tagged()

if __name__=="__main__":
    build_test()