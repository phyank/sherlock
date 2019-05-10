from tools import *
from kg import *
if __name__=="__main__":
    g = line_generator("tagged.json")

    conf_dict = get_local_settings()

    graph = Graph(uri=conf_dict['neo4j_address'], auth=(conf_dict['neo4j_user'], conf_dict['neo4j_pass']))

    for label in ("LegalCase", "Keyword", "Location", "Person", "Organization", "Time", "Item", "Entity","Action"):
        graph.run("CREATE INDEX ON :%s(name)" % label)

    with open("critical","r",encoding="utf8") as pfile:
        lines=pfile.readlines()

    regExractor=RegExtractor(patterns=lines)

    index=0
    while True:
        try:
            articleJSON = json.loads(g.__next__())
        except StopIteration:
            break
        else:


            add_case(graph, articleJSON['sentences'],articleJSON['fact'], index,regExractor)
            index+=1