import threading

from tools_general import *

ALL_DATA_PATHS=["final_all_data/first_stage/train.json","final_all_data/first_stage/test.json","final_all_data/restData/rest_data.json"]

OUTPUT_DIR="cut"

def cut_worker(myid=0,jump=1,lac_addr="localhost",lac_port=18080):
    try:
        of=open(OUTPUT_DIR+"/cut%d.json"%myid,"r" ,encoding='utf8')
    except:
        with open(OUTPUT_DIR+"/cut%d.json"%myid,"w"):
            pass
        of = open(OUTPUT_DIR+"/cut%d.json"%myid, "r",encoding='utf8')
    
    last_index=0
    while True:
        line=of.readline()
        if not line:break
        else:
            last_index+=1
    of.close()
    print("Thread %d last_index %d"%(myid,last_index))

    of = open(OUTPUT_DIR + "/cut%d.json" % myid, "a", encoding='utf8')
    index=0
    for path in ALL_DATA_PATHS:
        g = line_generator(path)
        lineNum=1
        while True:
            try:
                nextLine=g.__next__()
            except StopIteration:
                break
            else:
                lineNum+=1
                if lineNum%jump!=myid:continue
                else:            
                    index+=1
                    if index<=last_index:continue
                    else:
                        articleJSON=json.loads(nextLine)
                        wordlist = lac_cut(articleJSON["fact"].replace("\r\n", "").replace("\n", ""),
                                           addr=lac_addr,
                                           port=lac_port)
                        articleJSON['cut']=wordlist

                        of.write(json.dumps(articleJSON, ensure_ascii=False))
                        of.write("\n")
                        print("dump %d"%index)


if __name__=="__main__":
    threads=[]
    for i in range(6):
        thread=threading.Thread(target=cut_worker,args=(i,6,"192.168.59.141",int("1808%d"%i)))
        thread.start()
    
                
                
                
        