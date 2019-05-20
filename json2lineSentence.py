from tools_general  import *

cuts=["cut/cut0.json","cut/cut1.json","cut/cut2.json","cut/cut3.json","cut/cut4.json","cut/cut5.json"]

sentences=word2vec_sentence_generator(cuts)

with open("cut/lineSentence.txt","w",encoding='utf8') as of:
    for sentence in sentences:
        of.write(" ".join(sentence)+"\n")