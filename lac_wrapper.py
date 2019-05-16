#encoding:utf8

"""
该模块将lac中的lac_demo示例程序封装成一个web微服务
请确保本模块的运行环境能正常执行lac_demo，windows主机建议在docker环境下运行，
相关编译指引请参照官方文档： https://github.com/baidu/lac#%E8%BF%90%E8%A1%8CLAC

该文件为Python2.7环境编写
"""

import subprocess,sys

import tornado.ioloop,tornado.web,tornado.escape
from queue import Queue
import threading,json
from tornado import gen

PASSWORD='rq2j3fja9phwdfn2l3famsdoi1234t2143ghdsnwsqety56i'

LAC_DEMO_LOCATION='./lac_demo'
LAC_CONF_LOCATION='/paddle/lac/conf'
MAX_TOKENS='1000000'
THREADS='2'

if len(sys.argv)==1:
    PORT=18080
else:
    PORT=int(sys.argv[1])

def test_sub():
    p=subprocess.Popen([LAC_DEMO_LOCATION,LAC_CONF_LOCATION,MAX_TOKENS,THREADS],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    while True:
        i=raw_input(">")
        print(u"input:%s"%(i.decode('utf8')))
        p.stdin.write(i+'\n')
        p.stdin.flush()
        print(p.stdout.readline())


def my_unicode(sob,encoding='utf8'):
    if isinstance(sob,str):
        return sob.decode(encoding=encoding)
    elif isinstance(sob,unicode):
        return sob
    else:
        return str(sob)

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

class MainStatus:
    def __init__(self):
        self.rid=0
mainStatus=MainStatus()

class LacThread(threading.Thread):
    def __init__(self,inQueue,outQueue):
        threading.Thread.__init__(self)
        self.subp=subprocess.Popen(['./lac_demo','/paddle/lac/conf','100000','1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.inQueue=inQueue
        self.outQueue=outQueue
    def run(self):
        while True:
            rid,sentence=self.inQueue.get()
            # print(u"Receive sentence %s"%my_unicode(sentence))
            #print(type(sentence))
            sentence=sentence.replace("\n","")
            self.subp.stdin.write((sentence+u'\n').encode('utf8'))
            self.subp.stdin.flush()
            print("start readline")
            result=self.subp.stdout.readline()
            print("end readline")
            # print(result)
            self.outQueue.put((rid,result))
	
class HomeHandler(BaseHandler):
    def get(self):
        self.write('It works!')


class LacHandler(BaseHandler):
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
	                                 (r'/lac',LacHandler)])

if __name__=="__main__":
 #   test_sub()
    lacThreads=[]
	
    for i in range(6):
        t=LacThread(inQueue,outQueue)
        t.daemon=True
        t.start()
        lacThreads.append(t)
	
    print("All threads started.")
		
    app=make_app()
    app.listen(PORT)
	
    tornado.ioloop.IOLoop.current().start()
		
		
		    

