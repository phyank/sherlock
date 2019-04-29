import json,os
from tools import *

if os.name=='nt':
    copy_command="copy"
else:
    copy_command='cp'

# if not os.path.exists('tagged.json.bkup'):
#     print(os.popen('%s tagged.json tagged.json.bkup'%copy_command).read())

g=line_generator('bkup/tagged.json')

of=open("tagged.json","w",encoding='utf8')

for line in g:
    article=json.loads(line)
    sentences=article['sentences']

    new_standard_sentences=[]
    for sentence in sentences:
        index,parse,enhancedPlusPlusDependencies=sentence['index'],"NOT_IMPLEMENTED",sentence["enhancedPlusPlusDependencies"]
        dep=sentence["enhancedPlusPlusDependencies"]
        # sentenceStr=" ".join(map(lambda x:x[1]
        #                                 ,sorted([(k['index']
        #                                 ,k['word']+("/"+lac2penn[k['lac_pos']]) if lac2penn[k['lac_pos']] else "") for k in dep if k!=0])))
   
        tagged=sorted([{"index":w['index'],"word":w['word'],"type":w['lac_pos'],"start":w['characterOffsetBegin'],"length":w['characterOffsetEnd']-w['characterOffsetBegin']+1} for w in dep],key=lambda x:x['index'])
        tokenDict=call_stanford(tagged)

        for k in tokenDict:
            assert isinstance(k,int)
            break
        standard_sentence=new_sentence_repr(index=sentence['index'],tokenDict=tokenDict,manual_relations=sentence['manual_relations'])
        new_standard_sentences.append(standard_sentence)

    newArticle={}

    newArticle['fact']=article['fact']
    newArticle['meta']=article['meta']
    newArticle['sentences']=new_standard_sentences

    of.write(json.dumps(newArticle,ensure_ascii=False)+"\n")