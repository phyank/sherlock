import json

from py2neo import Graph

from tools import *
from relation_walker import *

graph=Graph(uri="127.0.0.1:7474",auth=("neo4j","Cion24"))

PATTERNS=['(b)<-[:appos]-(a) ?isA','(r)<-[:nsubj]-(a) , (r)<-[:dobj]-(b)',
          '(a) - [:nsubj]->() < -[: conj]-(r), (r) < -[: dobj]-(b)',
          '(b)-[:dep]->()<-[:conj]-(a) ?isA',]

PATTERN_REQUIREMENTS={
'(b)<-[:appos]-(a) ':{'a':'PER|n|nr','b':"PER|n|nr"},
'(r)<-[:nsubj]-(a) , (r)<-[:dobj]-(b)':{'a':'PER|n|nr','b':'n|nr'},
'(a) - [:nsubj]->() < -[: conj]-(r), (r) < -[: dobj]-(b)':{'a':'PER','b':'n|nz|nr'},
'(b)-[:dep]->()<-[:conj]-(a) ':{'a':'n|PER|nr','b':'PER|n|nr'}
}

POS_TO_LABEL={
    "PER":"Person",
    "ORG":"Organization",
    "TIME":"Time",
    "n":"Item",
    "nr":"Item",
    "LOC":"Location",
    "nz":"Item",
    "nw":"Item"
}

def get_word_label(pos):
    try:
        return POS_TO_LABEL[pos]
    except KeyError:
        return "Entity"

for article in line_generator("tagged.json", encoding='gbk'):
    articleDict = json.loads(article)

    lastSentenceSubject = None
    lastSentenceMainVerb = None
    lastSentenceTime = None
    index=0

    for sentence in articleDict['sentences']:
        index+=1

        caseName="Case%d"%index

        graph.run("MERGE (:LegalCase{name:'%s'})"%caseName)

        tokenDict=sentence['tokens']

        for tokenIndex in tokenDict:
            token=tokenDict[tokenIndex]

            if "LOC" in token['lac_pos']:
                graph.run("MERGE (:Location{name:'%s'});" % (token['word']))
                graph.run("MERGE (n:Location{name:'%s'}) ON MATCH SET n.prefix = '%s';"%(token['word'],token['prefix']))
                graph.run("MATCH (a:LegalCase),(b:Location) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:地理位于]->(b);"%(caseName,token['word']))
            elif "PER" in token['lac_pos']:
                graph.run("MERGE (:Person{name:'%s'});" % (token['word']+"_"+caseName))
                graph.run(
                    "MERGE (n:Person{name:'%s'}) ON MATCH SET n.prefix = '%s';" % (token['word']+"_"+caseName, token['prefix']))
                graph.run(
                    "MATCH (a:LegalCase),(b:Person) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:人物]->(b);" % (
                    caseName, token['word']+"_"+caseName))
            elif "ORG" in token['lac_pos']:
                graph.run("MERGE (:Organization{name:'%s'});" % (token['word']))
                graph.run(
                    "MERGE (n:Organization{name:'%s'}) ON MATCH SET n.prefix = '%s';" % (token['word'], token['prefix']))
                graph.run(
                    "MATCH (a:LegalCase),(b:Organization) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:相关组织]->(b);" % (
                    caseName, token['word']))
            elif "TIME" in token['lac_pos']:
                graph.run("MERGE (:Time{name:'%s'});" % (token['word']))
                graph.run(
                    "MERGE (n:Time{name:'%s'}) ON MATCH SET n.prefix = '%s';" % (
                    token['word'], token['prefix']))

                graph.run(
                    "MATCH (a:LegalCase),(b:Time) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:相关时间]->(b);" % (
                    caseName, token['word']))

            for relation in find_relation_by_pattern(PATTERNS,tokenDict):
                requirements=PATTERN_REQUIREMENTS[relation['pattern']]
                match=True
                for k in requirements:
                    all_pos=requirements[k].split("|")

                    if tokenDict[relation[k]['idx']]['lac_pos'] not in all_pos:
                        print(all_pos,tokenDict[relation[k]['idx']]['lac_pos'])
                        match=False
                        break
                if not match:
                    print("not match")
                    continue
                else:
                    a,r,b=tokenDict[relation['a']['idx']],relation['r'],tokenDict[relation['b']['idx']]

                    enames={}
                    for role,i in (("a",a),("b",b)):
                        if i['lac_pos']=="PER":
                            enames[role]=i['word']+"_"+caseName
                        else:
                            enames[role]=i['word']
                        cy="MERGE (:%s{name:'%s'});" % (get_word_label(i['lac_pos']),enames[role])
                        print(cy)
                        graph.run(cy)

                        cy="MERGE (n:%s{name:'%s'}) ON MATCH SET n.prefix = '%s';" % (
                                get_word_label(i['lac_pos']),enames[role], i['prefix'])
                        print(cy)
                        graph.run(cy)
                    graph.run(
                            "MATCH (a:%s),(b:%s) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:%s]->(b);" % (
                                get_word_label(a['lac_pos']),get_word_label(b['lac_pos']),enames['a'],enames['b'], r['w']))

