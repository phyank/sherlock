"""
强化学习模式的关系标注器，以ARB三元组关系标注为主要关系模型。
有以下几个功能：
1. 对输入文章进行分词、依存句法剖析、格式转换等基本预处理步骤
2. 根据历史标注数据重新抽取、统计依存关系模式并分别训练决策树分类器
3. 自动抽取部分关系，供用户确认。用户确认后即作为已标注关系保存
4. 记录用户手动输入的关系
5. 更新历史标注数据
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

conf_dict=get_local_settings()

s={
    "窃得":"盗窃",
"窃":"盗窃",
"窃取":"盗窃",
    "近亲属":"亲属"
}

def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def manual_tagger(draw_tree=False,add_kg=True):
    if add_kg:
        graph = Graph(uri=conf_dict['neo4j_address'], auth=(conf_dict['neo4j_user'], conf_dict['neo4j_pass']))

    g = line_generator("final_all_data/first_stage/train.json")
    try:
        of=open("tagged.json","r" ,encoding='utf8')
    except:
        with open("tagged.json","w"):
            pass
        of = open("tagged.json", "r",encoding='utf8')

    train_pattern_classifier()

    index=len(of.readlines())+1
    skip=index
    of.close()

    last=""
    final_sentences=[]
    for i in range(1000):
        with open("dependencyRelationPattern.json", 'r') as infile:
            patterns0 = json.load(infile)

            patterns = []
            for i in patterns0:
                if i['frequency'] >= PATTERN_MIN_FREQ:
                    patterns.append(i['pattern'])

        with open("classifiers.json", 'r') as infile:
            clfsb64 = json.load(infile)

        clfs={}

        for pattern in clfsb64:
            clfs[pattern]=pickle.loads(base64.b64decode(clfsb64[pattern].encode('ascii')))

        of = open("tagged.json", "a",encoding='utf8')
        articleJSON = json.loads(g.__next__())
        assert articleJSON!=last
        last=articleJSON

        if skip > 0:
            skip -= 1
            continue

        print("NEXT")
        # print(articleJSON)
        wordlist = lac_cut(articleJSON["fact"].replace("\r\n","").replace("\n",""),
                           addr=conf_dict['lac_addr'],
                           port=conf_dict['lac_port'])
        # print("wordlist")
        # print(wordlist)

        lac_result={}
        i=1
        #
        # PUs={}
        for word in wordlist:
            # if "index" in word and word['type']=="w":
            #     PUs[word['index']]=word

            lac_result[i]=word
            i+=1
        if USE=="CORENLP":
            # commas_and_stops=[]
            sentences=call_api(tokenized_repr(wordlist))
        else:# USE=="STANFORD":
            sentences=[]
            sentence=[]
            sentenceIndex=0
            PUs={}
            widx=0
            for w in wordlist:
                widx+=1
                sentence.append(w)
                if w['type']=="w":
                    PUs[widx]=w
                if w['word'] in "。？！":
                    tokenDict=call_stanford(sentence,host="http://%s:%d/stanford"%(conf_dict['corenlp_host'],conf_dict['corenlp_port']))
                    for pidx in PUs:
                        tokenDict[str(pidx)]=new_token(index=str(pidx),word=PUs[pidx]['word'],pos="PU",lac_pos="w",dep="-",head="0",begin=PUs[pidx]['start'],end=PUs[pidx]['start']+PUs[pidx]['length'])

                    ranked_tokens = {}
                    for i in sorted([int(k) for k in tokenDict]):
                        ranked_tokens[str(i)] = tokenDict[str(i)]

                    sentences.append(new_sentence_repr(index=sentenceIndex,
                                                       tokenDict=ranked_tokens))
                    sentence=[]
                    PUs={}
                    widx=0
        # print("sentences")
        # print(sentences)

        articleJSON['sentences']=sentences

        for sidx,sentence in enumerate(sentences):
            ranked_tokens=sentence['tokens']

            sentence['tokens']=ranked_tokens

            for k in special_r:
                ranked_tokens[str(k)] = new_token(index=str(k), word=special_r[k], pos=None, lac_pos=None, dep=None,
                                              head=None, begin=None, end=None)

            commas=set()
            stops=set()
            last_index='0'
            for wordidx in ranked_tokens:
                if int(wordidx) > 0:
                    word=ranked_tokens[wordidx]
                    if word['pos']=="PU":
                        if word['word'] in COMMAS:
                            commas.add(wordidx)
                        elif word['word'] in STOPS:
                            stops.add(wordidx)
                        else:
                            print("Ignored %s"%word['word'])
                    # print(ranked_tokens.keys())
                    ##build prefix
                    try:
                        if int(word['head'])>0 and ranked_tokens[word['head']]['pos'] in ("NN","NR") and word['pos'] not in ("PU"):
                            ranked_tokens[word['head']]['prefix']= \
                            word['word']+"|"+ranked_tokens[word['head']]['prefix']
                    except KeyError:
                        print("head not found:word %s head %s"%(word['word'],word['head']))
                        continue
                        # sentence['enhancedPlusPlusDependencies'].remove(word)

                # if int(wordidx)-int(last_index)>1:
                #     commas.update(map(lambda x:str(x),range(int(last_index)+1,int(wordidx)))) #for conll2007 output no commas in dict
                #
                # if ranked_tokens[wordidx]['word'] in ",，；;、":
                #     commas.add(ranked_tokens[wordidx]['index'])# for corenlp server

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
                    this_feature,n_features=make_feature(r,commas=commas,stops=stops,tokens=ranked_tokens)
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

            # print(ranked_tokens.keys())

            relations=[]

            for possible in auto_relations:
                try:
                    r = int(possible['r']['idx'])
                except:
                    try:
                        r = special[possible['r']['w']]
                    except:
                        print("Aborted")
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
                    confirm = input(
                        "pattern %s > %s,%s,%s?(Yes):" % (possible['pattern'],
                                                          ranked_tokens[a]['word'],
                                                          ranked_tokens[r]['word'],
                                                          ranked_tokens[b]['word']))
                except Exception as e:
                    print(e.__class__.__name__)
                    print(traceback.format_exc())
                    print("Invalid input. Aborted")
                    continue
                else:
                    if not confirm or confirm in "YESYesyes":
                        relations.append((a, r, b))
                    else:
                        print("Aborted")
                        continue

            while True:
                # print(" ".join(map(lambda x: ("%s(%s%s%s->%s)" % (
                #                 x['word'],
                #                 x['index'],
                #                 x['pos'],
                #                 x['lac_pos'],
                #                 ranked_tokens[x['head']]['word'] if x['head'] in ranked_tokens else "PUNC")),
                # (ranked_tokens[idx] for idx in ranked_tokens if int(idx)>0))))
                for x in [ranked_tokens[idx] for idx in ranked_tokens if int(idx) > 0]:
                    wordFormatted.append(make_word_repr(x, ranked_tokens))
                print("".join(wordFormatted))

                relation=input("[no.%d]relation(a,r,b)>"%index)
                if not relation:
                    print("Aborted")
                    continue
                if relation in "OKOkoKok":break
                relation=relation.split(" ")
                if len(relation)!=3 or not relation[0] or not relation[1] or not relation[2]:
                    print("INVALID INPUT")
                    continue
                else:
                    try:
                        r=int(relation[1])
                    except:
                        try:
                            r=special[relation[1]]
                        except:
                            print("Aborted")
                            continue

                    r=str(r)
                    try:
                        a,b=relation[0],relation[2]
                        if a in default_character:
                            a=default_character[a]

                        if b in default_character:
                            b=default_character[b]

                        confirm=input("%s,%s,%s?(Yes):" % (ranked_tokens[a]['word'],
                                                           ranked_tokens[r]['word'],
                                                           ranked_tokens[b]['word']))
                    except Exception as e:
                        print(e.__class__.__name__)
                        print(traceback.format_exc())
                        print("Invalid input. Aborted")
                        continue
                    else:
                        if not confirm or confirm in "YESYesyes":
                            relations.append((a,r,b))
                        else:
                            print("Aborted")
                            continue

            for a,r,b in relations:
                print("%s,%s,%s"%(ranked_tokens[a]['word'],
                                  ranked_tokens[r]['word'],
                                  ranked_tokens[b]['word']))
            sentence['manual_relations']=relations
            final_sentences.append(sentence)
        print(final_sentences)

        if add_kg:
            add_case(graph,final_sentences,index)
        articleJSON['sentences']=final_sentences
        of.write(json.dumps(articleJSON,ensure_ascii=False))
        of.write("\n")
        of.close()
        extract_dep_patterns(to_write=True)
        train_pattern_classifier()
        index+=1
def tag_test():
    manual_tagger()

if __name__=="__main__":
    tag_test()