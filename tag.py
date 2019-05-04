import traceback
from copy import deepcopy
from tools import *
from threading import Thread

from nltk.tree import Tree

from definitions import *
from relation_walker import *
from kg import *

USE="STANFORD"

VERBOSE=False

def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def manual_tagger(draw_tree=False,add_kg=True):
    if add_kg:
        graph = Graph(uri="127.0.0.1:7474", auth=("neo4j", "Cion24"))

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
        wordlist = lac_cut(articleJSON["fact"].replace("\r\n","").replace("\n",""),addr="192.168.59.141")
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
                                                       tokenDict=call_stanford(sentence)))
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
            auto_relations0=find_relation_by_pattern(patterns,ranked_tokens,print_result=False)

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
                    max_idx = max((r[k]['idx'] for k in r if ((k not in ("pattern", "id")) and ('idx' in r[k]))))
                    min_idx = min((r[k]['idx'] for k in r if ((k not in ("pattern", "id")) and ('idx' in r[k]))))

                    has_comma = False
                    for comma in commas:
                        if int(comma) > int(min_idx) and int(comma) < int(max_idx):
                            has_comma = True
                            break

                    result=clf.predict(np.ndarray(shape=(1,7),dtype='int',buffer=np.array((pos2i(ranked_tokens[r['a']['idx']]['lac_pos']),
                         pos2i(ranked_tokens[r['r']['idx']]['lac_pos'] if 'idx' in r['r'] else "None"),
                         pos2i(ranked_tokens[r['b']['idx']]['lac_pos']),
                         abs(int(r['r']['idx']) - int(r['a']['idx'])) if 'idx' in r['r'] and int(r['r']['idx']) > 0 else 0,
                         abs(int(r['b']['idx']) - int(r['r']['idx'])) if 'idx' in r['r'] and int(r['r']['idx']) > 0 else 0,
                         abs(int(r['b']['idx']) - int(r['a']['idx'])),
                         comma_marker["comma" if has_comma else "no_comma"]))))[0]
                    if result==1:
                        auto_relations.append(r)
                    else:
                        print("flitered %s %s %s"%(r['a']['w'],r['r']['w'],r['b']['w']))
                        print((pos2i(ranked_tokens[r['a']['idx']]['lac_pos']),
                         pos2i(ranked_tokens[r['r']['idx']]['lac_pos'] if 'idx' in r['r'] else "None"),
                         pos2i(ranked_tokens[r['b']['idx']]['lac_pos']),
                         abs(int(r['r']['idx']) - int(r['a']['idx'])) if 'idx' in r['r'] and int(r['r']['idx']) > 0 else 0,
                         abs(int(r['b']['idx']) - int(r['r']['idx'])) if 'idx' in r['r'] and int(r['r']['idx']) > 0 else 0,
                         abs(int(r['b']['idx']) - int(r['a']['idx'])),
                         comma_marker["comma" if has_comma else "no_comma"]))

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
                print(" ".join(map(lambda x: ("%s(%s%s%s->%s)" % (
                                x['word'],
                                x['index'],
                                x['pos'],
                                x['lac_pos'],
                                ranked_tokens[x['head']]['word'] if x['head'] in ranked_tokens else "PUNC")),
                (ranked_tokens[idx] for idx in ranked_tokens if int(idx)>0))))

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