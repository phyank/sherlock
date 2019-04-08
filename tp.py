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