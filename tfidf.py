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

def lac_cut(article,addr="localhost",port=18080):
    result = urlopen("http://%s:%d/lac"%(addr,port),
                     urlencode({"passwd": 'rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i',
                                "sentence": article}).encode('utf8')).read().decode('utf8')

    print(result)

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


def run_statistics(outQueue,skip=1,num=0,port=18080,each=10,target_accusations=set()):

    print("Thread %d start"%num)
    g = line_generator("final_all_data/first_stage/train.json")

    logfile=open("cut%d.txt"%num,"a",encoding="utf8")

    wordListByAccusation={}
    wordCountByAccusation={}
    articleCount={}

    i=-1
    while True:

        try:
            articleJSON = json.loads(g.__next__())
        except StopIteration:
            break
        i += 1

        if i%skip!=num:continue

        accusations=articleJSON['meta']['accusation']

        jump=True
        for accusation in accusations:
            if accusation not in target_accusations:
                continue
            if accusation in articleCount and articleCount[accusation]>=each:
                continue
            else:
                jump=False
            try:
                articleCount[accusation] += 1
            except KeyError:
                articleCount[accusation] = 1

        if jump:continue

        wordlist,tokenized = lac_cut(articleJSON["fact"].replace("\r\n", "").replace("\n", ""),port=port,addr="192.168.59.141")
        logfile.writelines(tokenized+"|||")
        for word in wordlist:
            if word['word'] in puncSet or word['type'] in "mcfqurxcpwTIMEPERLOCORG":
                continue
            else:
                word=word['word']+word['type']
                for accusation in accusations:
                    if accusation not in articleCount:continue
                    if accusation not in wordListByAccusation:
                        wordListByAccusation[accusation]={}
                    if accusation not in wordCountByAccusation:
                        wordCountByAccusation[accusation]=0

                    try:
                        wordListByAccusation[accusation][word]+=1
                    except:
                        wordListByAccusation[accusation][word]=1
                    wordCountByAccusation[accusation]+=1

        mission_complete=True
        for accusation in target_accusations:
            if accusation in articleCount and articleCount[accusation]>=each:pass
            else:
                mission_complete=False
                break

        if mission_complete:break
        else:
            pass


    outQueue.put({"wordList":wordListByAccusation,"wordCount":wordCountByAccusation,"article":articleCount})



def test(read=False):

    target_accusations={'敲诈勒索',
                        '传播淫秽物品',
                        '滥用职权',
                        '虚开发票',
                        '脱逃',
                        '生产、销售假药',
                        '贷款诈骗',
                        '以危险方法危害公共安全',
                        '单位行贿',
                        '动植物检疫徇私舞弊',
                        '妨害信用卡管理',
                        '妨害公务',
                        '破坏易燃易爆设备',
                        '组织卖淫',
                        '重大责任事故',
                        '帮助毁灭、伪造证据',
                        '拒不执行判决、裁定',
                        '受贿',
                        '盗伐林木',
                        '开设赌场',
                        '玩忽职守',
                        '伪造、变造金融票证',
                        '隐匿、故意销毁会计凭证、会计帐簿、财务会计报告',
                        '非法采伐、毁坏国家重点保护植物',
                        '职务侵占',
                        '非法吸收公众存款',
                        '诬告陷害',
                        '伪造、变造居民身份证',
                        '伪造、变造、买卖武装部队公文、证件、印章',
                        '赌博',
                        '非法采矿',
                        '强迫卖淫',
                        '拒不支付劳动报酬',
                        '失火',
                        '行贿',
                        '非法转让、倒卖土地使用权',
                        '生产、销售伪劣产品', '抢劫', '强奸', '寻衅滋事', '生产、销售有毒、有害食品', '传授犯罪方法', '伪证', '假冒注册商标', '妨害作证', '引诱、容留、介绍卖淫', '出售、购买、运输假币', '销售假冒注册商标的商品', '破坏监管秩序', '盗窃', '聚众斗殴', '强迫交易', '挪用资金', '引诱、教唆、欺骗他人吸毒', '过失致人重伤', '爆炸',
                        '票据诈骗', '诈骗', '非法持有毒品', '窝藏、包庇', '非法占用农用地', '骗取贷款、票据承兑、金融票证', '窝藏、转移、隐瞒毒品、毒赃', '危险驾驶', '故意杀人', '破坏广播电视设施、公用电信设施', '窝藏、转移、收购、销售赃物', '侵占',
                        '破坏生产经营', '走私、贩卖、运输、制造毒品', '虐待', '容留他人吸毒', '掩饰、隐瞒犯罪所得、犯罪所得收益', '非法收购、运输盗伐、滥伐的林木', '过失致人死亡', '生产、销售不符合安全标准的食品', '污染环境', '信用卡诈骗', '非法处置查封、扣押、冻结的财产', '故意毁坏财物', '挪用公款', '非国家工作人员受贿', '交通肇事', '拐卖妇女、儿童',
                        '抢夺', '集资诈骗', '持有伪造的发票', '伪造、变造、买卖国家机关公文、证件、印章', '虚报注册资本', '招摇撞骗', '贪污', '猥亵儿童', '非法持有、私藏枪支、弹药', '保险诈骗', '滥伐林木',
                        '非法猎捕、杀害珍贵、濒危野生动物', '伪造公司、企业、事业单位、人民团体印章', '绑架', '破坏电力设备', '持有、使用假币', '盗掘古文化遗址、古墓葬', '放火', '重婚', '合同诈骗',
                        '非法侵入住宅', '组织、强迫、引诱、容留、介绍卖淫', '扰乱无线电通讯管理秩序', '非法拘禁', '冒充军人招摇撞骗', '制作、复制、出版、贩卖、传播淫秽物品牟利', '故意伤害', '非法制造、买卖、运输、邮寄、储存枪支、弹药、爆炸物', '组织、领导、参加黑社会性质组织', '非法经营', '盗窃、抢夺枪支、弹药、爆炸物', '盗窃、抢夺枪支、弹药、爆炸物、危险物质', '强制猥亵、侮辱妇女', '制造、贩卖、传播淫秽物品', '虚开增值税专用发票、用于骗取出口退税、抵扣税款发票'}

    start=time.time()
    if not read:
        wordListByAccusation = {}
        wordCountByAccusation = {}
        articleCount = {}

        threads=[]
        for i in range(THREADS):
            threads.append(Thread(target=run_statistics,args=(result_queue,THREADS,i,18080+i,10,target_accusations)))
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
                    try:
                        articleCount[accusation] = aResult['article'][accusation]
                    except:
                        print(aResult['wordList'].keys())
                        print(aResult['article'].keys())
                        raise Exception

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

    # ss=set()
    # for accusation in articleCount:
    #     if articleCount[accusation]>5:ss.add(accusation)
    # print(ss)
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
            json.dump({"word_list":wordListByAccusation,"word_count":wordCountByAccusation,"word_appear":change_set_to_list(wordAppearInAccusations),"article_count":articleCount},of)
    print("total spend %.2f seconds."%(time.time()-start))

def change_set_to_list(o):
    if isinstance(o,list):
        for i in range(len(o)):
            o[i]=change_set_to_list(o[i])
    elif isinstance(o,dict):
        for k in o:
            o[k]=change_set_to_list(o[k])
    elif isinstance(o,tuple):
        newlist=[]
        for i in o:
            newlist.append(change_set_to_list(i))
        return tuple(newlist)
    elif isinstance(o,set):
        newlist = []
        for i in o:
            newlist.append(change_set_to_list(i))
        return newlist
    else:
        return o


if __name__=="__main__":
    test(read=True)