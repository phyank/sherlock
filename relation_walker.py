import traceback,json,pickle,base64
from copy import deepcopy
from tools import *
from definitions import *

from nltk.tree import Tree
import numpy as np
from sklearn.naive_bayes import MultinomialNB,ComplementNB,GaussianNB
from sklearn.tree import DecisionTreeClassifier

PATTERN_EXTRACTION_MIN_FREQ=5

class Impossible(Exception):
    pass

class Node:
    def __init__(self,index,name,fullname):
        self.index=index
        self.father=None
        self.childs=set()
        self.name=name
        self.fullname=fullname
        self.addition=""
        self.out_relations=set()
        self.in_relation=None

class Edge:
    def __init__(self,src,name,dst):
        self.src=src
        self.src.out_relations.add(self)
        self.src.childs.add(dst)
        self.name=name
        self.dst=dst
        self.dst.father=self.src
        self.dst.in_relation=self

def tree_to_string(node,dep_name="ROOT"):
    childs_literal=""
    # for child in node.childs:
    #     childs_literal+=tree_to_string(child)
    for edge in node.out_relations:
        childs_literal += tree_to_string(edge.dst,edge.name)
    return "(%s %s)"%(dep_name+":"+node.name+node.addition,childs_literal)



def link_str(s,a,direction=RIGHT):
    if direction is RIGHT:
        return s+a
    elif direction is LEFT:
        return a+s
    else:
        raise Impossible

def find_path_in_tree2(root,a_addition,b_addition,direction=RIGHT):
    """

    :param root:
    :param a_addition:
    :param b_addition:
    :param direction:
    :return: half_result, full_result, hit
    """
    path=""
    half_path=""
    hit=0
    all_hit=0
    clue=(a_addition,b_addition)

    halfs=set()

    current=root

    if current.addition in clue:
        hit+=1
        all_hit+=1
        path=("(%s)"%current.addition)
        half_path=("(%s)"%current.addition)
    else:
        half_path="()"

    loop=1
    subdirection=direction
    for relation in current.out_relations:
        child_half,child_full,child_hit=find_path_in_tree2(relation.dst,a_addition,b_addition,direction=subdirection)
        all_hit+=child_hit
        if child_hit==2:
            return "",child_full,2
        elif child_hit<2:
            if subdirection is RIGHT:
                child_half=(("<-[:%s]-" % relation.name) + child_half)
            elif subdirection is LEFT:
                child_half=(child_half + (("-[:%s]->" % relation.name)))

            if child_hit<1:continue
            elif child_hit==1:
                if hit==1:
                    return "",link_str(path,child_half,direction=direction),2
                elif hit<=0:
                    halfs.add((child_half,subdirection))
                    pass
                else:
                    raise Impossible
            else:
                raise Impossible
        else:
            raise Impossible

        if loop==2:
            break
        else:
            subdirection*=-1
            loop+=1


    if all_hit==2:
        if hit==0:
            suba,subb=first_N(halfs,n=2)
            suba,ad=suba
            subb,bd=subb
            path=link_str("()",suba,ad)
            path=link_str(path,subb,bd)
            return half_path,path,2
        if hit==1:
            raise Impossible
    elif all_hit==1:
        if hit==1:
            return half_path,path,1
        elif hit==0:
            chalf,cd=first(halfs)
            half_path=link_str(half_path,chalf,cd)
            return half_path,path,1
        else:
            raise Impossible
    else:
        return "","",0

def get_words_relations(a,r,b,tokenDict,final):
    if int(a)>=0 and int(b)>=0:
        nodes={}

        nodes[0]=Node(0,"ROOT","ROOT")

        all_edges={}

        a,r,b=str(a),str(r),str(b)

        for i,iname in ((a,"a"),(b,"b"),(r,"r")):

            if int(i)<0:
                assert iname=="r"
                continue
            try:
                token=tokenDict[str(i)]# json make int to str
            except KeyError:
                print("WARNING: Missing key %s in %s"%(i," ".join(map(lambda x:tokenDict[x]['word'],(k for k in [ k for k in tokenDict.keys()][:min(len(tokenDict.keys()),10)])))))
                print("1(target %s,%s,%s)"%(a,r,b))
                return
            if i not in nodes:
                nodes[i]=Node(i,token['word'],token['prefix']+token['word'])
            current_token_node=nodes[i]
            current_token=token
            current_token_node.addition=iname

            while int(current_token['head'])>0:
                if current_token['head'] not in nodes:
                    try:
                        father_token=tokenDict[current_token['head']]
                    except KeyError as e:
                        print("WARNING: Missing key %s in %s" % (current_token['head'], " ".join(map(lambda x: tokenDict[x]['word'],
                                                                                 (k for k in
                                                                                  [k for k in tokenDict.keys()][
                                                                                  :min(len(tokenDict.keys()), 10)])))))
                        print("(target %s,%s,%s)" % (a, r, b))
                        return

                    father_token_node=Node(father_token['index'],father_token['word'],father_token['prefix']+father_token['word'])
                    nodes[father_token['index']]=father_token_node
                else:
                    try:
                        father_token=tokenDict[current_token['head']]
                    except KeyError:
                        print("WARNING: Missing key %s in %s" % (current_token['head'], " ".join(map(lambda x: tokenDict[x]['word'],
                                                                                 (k for k in
                                                                                  [k for k in tokenDict.keys()][
                                                                                  :min(len(tokenDict.keys()), 10)])))))
                        print("(3target %s,%s,%s)" % (a, r, b))
                        return
                    father_token_node=nodes[father_token['index']]

                if father_token_node.name+current_token['dep']+current_token_node.name not in all_edges:
                    all_edges[father_token_node.name+current_token['dep']+current_token_node.name]=\
                        Edge(father_token_node, current_token['dep'], current_token_node)
                current_token, current_token_node = father_token, father_token_node

            if current_token['head']=='0':
                father_token_node = nodes[0]
                if father_token_node.name + current_token['dep'] + current_token_node.name not in all_edges:
                    all_edges[father_token_node.name + current_token['dep'] + current_token_node.name] = \
                        Edge(father_token_node, current_token['dep'], current_token_node)


        root = nodes[0]
        if int(r)<0: # R(A,B)
            _,path_left,hit=find_path_in_tree2(root,"a","b",direction=LEFT)
            _, path_right, hit = find_path_in_tree2(root, "a", "b", direction=RIGHT)
            for path in (path_left,path_right):
                patternDescriptor="%s ?%s"%(path,special_r[int(r)])
                found=False
                try:
                    final[patternDescriptor]+=1
                except:
                    continue
                else:
                    found=True
                    break
            if not found:final[patternDescriptor]=1 #new pattern

        else:# R (A,R,B)
            _,path1_left,hit1=find_path_in_tree2(root,"a","r",direction=LEFT)
            _, path1_right, hit1 = find_path_in_tree2(root, "a", "r",direction=RIGHT)
            assert (path1_left and path1_right) or not (path1_left or path1_right)
            if not path1_left:return

            _,path2_left,hit2=find_path_in_tree2(root,"r","b",direction=LEFT)
            _, path2_right, hit2 = find_path_in_tree2(root, "r", "b", direction=RIGHT)
            assert (path1_left and path1_right) or not (path1_left or path1_right)
            if not path2_left: return
            path1=[path1_left,path1_right]
            path2=[path2_left,path2_right]

            patternDescriptor="NO PATTERN"
            found=False
            for p1 in path1:
                for p2 in path2:

                    patternDescriptor=("%s,%s"%(p1,p2))

                    try:
                        final[patternDescriptor]+=1
                    except:
                        continue
                    else:
                        found=True
                        break
                if found:break

            assert patternDescriptor!= "NO PATTERN"
            if not found:
                final[patternDescriptor]=1 #new pattern

    elif a<0:
        pass
    elif b<0:
        pass
    else:
        raise Impossible

def make_ranked_token_dict(tokens,reverse=True):
    if isinstance(tokens,dict):
        makeFrom="dict"
    else:
        makeFrom="list"
    tokenDict = {0: {"word": "ROOT"}}
    for k in special:
        tokenDict[special[k]] = {"word": k}
    for k in default_character:
        tokenDict[default_character[k]] = {"word": k}

    for word in tokens:
        if makeFrom=="dict":word=tokens[word]
        try:
            tokenDict[word['index']] = word
        except:
            print(word)
            raise Exception
        word['ref']['fullname'] = \
            word['word']

    ranked_tokens = {}
    for idx in sorted([i['index'] for i in tokens], reverse=reverse):
        ranked_tokens[idx] = tokenDict[idx]

    print(" ".join((ranked_tokens[i]['word'] for i in ranked_tokens)))
    for word_index in ranked_tokens:
        word = ranked_tokens[word_index]
        if word['head'] != 0 and tokenDict[word['head']]['pos'] in ("NN", "NR") and \
                tokenDict[word['ref']['dependent']]['pos'] not in ("PU"):
            # print(word)
            # print("%s PING %s"%(tokenDict[word['head']]['ref']['fullname'],word['word']))
            tokenDict[word['head']]['ref']['fullname'] = \
                word['word'] + "|" + tokenDict[word['head']]['ref']['fullname']
    return ranked_tokens

def no_distance(x):
    return x[0],x[1],x[2],x[6]

def train_pattern_classifier():
    with open("dependencyRelationPattern.json", 'r') as infile:
        patterns0 = json.load(infile)

        patterns = []
        for i in patterns0:
            if i['frequency'] > 2:
                patterns.append(i['pattern'])
                # print("Append pattern %s"%i['pattern'])
    training_set_by_pattern={}
    for article in line_generator("tagged.json", encoding='utf8'):
        try:
            articleDict = json.loads(article)
        except:
            print(repr(article))
            raise Exception

        lastSentenceSubject = None
        lastSentenceMainVerb = None
        lastSentenceTime = None
        for sentence in articleDict['sentences']:
            ranked_tokens = sentence['tokens']


            this_training_set_by_pattern=generate_training_set(patterns, ranked_tokens, sentence['manual_relations'])
            for pattern in this_training_set_by_pattern:
                try:
                    training_set_by_pattern[pattern]['data']+=this_training_set_by_pattern[pattern][0]
                    training_set_by_pattern[pattern]['label'] += this_training_set_by_pattern[pattern][1]
                except KeyError:
                    training_set_by_pattern[pattern]={'data':this_training_set_by_pattern[pattern][0],
                                                      'label':this_training_set_by_pattern[pattern][1]}
    classifiers={}

    # print("training set",training_set_by_pattern)
    for aPattern in training_set_by_pattern:
        data0,label=training_set_by_pattern[aPattern]['data'],training_set_by_pattern[aPattern]['label']
        if not data0 or len(data0)<PATTERN_MIN_FREQ:continue
        data=[]
        for i in data0:data+=i
        # print(aPattern)

        dataArray=np.ndarray(shape=(len(data0),len(data0[0])),dtype='int',buffer=np.array(data))
        labelArray=np.array(label)
        # print(len(dataArray), len(labelArray))
        # clf = ComplementNB()
        # clf=GaussianNB()
        clf=DecisionTreeClassifier()
        clf.fit(dataArray, labelArray)
        # print([(clf.predict(dataArray)[i],labelArray[i]) for i in range(len(labelArray))])
        count=len(dataArray)
        hit=0
        p=clf.predict(dataArray)
        for i in range(len(dataArray)):
            if p[i]==labelArray[i]:hit+=1
        print("pattern %s correct %.2f all %d"%(aPattern,hit/count,count))
        classifiers[aPattern]=base64.b64encode(pickle.dumps(clf)).decode('ascii')
    with open("classifiers.json",'w') as of:
        json.dump(classifiers,of)

def extract_dep_patterns(to_write=False):
    final = {}
    with open("dependencyRelationPattern.json", 'r') as infile:
        patterns0 = json.load(infile)

        patterns = []
        for i in patterns0:
            if i['frequency'] > PATTERN_MIN_FREQ:
                patterns.append(i['pattern'])
    for article in line_generator("tagged.json", encoding='utf8'):
        try:
            articleDict = json.loads(article)
        except:
            print(repr(article))
            raise Exception

        for sentence in articleDict['sentences']:
            ranked_tokens=sentence['tokens']

            # train_pattern_classifier(patterns[1], ranked_tokens, sentence['manual_relations'])
            # testtest = find_relation_by_pattern(patterns, ranked_tokens)
            for a,r,b in sentence['manual_relations']:
                (get_words_relations(a,r,b,ranked_tokens,final))

    for pattern,frequency in sorted(final.items(),key=lambda i:i[1],reverse=True):
        print(pattern,frequency)

    if to_write:
        rps=[]
        for pattern,frequency in sorted(final.items(),key=lambda i:i[1],reverse=True):
            rps.append({'pattern':pattern,'frequency':frequency})
        with open("dependencyRelationPattern.json",'w') as rfile:
            json.dump(rps,rfile)

def extract_relation_by_dep_patterns():

    with open("dependencyRelationPattern.json", 'r') as infile:
        patterns0 = json.load(infile)

        patterns = []
        for i in patterns0:
            if i['frequency'] > 2:
                patterns.append(i['pattern'])
    for article in line_generator("tagged.json", encoding='gbk'):
        articleDict = json.loads(article)

        for sentence in articleDict['processed_sentences']:
            ranked_tokens = make_ranked_token_dict(sentence['tokens'])

            testtest = find_relation_by_pattern(patterns, ranked_tokens)


def test():
    extract_relation_by_dep_patterns()

class Gen:
    def __init__(self,iterable):
        self.iterable=iterable
        self.pointer=0
    def __next__(self):
        if self.pointer<self.__len__():
            r=self.iterable[self.pointer]
            self.pointer+=1
            return r
        else:
            raise StopIteration

    def __deepcopy__(self, memodict={}):
        copy=Gen(deepcopy(self.iterable))
        copy.pointer=self.pointer
        return copy
    def __len__(self):
        return len(self.iterable)

def find_relation_by_pattern_token_and_tree_given(tokenIndex,pattern,nodes,tokenDict):

        r_pttrn = r"-\[[\w\d:]+\]->|<-\[[\w\d:]+\]-"

        pttrn_nodes_path = re.findall("\([\w\d_]*\)", pattern)
        pttrn_nodes_path = [i[:-1][1:] for i in pttrn_nodes_path]

        required_roles = set()
        for i in pttrn_nodes_path:
            if i: required_roles.add(i)

        pttrn_relation_path0 = re.findall(r_pttrn, pattern)
        pttrn_relation_path = [(re.search("[\w\d]+:?[\w\d]*", i).group(), LEFT if "<" in i else RIGHT) for i in
                               pttrn_relation_path0]
        # if reverse:
        #     pttrn_nodes_path.reverse()
        #     pttrn_relation_path.reverse()
        try:
            assert pttrn_nodes_path and pttrn_relation_path
        except:
            return []
        role = {}
        pttrn_node_gen = Gen(pttrn_nodes_path)
        relation_gen = Gen(pttrn_relation_path)

        currents = {
            0: {"current": nodes[tokenIndex], "role": role, "required_roles": required_roles, "pttrn_node": pttrn_node_gen,
                "rgen": relation_gen, "found": -1}}

        # print(pttrn_nodes_path)
        # print(pttrn_relation_path)
        relations=[]
        while currents:
            idx = min(currents)
            currentAll = currents[idx]
            current = currentAll['current']
            role = currentAll['role']
            pttrn_node_gen = currentAll["pttrn_node"]
            relation_gen = currentAll['rgen']
            required_roles = currentAll['required_roles']
            # print("role",role,"id",id(role))
            # print("req role",required_roles)
            found = currentAll['found']
            while True:
                try:
                    pttrn_node = pttrn_node_gen.__next__()
                except StopIteration:
                    if required_roles:
                        found = False
                    else:
                        found = True
                    break

                if pttrn_node:
                    assert pttrn_node not in role
                    if current.index not in role:# one word cannot have 2 roles
                        role[current.index] = {"w":current.name,"role": pttrn_node}
                        required_roles.remove(pttrn_node)

                try:
                    pttrn_dep, dep_direction = relation_gen.__next__()
                except StopIteration:
                    pttrn_dep, dep_direction = None, None

                if dep_direction is RIGHT:
                    if pttrn_dep is not None and current.in_relation is not None:
                        if pttrn_dep == current.in_relation.name:
                            current = current.father
                            continue
                        else:
                            found = False
                            # print("break0")
                            break
                    else:
                        if required_roles:
                            found = False
                        # print("break1")
                        break
                elif dep_direction is LEFT:
                    if pttrn_dep is not None and current.out_relations:
                        for r in current.out_relations:#TODO:prevent walk back
                            if pttrn_dep == r.name:
                                currents[max(currents) + 1] = \
                                    {"current": r.dst,
                                     "role": deepcopy(role),
                                     "required_roles": deepcopy(required_roles),
                                     "pttrn_node": deepcopy(pttrn_node_gen),
                                     "rgen": deepcopy(relation_gen),
                                     "found": True if found else False}

                                continue
                            else:
                                continue

                        if required_roles:
                            found = False
                        else:
                            found = True
                        # del currents[idx]
                        # print("break2")
                        break
                    else:
                        if required_roles:
                            found = False
                        else:
                            found = True
                        # print("break3")
                        break
                else:
                    assert dep_direction is None#stop iteration
                    if required_roles:
                        found = False
                    else:
                        found = True
                    # print("break4")
                    break
            if found is True:
                # print("role2",role)
                relations.append(role)
            elif found is False:
                pass
            else:
                raise Impossible
            del currents[idx]
        final_results=[]
        for r in relations:
            rd = {}
            for k in r:
                rd[r[k]['role']]={"w":r[k]['w'],"idx":k}
            final_results.append(rd)


        return final_results

def generate_training_set(patterns,tokenDict,manual_relations):
    nodes = {}
    nodes[0] = Node(0, "ROOT", "ROOT")
    all_edges = {}
    tokenDict[-100]=new_token(index='-100',word="None",pos=None,lac_pos=None,dep=None,head='0',begin=None,end=None)
    #{'lac_pos':"None","word":"None","ref":{"fullname":"None","governor":0,"dep":"None"}}

    commas=set()

    for a in tokenDict:

        token = tokenDict[a]
        if token['lac_pos'] == -100:continue

        if token['word'] in ",，；;、":commas.add(a)

        if a not in nodes:
            nodes[a] = Node(a, token['word'], token['prefix']+token['word'])
        current_token_node = nodes[a]
        current_token = token
        current_token_node.addition = "a"

        while current_token['head'] in tokenDict and int(current_token['head']) > 0:
            if current_token['head'] not in nodes:
                father_token = tokenDict[current_token['head']]
                father_token_node = Node(father_token['index'], father_token['word'], father_token['prefix']+father_token['word'])
                nodes[current_token['head']] = father_token_node
            else:
                father_token = tokenDict[current_token['head']]
                father_token_node = nodes[current_token['head']]

            if father_token_node.name + current_token['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['dep'], current_token_node)
            current_token, current_token_node = father_token, father_token_node

        if current_token['head'] == 0:
            father_token_node = nodes[0]
            if father_token_node.name + current_token['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['dep'], current_token_node)

    # async_run_draw(tree_to_string(nodes[0]),daemon=False)
    pattern=None
    pattern1,pattern0=None,None
    training_data_by_pattern={}
    for pattern00 in patterns:
        relations = []
        ARB=1
        AB=0
        if "," in pattern00:
            relationType=ARB
            pattern0,pattern1=pattern00.split(",")
        else:
            relationType=AB
            r="NOT_AVAILABLE"
            if "?" in pattern00:
                pattern,r=pattern00.split("?")
            else:
                pattern=pattern00
        for tokenIndex in tokenDict:
            if relationType==AB:
                results=find_relation_by_pattern_token_and_tree_given(tokenIndex,pattern,nodes,tokenDict)
                for i in results:
                    i['r']={'w':r,'idx':-100}
                    i['pattern']=pattern
                #print(results)
                relations=relations+results
            elif relationType==ARB:
                firstStage=find_relation_by_pattern_token_and_tree_given(tokenIndex,pattern0,nodes,tokenDict)

                for possible in firstStage:
                    nextIndex=possible['r']['idx']
                    nextStage=find_relation_by_pattern_token_and_tree_given(nextIndex,pattern1,nodes,tokenDict)
                    if nextStage:
                        for rb in nextStage:
                            rb.update(possible)
                            rb['pattern']=pattern
                            relations.append(rb)

        labeled_relations=set()
        for a,r,b in manual_relations:
            labeled_relations.add("%s,%s,%s"%(a,r if int(r) >0 else -100,b))

        data=[]
        label=[]

        for r in relations:
            # print(r)

            thisTraining,n_features=make_feature(r,commas=commas,tokens=tokenDict)

            data.append(thisTraining)
            if "%s,%s,%s"%(r['a']['idx'],r['r']['idx'],r['b']['idx']) in labeled_relations:
                label.append(CLASS["Y"])
                # if r['pattern'] and 'app' in r['pattern']:
                #     print("YEAH")
            else:
                # print("%d,%d,%d"%(r['a']['idx'],r['r']['idx'],r['b']['idx']) ,"not in ",labeled_relations)
                # if r['pattern'] and 'app' in r['pattern']:
                #     print("NO")
                label.append(CLASS["N"])
            # print(r['a']['w'],tokenDict[r['a']['idx']]['lac_pos'],r['r']['w'],r['b']['w'],tokenDict[r['b']['idx']]['lac_pos'],"  ",r['pattern'])
        # for i in range(len(data)):
        #     print(data,label)
        training_data_by_pattern[pattern00]=(data,label)
    return training_data_by_pattern

# @print_local_when_exception
def find_relation_by_pattern(patterns,tokenDict,print_result=True):
    nodes = {}
    nodes['0'] = Node('0', "ROOT", "ROOT")
    all_edges = {}
    for a in tokenDict:
        if int(a)<0:continue

        token = tokenDict[a]

        if a not in nodes:
            nodes[a] = Node(a, token['word'], token['prefix']+token['word'] if 'ref' in token and 'fullname' in token['ref'] else token['word'])

        current_token_node = nodes[a]
        current_token = token
        current_token_node.addition = "a"
        while  current_token['head']!="None" and int(current_token['head']) > 0:
            if current_token['head'] not in nodes:
                try:
                    father_token = tokenDict[current_token['head']]
                except KeyError as e:
                    print(e.__class__.__name__)
                    print(e.args)
                    print("father of %s (%s) not in tokenDict"%(current_token['word'],current_token['head']))
                    break
                else:
                    father_token_node = Node(father_token['index'], father_token['word'], father_token['prefix']+father_token['word'])
                    nodes[father_token['index']] = father_token_node
            else:
                father_token = tokenDict[current_token['head']]
                father_token_node = nodes[current_token['head']]

            if father_token_node.name + current_token['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['dep'], current_token_node)
            current_token, current_token_node = father_token, father_token_node


        if current_token['head'] == '0':
            father_token_node = nodes['0']
            if father_token_node.name + current_token['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['dep'], current_token_node)

    # t=Tree.fromstring(tree_to_string(nodes[0]))
    # t.draw()
    relations=[]
    for pattern in patterns:
        ARB=1
        AB=0
        if "," in pattern:
            relationType=ARB
            pattern0,pattern1=pattern.split(",")
        else:
            relationType=AB
            r="NOT_AVAILABLE"
            if "?" in pattern:
                pattern,r=pattern.split("?")
        for tokenIndex in tokenDict:
            if int(tokenIndex)<0:continue
            if relationType==AB:
                results=find_relation_by_pattern_token_and_tree_given(tokenIndex,pattern,nodes,tokenDict)
                for i in results:
                    i['r']={'w':r}
                    i['pattern']=pattern
                relations=relations+results
            elif relationType==ARB:
                firstStage=find_relation_by_pattern_token_and_tree_given(tokenIndex,pattern0,nodes,tokenDict)

                for possible in firstStage:
                    nextIndex=possible['r']['idx']
                    nextStage=find_relation_by_pattern_token_and_tree_given(nextIndex,pattern1,nodes,tokenDict)
                    if nextStage:
                        for rb in nextStage:
                            rb.update(possible)
                            rb['pattern']=pattern
                            relations.append(rb)

    if print_result:
        print("")
        for r in relations:
            print(r['a']['w'],tokenDict[r['a']['idx']]['lac_pos'],r['r']['w'],r['b']['w'],tokenDict[r['b']['idx']]['lac_pos'],"  ",r['pattern'])
    return relations
    # t.draw()

if __name__=="__main__":
    # extract_dep_patterns(to_write=True)
    train_pattern_classifier()
    # g = line_generator('tagged.json')
    #
    # # of = open("tagged.json", "w", encoding='utf8')
    #
    # for line in g:
    #     article = json.loads(line)
    #     sentences = article['sentences']
    #
    #     for sentence in sentences:
    #         print(find_relation_by_pattern(['(b)<-[:appos]-(a) ?is'],sentence['tokens']))