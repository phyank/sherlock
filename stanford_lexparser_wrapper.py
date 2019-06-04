"""
该模块将stanford parser中的LexicalizedParser类封装成一个web微服务
特别封装该类是由于该类支持仅进行部分词类标注的输入，故能复用准确度比内置词性标注器更高的词法分析的标注结果
由于LexicalizedParser main函数中的一个逻辑问题，需要修改edu.stanford.nlp.parser.lexparser.LexicalizedParser
中的一行代码后本包装器才能正常运行，建议使用 https://github.com/phyank/CoreNLP

"""

import subprocess,os

import tornado.ioloop,tornado.web,tornado.escape
from queue import Queue
import threading,json
from time import sleep

from tornado import gen

from tools_cpython import get_local_settings

PASSWORD='rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i'

conf_dict=get_local_settings()

CORENLP_DIR=conf_dict['corenlp_dir']

CMD=['java',
                  '-mx2g',
                  '-cp','*',
                  'edu.stanford.nlp.parser.lexparser.LexicalizedParser',
                  '-model', 'edu/stanford/nlp/models/lexparser/chinesePCFG.ser.gz',
                  '-sentences', 'newline',
                  '-outputFormat', 'conll2007',
                  '-tokenized',
                  '-tagSeparator','/',
                  '-tokenizerFactory', 'edu.stanford.nlp.process.WhitespaceTokenizer',
                  '-tokenizerMethod', 'newCoreLabelTokenizerFactory',
                  '-encoding', 'utf8',
                  '-']

os.chdir(CORENLP_DIR)

def test_sub():
    p=subprocess.Popen(CMD,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    readThread = ReadThread(p.stdout)
    readThread.daemon=True
    readThread.start()
    print(readThread.is_alive())
    while True:
        i=input(">")
        print("input:%s"%(i))
        p.stdin.write(i.encode('utf8')+'\n'.encode('utf8'))
        p.stdin.flush()
        p.stdin.write('|||\n'.encode('utf8'))
        p.stdin.flush()
        while True:
                try:
                    newline=stdoutQueue.get(block=False)
                except:
                    newline=None
                if newline:
                    newline=newline.decode("utf8")
                    if "|||" in newline:
                        break
                    print(newline)
                else:
                    sleep(0.1)

class BaseHandler(tornado.web.RequestHandler):
    def write_error(self, status_code,**kwargs):
        self.finish("<html><title>%(code)d: %(message)s</title>"
                    "<body>%(code)d: %(message)s</body></html>" % {
                        "code": status_code,
                        "message": kwargs['content'] if 'content' in kwargs else '',
                    })

inQueue=Queue()
outQueue=Queue()
mainMutex=threading.Lock()

stdoutQueue=Queue()

class ReadThread(threading.Thread):
    def __init__(self,stdout):
        threading.Thread.__init__(self)
        self.stdout=stdout

    def run(self):
        print("Read thread start")
        while True:
            # print("waiting newline")
            newline = self.stdout.readline()
            # print("get newline")
            stdoutQueue.put(newline)

class PrintThread(threading.Thread):
    def __init__(self,stdout):
        threading.Thread.__init__(self)
        self.stdout=stdout

    def run(self):
        print("Read thread start")
        while True:
            # print("waiting newline")
            newline = self.stdout.readline()
            # print("get newline")
            print("PRINT :%s"%newline.decode('utf8'))

def read_from_stdout(stdout):
    print("thread start")
    while True:
        print("waiting newline")
        newline=stdout.readline()
        print("get newline")
        stdoutQueue.put(newline)

class MainStatus:
    def __init__(self):
        self.rid=0
mainStatus=MainStatus()

class StanfordThreads(threading.Thread):
    def __init__(self,inQueue,outQueue):
        threading.Thread.__init__(self)

        self.cmd=CMD
        self.subp=subprocess.Popen(self.cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.inQueue=inQueue
        self.outQueue=outQueue

        self.readThread=ReadThread(self.subp.stdout)
        self.readThread.daemon=True
        self.readThread.start()

        self.printErrorThread = PrintThread(self.subp.stderr)
        self.printErrorThread.daemon = True
        self.printErrorThread.start()
    def run(self):

        while True:
            rid,sentence=self.inQueue.get()
            print(u"Receive sentence %s"%sentence)
            #print(type(sentence))
            sentence=sentence.replace("\n","")
            self.subp.stdin.write((sentence+u'\n').encode('utf8'))
            self.subp.stdin.flush()
            self.subp.stdin.write(' |||/NR\n'.encode('utf8'))
            self.subp.stdin.flush()
            # print("start readline")
            results=[]
            while True:
                try:
                    newline = stdoutQueue.get(block=False)
                except:
                    newline = None
                if newline:
                    newline = newline.decode("utf8")
                    if "|||" in newline:
                        # print("Terminator:%s"%repr(newline))
                        _ = stdoutQueue.get()
                        break
                    # else:
                        # print("Non-terminator:%s" % repr(newline))
                    results.append(newline)
                else:
                    sleep(0.1)
            # print("end readline")
            result="\n".join(results)
            print(result)
            self.outQueue.put((rid,result))
	
class HomeHandler(BaseHandler):
    def get(self):
        self.write('It works!')


class StanfordHandler(BaseHandler):
    def get(self):
        self.write_error(403,content='403 Forbidden:\nYou should not get from this address.')
    def post(self, *args, **kwargs):
        pswd=self.get_body_argument('passwd')
        if pswd!=PASSWORD:
            self.write_error(403,content='403 Forbidden:\nAuth failed.')
            return
		
        sentence=self.get_body_argument('sentence')
        with mainMutex:
            rid=mainStatus.rid
            mainStatus.rid=rid+1
		
        inQueue.put((rid,sentence))
		
        while True:
            arid,aresult=outQueue.get()
            if arid==rid:
                 break
            else:
                outQueue.put((arid,aresult))
                continue
		
        self.write(aresult)

def make_app():
    return tornado.web.Application([(r'/',HomeHandler),
	                                 (r'/stanford',StanfordHandler)])

if __name__=="__main__":
    # test_sub()
    stanfordThreads=[]
	
    for i in range(1):
        t=StanfordThreads(inQueue,outQueue)
        t.daemon=True
        t.start()
        stanfordThreads.append(t)
	
    print("All threads started.")
		
    app=make_app()
    app.listen(conf_dict['corenlp_port'])
	
    tornado.ioloop.IOLoop.current().start()
		
		
		    

