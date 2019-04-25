import traceback,json
from copy import deepcopy
from tools import *
from definitions import *

from nltk.tree import Tree

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
    if a>=0 and b>=0:
        nodes={}

        nodes[0]=Node(0,"ROOT","ROOT")

        all_edges={}

        token=tokenDict[a]

        if a not in nodes:
            nodes[a]=Node(a,token['word'],token['ref']['fullname'])
        current_token_node=nodes[a]
        current_token=token
        current_token_node.addition="a"

        while current_token['ref']['governor']>0:
            if current_token['ref']['governor'] not in nodes:
                father_token=tokenDict[current_token['ref']['governor']]
                father_token_node=Node(father_token['index'],father_token['word'],father_token['ref']['fullname'])
                nodes[current_token['ref']['governor']]=father_token_node
            else:
                father_token=tokenDict[current_token['ref']['governor']]
                father_token_node=nodes[current_token['ref']['governor']]

            if father_token_node.name+current_token['ref']['dep']+current_token_node.name not in all_edges:
                all_edges[father_token_node.name+current_token['ref']['dep']+current_token_node.name]=\
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)
            current_token, current_token_node = father_token, father_token_node

        if current_token['ref']['governor']==0:
            father_token_node = nodes[0]
            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)

        token = tokenDict[b]

        # print(token['ref']['fullname'])
        if b not in nodes:
            nodes[b] = Node(b, token['word'], token['ref']['fullname'])
        current_token_node = nodes[b]
        current_token = token
        current_token_node.addition = "b"

        while current_token['ref']['governor'] > 0:
            if current_token['ref']['governor'] not in nodes:
                father_token = tokenDict[current_token['ref']['governor']]
                father_token_node = Node(father_token['index'], father_token['word'], father_token['ref']['fullname'])
                nodes[current_token['ref']['governor']] = father_token_node
            else:
                father_token = tokenDict[current_token['ref']['governor']]
                father_token_node = nodes[current_token['ref']['governor']]

            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)

            # print("(%s)<-[%s]-(%s)"%(father_token_node.fullname, current_token['ref']['dep'], current_token_node.fullname))
            current_token, current_token_node = father_token, father_token_node

        if current_token['ref']['governor'] == 0:
            father_token_node = nodes[0]
            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)

        if r>0:
            if r not in nodes:
                nodes[r] = Node(r, token['word'], token['ref']['fullname'])
                current_token_node = nodes[r]
                current_token = token
                current_token_node.addition = "r"

                while current_token['ref']['governor'] > 0:
                    if current_token['ref']['governor'] not in nodes:
                        father_token = tokenDict[current_token['ref']['governor']]
                        father_token_node = Node(father_token['index'], father_token['word'],
                                                 father_token['ref']['fullname'])
                        nodes[current_token['ref']['governor']] = father_token_node
                    else:
                        father_token = tokenDict[current_token['ref']['governor']]
                        father_token_node = nodes[current_token['ref']['governor']]

                    if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                        all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                            Edge(father_token_node, current_token['ref']['dep'], current_token_node)

                    # print("(%s)<-[%s]-(%s)"%(father_token_node.fullname, current_token['ref']['dep'], current_token_node.fullname))
                    current_token, current_token_node = father_token, father_token_node

                if current_token['ref']['governor'] == 0:
                    father_token_node = nodes[0]
                    if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                        all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                            Edge(father_token_node, current_token['ref']['dep'], current_token_node)
            else:
                nodes[r].addition="r"
        else:
            pass

        root = nodes[0]
        if r<0:
            _,path_left,hit=find_path_in_tree2(root,"a","b",direction=LEFT)
            _, path_right, hit = find_path_in_tree2(root, "a", "b", direction=RIGHT)
            for path in (path_left,path_right):
                dd="%s ?%s"%(path,special_r[r])
                found=False
                try:
                    final[dd]+=1
                except:
                    continue
                else:
                    found=True
                    break
            if not found:final[dd]=1

        else:
            _,path1_left,hit1=find_path_in_tree2(root,"a","r",direction=LEFT)
            _, path1_right, hit1 = find_path_in_tree2(root, "a", "r",direction=RIGHT)
            _,path2_left,hit2=find_path_in_tree2(root,"r","b",direction=LEFT)
            _, path2_right, hit2 = find_path_in_tree2(root, "r", "b", direction=RIGHT)
            path1=[path1_left,path1_right]
            path2=[path2_left,path2_right]

            found=False
            for p1 in path1:
                for p2 in path2:

                    dd=("%s , %s"%(p1,p2))

                    try:
                        final[dd]+=1
                    except:
                        continue
                    else:
                        found=True
                        break
                if found:break
            if not found:
                final[dd]=1

    elif a<0:
        pass
    elif b<0:
        pass
    else:
        raise Impossible

def make_ranked_token_dict(tokens,reverse=True):
    tokenDict = {0: {"word": "ROOT"}}
    for k in special:
        tokenDict[special[k]] = {"word": k}
    for k in default_character:
        tokenDict[default_character[k]] = {"word": k}

    for word in tokens:
        tokenDict[word['index']] = word
        word['ref']['fullname'] = \
            word['word']

    ranked_tokens = {}
    for idx in sorted([i['index'] for i in tokens], reverse=reverse):
        ranked_tokens[idx] = tokenDict[idx]

    print(" ".join((ranked_tokens[i]['word'] for i in ranked_tokens)))
    for word_index in ranked_tokens:
        word = ranked_tokens[word_index]
        if word['ref']['governor'] != 0 and tokenDict[word['ref']['governor']]['pos'] in ("NN", "NR") and \
                tokenDict[word['ref']['dependent']]['pos'] not in ("PU"):
            # print(word)
            # print("%s PING %s"%(tokenDict[word['ref']['governor']]['ref']['fullname'],word['word']))
            tokenDict[word['ref']['governor']]['ref']['fullname'] = \
                word['word'] + "|" + tokenDict[word['ref']['governor']]['ref']['fullname']
    return ranked_tokens

def train_pattern_classifier():
    with open("dependencyRelationPattern.json", 'r') as infile:
        patterns0 = json.load(infile)

        patterns = []
        for i in patterns0:
            if i['frequency'] > 2:
                patterns.append(i['pattern'])
    training_set_by_pattern={}
    for article in line_generator("tagged.json", encoding='gbk'):
        articleDict = json.loads(article)

        lastSentenceSubject = None
        lastSentenceMainVerb = None
        lastSentenceTime = None
        for sentence in articleDict['processed_sentences']:
            ranked_tokens = make_ranked_token_dict(sentence['tokens'],reverse=False)

            this_training_set_by_pattern=generate_training_set(patterns, ranked_tokens, sentence['manual_relations'])
            for pattern in this_training_set_by_pattern:
                try:
                    training_set_by_pattern[pattern]['data']+=this_training_set_by_pattern[pattern][0]
                    training_set_by_pattern[pattern]['label'] += this_training_set_by_pattern[pattern][1]
                except KeyError:
                    training_set_by_pattern[pattern]={'data':this_training_set_by_pattern[pattern][0],
                                                      'label':this_training_set_by_pattern[pattern][1]}
    print(training_set_by_pattern)
def extract_dep_patterns(to_write=False):
    final = {}
    with open("dependencyRelationPattern.json", 'r') as infile:
        patterns0 = json.load(infile)

        patterns = []
        for i in patterns0:
            if i['frequency'] > 2:
                patterns.append(i['pattern'])
    for article in line_generator("tagged.json", encoding='gbk'):
        articleDict = json.loads(article)

        # lastSentenceSubject = None
        # lastSentenceMainVerb = None
        # lastSentenceTime = None
        for sentence in articleDict['processed_sentences']:
            ranked_tokens = make_ranked_token_dict(sentence['tokens'])

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
    tokenDict[-100]={'lac_pos':"None","word":"None","ref":{"fullname":"None","governor":0,"dep":"None"}}

    commas=set()

    for a in tokenDict:

        token = tokenDict[a]
        if token['lac_pos'] == -100:continue

        if token['word'] in ",，；;、":commas.add(a)

        if a not in nodes:
            nodes[a] = Node(a, token['word'], token['ref']['fullname'])
        current_token_node = nodes[a]
        current_token = token
        current_token_node.addition = "a"

        while 'ref' in current_token and current_token['ref']['governor'] > 0:
            if current_token['ref']['governor'] not in nodes:
                father_token = tokenDict[current_token['ref']['governor']]
                father_token_node = Node(father_token['index'], father_token['word'], father_token['ref']['fullname'])
                nodes[current_token['ref']['governor']] = father_token_node
            else:
                father_token = tokenDict[current_token['ref']['governor']]
                father_token_node = nodes[current_token['ref']['governor']]

            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)
            current_token, current_token_node = father_token, father_token_node

        if 'ref' in current_token and current_token['ref']['governor'] == 0:
            father_token_node = nodes[0]
            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)

    # async_run_draw(tree_to_string(nodes[0]),daemon=False)
    training_data_by_pattern={}
    for pattern in patterns:
        relations = []
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
            if relationType==AB:
                results=find_relation_by_pattern_token_and_tree_given(tokenIndex,pattern,nodes,tokenDict)
                for i in results:
                    i['r']={'w':r,'idx':-100}
                    i['pattern']=pattern
                print(results)
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
            labeled_relations.add("%d,%d,%d"%(a,r if r >0 else -100,b))

        data=[]
        label=[]

        for r in relations:
            # print(r)
            max_idx=max((r[k]['idx'] for k in r if k not in  ("pattern","id")))
            min_idx=min((r[k]['idx'] for k in r if k not in  ("pattern","id")))
            has_comma=False
            for comma in commas:
                if comma>min_idx and comma<max_idx:
                    has_comma=True
                    break
            data.append((tokenDict[r['a']['idx']]['lac_pos'],tokenDict[r['r']['idx']]['lac_pos'],tokenDict[r['b']['idx']]['lac_pos'],r['r']['idx']-r['a']['idx'],r['b']['idx']-r['r']['idx'],r['b']['idx']-r['a']['idx'],"comma" if has_comma else "no_comma"))
            if "%d,%d,%d"%(r['a']['idx'],r['r']['idx'],r['b']['idx']) in labeled_relations:
                label.append("Y")
            else:
                # print("%d,%d,%d"%(r['a']['idx'],r['r']['idx'],r['b']['idx']) ,"not in ",labeled_relations)
                label.append("N")
            # print(r['a']['w'],tokenDict[r['a']['idx']]['lac_pos'],r['r']['w'],r['b']['w'],tokenDict[r['b']['idx']]['lac_pos'],"  ",r['pattern'])
        # for i in range(len(data)):
        #     print(data,label)
        training_data_by_pattern[pattern]=(data,label)
    return training_data_by_pattern

def find_relation_by_pattern(patterns,tokenDict,print_result=True):
    nodes = {}
    nodes[0] = Node(0, "ROOT", "ROOT")
    all_edges = {}
    for a in tokenDict:
        token = tokenDict[a]

        if a not in nodes:
            nodes[a] = Node(a, token['word'], token['ref']['fullname'])
        current_token_node = nodes[a]
        current_token = token
        current_token_node.addition = "a"

        while current_token['ref']['governor'] > 0:
            if current_token['ref']['governor'] not in nodes:
                father_token = tokenDict[current_token['ref']['governor']]
                father_token_node = Node(father_token['index'], father_token['word'], father_token['ref']['fullname'])
                nodes[current_token['ref']['governor']] = father_token_node
            else:
                father_token = tokenDict[current_token['ref']['governor']]
                father_token_node = nodes[current_token['ref']['governor']]

            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)
            current_token, current_token_node = father_token, father_token_node

        if current_token['ref']['governor'] == 0:
            father_token_node = nodes[0]
            if father_token_node.name + current_token['ref']['dep'] + current_token_node.name not in all_edges:
                all_edges[father_token_node.name + current_token['ref']['dep'] + current_token_node.name] = \
                    Edge(father_token_node, current_token['ref']['dep'], current_token_node)
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