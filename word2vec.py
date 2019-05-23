from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
import MySQLdb

from scipy.spatial.distance import cosine,jaccard

from tools_cpython import *

def train():
    sentences=LineSentence("cut/lineSentence.txt")

    model=Word2Vec(sentences,size=200,window=7,min_count=10,workers=6,sg=1)
    model.save("knowledge/word2vec.model")

def test():
    model = Word2Vec.load("knowledge/word2vec.model")
    vectors=model.wv
    print(vectors.cosine_similarities(vectors['云南'],[vectors['汽车'],vectors['摩托'],vectors['自行车']]))

def test_tencent():
    conn = MySQLdb.connect(host="localhost", port=3306, user="nlpuser", passwd="testmysqltest", database="nlp")
    conn.autocommit(1)

    conn.set_character_set('utf8')

    cursor = conn.cursor()

    cursor.execute('SET NAMES utf8;')
    cursor.execute('SET CHARACTER SET utf8;')
    cursor.execute('SET character_set_connection=utf8;')

    words={"云南省":None,"云南":None,"四川":None,"四川省":None,"北京":None,"军舰":None}
    for word in words:
        cursor.execute("select * from tencent_word_embeddings where word='%s';"%word)
        result=cursor.fetchall()
        if not result or not result[0]:pass
        else:
            words[word]=result[0][1:]
    print(words)

    print(cosine(words['云南省'],words['云南']))
    print(cosine(words['四川'], words['四川省']))
    print(cosine(words['军舰'], words['云南']))

def test_cosine(a,b):
    conn = MySQLdb.connect(host="localhost", port=3306, user="nlpuser", passwd="testmysqltest", database="nlp")
    conn.autocommit(1)

    conn.set_character_set('utf8')

    cursor = conn.cursor()

    cursor.execute('SET NAMES utf8;')
    cursor.execute('SET CHARACTER SET utf8;')
    cursor.execute('SET character_set_connection=utf8;')

    d={"a":None,"b":None}

    for c,word in (("a",a),("b",b)):
        cursor.execute("select * from tencent_word_embeddings where word='%s';"%word)
        result=cursor.fetchall()
        if not result or not result[0]:pass
        else:
            d[c]=result[0][1:]

    print("%s vs. %s cosine distance:%.10f"%(a,b,cosine(d['a'],d['b'])))
    # print("%s with %s Diff jaccard:%.10f" % (a, b, jaccard(d['a'], d['b'])))

test_cosine("盘州","盘县")