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
            _,path,hit=find_path_in_tree2(root,"a","b")
            dd="%s ?%s"%(path,special_r[r])

        else:
            _,path1,hit1=find_path_in_tree2(root,"a","r")
            _,path2,hit2=find_path_in_tree2(root,"r","b")
            dd=("%s , %s"%(path1,path2))

        try:
            final[dd]+=1
        except:
            final[dd]=1

        # tstr=tree_to_string(root)
        # t = Tree.fromstring(tstr)
        # t.draw()
    elif a<0:
        pass
    elif b<0:
        pass
    else:
        raise Impossible

def test():
    final = {}
    for article in line_generator("tagged.json",encoding='gbk'):
        articleDict=json.loads(article)



        lastSentenceSubject=None
        lastSentenceMainVerb=None
        lastSentenceTime=None
        for sentence in articleDict['processed_sentences']:

            tokenDict = {0: {"word": "ROOT"}}
            for k in special:
                tokenDict[special[k]] = {"word": k}
            for k in default_character:
                tokenDict[default_character[k]] = {"word": k}

            for word in sentence['tokens']:
                tokenDict[word['index']] = word
                word['ref']['fullname'] = \
                    word['word']

            ranked_tokens={}
            for idx in sorted([i['index'] for i in sentence['tokens']],reverse=True):
                ranked_tokens[idx]=tokenDict[idx]


            for word_index in ranked_tokens:
                word=ranked_tokens[word_index]
                if word['ref']['governor'] != 0 and tokenDict[word['ref']['governor']]['pos'] in ("NN", "NR") and \
                        tokenDict[word['ref']['dependent']]['pos'] not in ("PU"):
                    # print(word)
                    # print("%s PING %s"%(tokenDict[word['ref']['governor']]['ref']['fullname'],word['word']))
                    tokenDict[word['ref']['governor']]['ref']['fullname'] = \
                            word['word'] + "|" + tokenDict[word['ref']['governor']]['ref']['fullname']

            testtest = find_relation_by_pattern(['(r)<-[:conj]-()<-[:conj]-(b)'], ranked_tokens)

            for a,r,b in sentence['manual_relations']:
                get_words_relations(a,r,b,tokenDict,final)
    for pattern,frequency in sorted(final.items(),key=lambda i:i[1],reverse=True):
        print(pattern,frequency)


def find_relation_by_pattern(patterns,tokenDict):
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
        for tokenIndex in tokenDict:
            token=tokenDict[tokenIndex]
            if ("<" not in pattern and ">" in pattern) or(">" not in pattern and "<" in pattern):
                if "<" in pattern:reverse=True
                else:reverse=False

                if ">" in pattern:
                    r_pttrn=r"-\[[\w\d:]+\]->"
                else:
                    r_pttrn = r"<-\[[\w\d:]+\]-"
                pttrn_nodes_path=re.findall("\([\w\d_]*\)",pattern)
                pttrn_nodes_path=[i[:-1][1:] for i in pttrn_nodes_path]

                required_roles=set()
                for i in pttrn_nodes_path:
                    if i:required_roles.add(i)

                pttrn_relation_path0=re.findall(r_pttrn,pattern)
                pttrn_relation_path = [re.search("[\w\d]+:?[\w\d]*", i).group() for i in pttrn_relation_path0]
                if reverse:
                    pttrn_nodes_path.reverse()
                    pttrn_relation_path.reverse()

                assert pttrn_nodes_path and pttrn_relation_path
                role={}
                relation_gen=(i for i in pttrn_relation_path)

                current=nodes[tokenIndex]
                found=True
                for pttrn_node in pttrn_nodes_path:
                    try:
                        pttrn_dep=relation_gen.__next__()
                    except StopIteration:
                        pttrn_dep=None

                    if pttrn_node:
                        assert pttrn_node not in role
                        role[current.index]=current.name+pttrn_node
                        required_roles.remove(pttrn_node)

                    if pttrn_dep is not None and current.in_relation is not None:
                        if pttrn_dep==current.in_relation.name:
                            current=current.father
                            continue
                        else:
                            found=False
                            break
                    else:
                        if required_roles:
                            found=False
                        break
                if found:
                    # print(required_roles)
                    relations.append(role)
    print(relations)











if __name__=="__main__":
    test()