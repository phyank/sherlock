from tools import *
from kg import *
if __name__=="__main__":
    g = line_generator("tagged.json")

    conf_dict = get_local_settings()

    graph = Graph(uri=conf_dict['neo4j_address'], auth=(conf_dict['neo4j_user'], conf_dict['neo4j_pass']))

    index=0
    while True:
        try:
            articleJSON = json.loads(g.__next__())
        except StopIteration:
            break
        else:
            add_case(graph, articleJSON['sentences'], index)
            index+=1