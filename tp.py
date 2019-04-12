from  py2neo import Graph

class TT:
    def __init__(self):
        self.a=None

def tt(a):
    a.a=1

ttt=TT()
ttt.a=0
tt(ttt)
print(ttt.a)

for i in range(10):
    with open("test.txt",'a') as jf:
        jf.write("1\n")


def make_text(current):
    if "Topic" in current['data_type']:
        finalText=''
        for item in current['data']:
            finalText+=make_text(item)
        return finalText
    else:
        data=current['data']
        dataType=current['data_type']
        context=current['context']
        text=''

        #这里创建格式化文本

        return text

def test_neo4j():
    g=Graph(uri="127.0.0.1:7474",user="root",passwd="Cion24")
    c=g.run("MATCH (n:HelloWorld) RETURN n;")
    for i in c:
        print(i)

if __name__=="__main__":
    test_neo4j()