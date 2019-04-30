from tools import *

INFILE="bkup/tagged.json"
OUTFILE="bkup/new_tagged.json"

ifile=open(INFILE,"r",encoding='gbk')
ofile=open(OUTFILE,"w",encoding='utf8')

ofile.write(ifile.read())

