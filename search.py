"""
这是一个在CAIL2018中进行关键字搜索的小工具
"""

import json

def line_generator(fn,encoding='utf8'):
    jf = open(fn,encoding=encoding)
    while True:
        line=jf.readline()
        if line:
            yield line
        else:
            return

def search_keyword_any(keyword='test',crime_exempt=''):
    g = line_generator("final_all_data/first_stage/train.json")

    while True:
        try:
            articleJSON = json.loads(g.__next__())
        except StopIteration:
            break

        if keyword in articleJSON['fact']:
            jump=False
            for accusation in articleJSON['meta']['accusation']:
                if accusation in  crime_exempt:
                    jump=True
                    break
            if jump: continue
            print('crime: %s'%";".join(articleJSON['meta']['accusation']))
            print(articleJSON['fact'])

        continue

def search_keyword_any_baike(keyword='test',word=True):
    g = line_generator("D:\\Downloads\\baiketriples\\baike_triples.txt")

    while True:
        try:
            line=g.__next__()
        except StopIteration:
            break

        a,r,b=line.split("\t")
        if word:
            if keyword in a:
                print(line)
        else:
            if keyword in a or keyword in r or keyword in b:
                print(line)

        continue

if __name__=="__main__":
    search_keyword_any_baike('钝器')