import traceback
from copy import deepcopy
from tools import *
from threading import Thread

from nltk.tree import Tree

from definitions import *
from relation_walker import *

PATTERN_MIN_FREQ=10

def run_draw(sentence_repr):
    Tree.fromstring(sentence_repr).draw()

def manual_tagger(draw_tree=False):
    g = line_generator("final_all_data/first_stage/train.json")
    try:
        of=open("tagged.json","r")
    except:
        with open("tagged.json","w"):
            pass
        of = open("tagged.json", "r")



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

        of = open("tagged.json", "a")
        articleJSON = json.loads(g.__next__())
        assert articleJSON!=last
        last=articleJSON

        if skip > 0:
            skip -= 1
            continue

        print("NEXT")
        # print(articleJSON)
        wordlist = lac_cut(articleJSON["fact"].replace("\r\n","").replace("\n",""))
        # print("wordlist")
        # print(wordlist)

        lac_result={}
        i=1
        for word in wordlist:
            lac_result[i]=word
            i+=1
        sentences=call_api(tokenized_repr(wordlist))['sentences']
        # print("sentences")
        # print(sentences)

        articleJSON['sentences']=sentences

        lac_result_gen=(i for i in wordlist)
        for sentence in sentences:
            # print(sentence)
            tokenDict={0:{"word":"ROOT"}}
            for k in special:
                tokenDict[special[k]]={"word":k}
            for k in default_character:
                tokenDict[default_character[k]]={"word":k}

            for word in sentence['tokens']:
                lac=lac_result_gen.__next__()
                assert lac['word']==word['word']
                word['lac_pos']=lac['type']
                tokenDict[word['index']]=word

            rankingDict = {}
            for word in sentence['enhancedPlusPlusDependencies']:
                tokenDict[word['dependent']]['ref']=word
                rankingDict[word['dependent']] = word
                idxs=sorted(rankingDict)

            ranked_tokens = make_ranked_token_dict(sentence['tokens'], reverse=False)

            for wordidx in ranked_tokens:
                word=ranked_tokens[wordidx]['ref']
                if word['governor']!=0 and tokenDict[word['governor']]['pos'] in ("NN","NR") and tokenDict[word['dependent']]['pos'] not in ("PU"):
                    tokenDict[word['governor']]['ref']['dependentGloss']= \
                    word['dependentGloss']+"|"+tokenDict[word['governor']]['ref']['dependentGloss']
                    # sentence['enhancedPlusPlusDependencies'].remove(word)
            print(" ".join(map(lambda x:("%s(%d%s%s->%s)"%(x['dependentGloss'],x['dependent'],tokenDict[x['dependent']]['pos'],tokenDict[x['dependent']]['lac_pos'],tokenDict[x['governor']]['word'])) ,[rankingDict[idx] for idx in idxs])))

            if draw_tree:
                async_run_draw(sentence['parse'])

            auto_relations=find_relation_by_pattern(patterns,ranked_tokens,print_result=False)



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
                try:
                    a, b = possible['a']['idx'], possible['b']['idx']
                    if a in default_character:
                        a = default_character[a]
                    else:
                        a = int(possible['a']['idx'])
                    if b in default_character:
                        b = default_character[b]
                    else:
                        b = int(possible['b']['idx'])
                    confirm = input(
                        "pattern %s > %s,%s,%s?(Yes):" % (possible['pattern'],tokenDict[a]['word'], tokenDict[r]['word'], tokenDict[b]['word']))
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
                print(" ".join(map(lambda x: ("%s(%d%s%s->%s)" % (
                x['dependentGloss'], x['dependent'], tokenDict[x['dependent']]['pos'],
                tokenDict[x['dependent']]['lac_pos'], tokenDict[x['governor']]['word'])),
                                   [rankingDict[idx] for idx in idxs])))

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
                    try:
                        a,b=relation[0],relation[2]
                        if a in default_character:
                            a=default_character[a]
                        else:
                            a=int(relation[0])
                        if b in default_character:
                            b=default_character[b]
                        else:
                            b=int(relation[2])
                        confirm=input("%s,%s,%s?(Yes):" % (tokenDict[a]['word'], tokenDict[r]['word'], tokenDict[b]['word']))
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
            for word in sentence['enhancedPlusPlusDependencies']:
                newTokenDict=deepcopy(tokenDict[word['dependent']])
                del newTokenDict['ref']
                word.update(newTokenDict)

            for a,r,b in relations:
                print("%s,%s,%s"%(tokenDict[a]['word'],tokenDict[r]['word'],tokenDict[b]['word']))
            sentence['manual_relations']=relations
            final_sentences.append(sentence)
        print(final_sentences)
        articleJSON['processed_sentences']=final_sentences
        of.write(json.dumps(articleJSON,ensure_ascii=False))
        of.write("\n")
        of.close()
        extract_dep_patterns(to_write=True)
        index+=1
def tag_test():
    manual_tagger()

if __name__=="__main__":
    tag_test()