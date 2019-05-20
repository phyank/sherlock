import MySQLdb,time

from tools_general import *

batch_size=100

def create_table():
    conn=MySQLdb.connect(host="localhost",port=3306,user="nlpuser",passwd="testmysqltest",database="nlp")

    cursor=conn.cursor()
    cursor.execute("create table tencent_word_embeddings(word char(30) primary key not null,%s)  DEFAULT CHARSET=utf8;"%(",".join((("dim%d double not null"%i) for i in range(200)))))
    cursor.execute("ALTER TABLE tencent_word_embeddings MODIFY word varchar(30) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL;")
def add_vecs():
    conn = MySQLdb.connect(host="localhost", port=3306, user="nlpuser", passwd="testmysqltest", database="nlp")
    conn.autocommit(1)

    conn.set_character_set('utf8')


    cursor = conn.cursor()

    cursor.execute('SET NAMES utf8;')
    cursor.execute('SET CHARACTER SET utf8;')
    cursor.execute('SET character_set_connection=utf8;')

    cursor.execute("select count(1) from tencent_word_embeddings;")
    result=cursor.fetchall()
    jump=result[0][0]+1
    jump0=jump
    print("Start from %d line"%jump)
    g=line_generator("D:/Tencent_AILab_ChineseEmbedding.txt")

    last_calc_start=time.time()

    i=0
    batch=[]
    for line0 in g:
        if jump:
            jump-=1
            continue
        line=line0.split(" ")
        if len(line)!=201:
            print("broken line %s"%line0)
            continue
        else:
            word=line[0]
            vec=[i for i in line[1:]]

            value="('"+conn.escape_string(word).decode("utf8")+"',%s)"%(",".join(vec))
            batch.append(value)
            if len(batch)>batch_size:
                sql="insert into tencent_word_embeddings values %s;"%(",".join(batch))
                print("calc spend %.4f seconds"%(time.time()-last_calc_start))
                try:
                    run_sql_start=time.time()
                    cursor.execute(sql)
                    print("sql spend %.4f seconds"%(time.time()-run_sql_start))
                except:
                    print(sql)
                    raise Exception
                else:
                    batch=[]
                    jump0+=batch_size
                    print("Put %d records"%jump0)
                    last_calc_start=time.time()

    if batch:
        sql = "insert into tencent_word_embeddings values %s;" % (",".join(batch))
        try:
            cursor.execute(sql)
        except:
            print(sql)
            raise Exception
        else:
            jump0 += len(batch)
            print("Put %d records" % jump0)
            batch = []

add_vecs()