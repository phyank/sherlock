from tools import *

g = line_generator("final_all_data/first_stage/train.json")

while True:
    articleJSON = json.loads(g.__next__())
    accusations=articleJSON['meta']['accusation']
    wordlist = lac_cut(articleJSON["fact"].replace("\r\n", "").replace("\n", ""))
    print(wordlist)
    break