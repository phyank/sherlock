# from tools import *
import json,math,time

from urllib.parse import urlencode
from urllib.request import urlopen

from threading import Thread

from queue import Queue

result_queue=Queue()

THREADS=6

def line_generator(fn,encoding='utf8'):
    jf = open(fn,encoding=encoding)
    while True:
        line=jf.readline()
        if line:
            yield line
        else:
            return

def lac_cut(article,port=18080):
    result = urlopen("http://127.0.0.1:%d/lac"%port,
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    # print(result)

    words = result.split("\t")

    a=[]
    for word in words:
        word = word.split(" ")
        if len(word)!=4:continue
        a.append({"word": word[0], "type": word[1], "start": word[2], "length": word[3]})

    return a,result

with open("knowledge/punctuation.txt","r") as punc_file:
    punc0=punc_file.read()

puncSet=set(punc0.split(" "))

# g = line_generator("final_all_data/first_stage/train.json")


def run_statistics(outQueue,skip=1,num=0,port=18080):
    g = line_generator("final_all_data/first_stage/train.json")

    logfile=open("cut%d.txt"%num,"a",encoding="utf8")

    wordListByAccusation={}
    wordCountByAccusation={}
    articleCount={}
    for i in range(1000000):
        try:
            articleJSON = json.loads(g.__next__())
        except StopIteration:
            break


        if i%skip!=num:continue

        accusations=articleJSON['meta']['accusation']
        for accusation in accusations:
            try:
                articleCount[accusation] += 1
            except KeyError:
                articleCount[accusation] = 1

        wordlist,tokenized = lac_cut(articleJSON["fact"].replace("\r\n", "").replace("\n", ""),port=port)
        logfile.writelines(tokenized+"|||")
        for word in wordlist:
            if word['word'] in puncSet or word['type'] in "mcfqurxcpwTIMEPERLOCORG":
                continue
            else:
                word=word['word']+word['type']
                for accusation in accusations:
                    if accusation not in wordListByAccusation:
                        wordListByAccusation[accusation]={}
                    if accusation not in wordCountByAccusation:
                        wordCountByAccusation[accusation]=0

                    try:
                        wordListByAccusation[accusation][word]+=1
                    except:
                        wordListByAccusation[accusation][word]=1
                    wordCountByAccusation[accusation]+=1

    outQueue.put({"wordList":wordListByAccusation,"wordCount":wordCountByAccusation,"article":articleCount})



def test(read=False):

    start=time.time()
    if not read:
        wordListByAccusation = {}
        wordCountByAccusation = {}
        articleCount = {}

        threads=[]
        for i in range(THREADS):
            threads.append(Thread(target=run_statistics,args=(result_queue,THREADS,i,18080+i)))
            threads[i].daemon=True
            threads[i].start()


        while True:
            alive=False
            for thread in threads:
                alive=alive or thread.is_alive()
            if not alive :break

        while not result_queue.empty():
            aResult=result_queue.get()
            for accusation in aResult['wordList']:
                if accusation not in wordListByAccusation:
                    wordListByAccusation[accusation]={}

                try:
                    articleCount[accusation]+=aResult['article'][accusation]
                except KeyError:
                    articleCount[accusation] = aResult['article'][accusation]

                try:
                    wordCountByAccusation[accusation]+=aResult['wordCount'][accusation]
                except KeyError:
                    wordCountByAccusation[accusation] = aResult['wordCount'][accusation]

                # print(aResult['wordList'][accusation].keys())
                for word in aResult['wordList'][accusation]:
                    # assert word in aResult['wordList'][accusation]
                    try:
                        wordListByAccusation[accusation][word]+=aResult['wordList'][accusation][word]
                    except KeyError:
                        wordListByAccusation[accusation][word] = aResult['wordList'][accusation][word]
    else:
        with open("term_freq.json","r") as jfile:
            j=json.load(jfile)
        wordListByAccusation,wordCountByAccusation,wordAppearInAccusations,articleCount=\
        j['word_list'],j['word_count'],j['word_appear'],j['article_count']

    # accusationCount=len(wordListByAccusation)
    # wordAppearInAccusations={}
    # tfs={}
    # save=True
    # for accusation in wordListByAccusation:
    #     print("Accusation: %s(%d articles)"%(accusation,articleCount[accusation]))
    #
    #     for word in wordListByAccusation[accusation]:
    #         tfs[word]=wordListByAccusation[accusation][word]/articleCount[accusation]
    #         try:
    #             wordAppearInAccusations[word].add(accusation)
    #         except KeyError:
    #             wordAppearInAccusations[word]={accusation}
    # tfidfs={}
    # for word in wordAppearInAccusations:
    #     tfidfs[word]=tfs[word]*math.log(accusationCount/len(wordAppearInAccusations[word]),math.e)
    #
    #         # print("%s  %d %d %.4f"%(word,wordListByAccusation[accusation][word],wordCountByAccusation[accusation],wordListByAccusation[accusation][word]/wordCountByAccusation[accusation]))
    #     #     words.append((tf,word))
    #     # words=sorted(words,reverse=True)
    #     # for word in words[:20]:
    #     #     print("%s %.5f"%(word[1],word[0]))
    accusationCount = len(wordListByAccusation)
    wordAppearInAccusations={}
    tfs={}
    for accusation in wordListByAccusation:
        print("Accusation: %s(%d articles)"%(accusation,articleCount[accusation]))

        for word in wordListByAccusation[accusation]:
            tfs[word]=wordListByAccusation[accusation][word]/wordCountByAccusation[accusation]
            try:
                wordAppearInAccusations[word].add(accusation)
            except KeyError:
                wordAppearInAccusations[word]={accusation}
    # for word in wordAppearInAccusations:
    #     wordAppearInAccusations[word]=len(wordAppearInAccusations[word])
    tfidfs={}
    for word in wordAppearInAccusations:
        tfidfs[word]=(tfs[word]*math.log(accusationCount/len(wordAppearInAccusations[word]),math.e),";".join(wordAppearInAccusations[word]))

            # print("%s  %d %d %.4f"%(word,wordListByAccusation[accusation][word],wordCountByAccusation[accusation],wordListByAccusation[accusation][word]/wordCountByAccusation[accusation]))
        #     words.append((tf,word))
        # words=sorted(words,reverse=True)
        # for word in words[:20]:
        #     print("%s %.5f"%(word[1],word[0]))
    words=sorted([(tfidfs[word][0],word,tfidfs[word][1]) for word in tfidfs],reverse=True)

    for word in words[:200]:
        print("%s %.5f in %s"%(word[1],word[0],word[2]))

    tfwords=sorted([(tfs[w],w) for w in tfs],reverse=True)

    for word in tfwords[:100]:
        print("%s %.5f" % (word[1], word[0]))

    if not read:
        with open("term_freq.json","w") as of:
            json.dump({"word_list":wordListByAccusation,"word_count":wordCountByAccusation,"word_appear":wordAppearInAccusations,"article_count":articleCount},of)
    print("total spend %.2f seconds."%(time.time()-start))

if __name__=="__main__":
    test(read=True)