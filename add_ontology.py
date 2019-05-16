"""
本体导入、融合模块，从已有图谱导入结构化知识
"""

# from tools import *
from py2neo import Graph
from py2neo.cypher import cypher_repr
from  tools_general import *

conf_dict=get_local_settings()


wordnet={"行政区划":"地理位置","位置":"地理位置","所属地区":"地理位置","位于":"地理位置"}

nations={'基诺', '门巴族', '布朗', '毛南', '珞巴', '土家', '普米', '裕固族', '僳僳','傈僳', '维吾尔', '景颇', '哈萨克', '独龙族', '塔塔尔族', '僳僳族', '傈僳族', '回族', '蒙古族', '鄂温克族', '塔塔尔', '怒族', '彝族', '苗族', '达斡尔族', '拉祜', '布朗族', '毛南族', '阿昌', '独龙', '仡佬', '德昂', '俄罗斯', '水族', '高山族', '高山', '畲族', '哈萨克族', '阿昌族', '土家族', '蒙古', '东乡', '乌孜别克', '藏族', '佤族', '土族', '达斡尔', '侗族', '塔吉克族', '朝鲜', '赫哲族', '黎族', '撒拉', '撒拉族', '仫佬族', '布依', '鄂温克', '赫哲', '羌族', '仫佬', '柯尔克孜', '鄂伦春', '乌孜别克族', '鄂伦春族', '珞巴族', '景颇族', '保安族', '朝鲜族', '汉族', '京族', '东乡族', '傣族', '裕固', '哈尼', '满族', '布依族', '维吾尔族', '基诺族', '纳西族', '普米族', '纳西', '柯尔克孜族', '保安', '锡伯族', '俄罗斯族', '塔吉克', '锡伯', '门巴', '哈尼族', '白族', '瑶族', '仡佬族', '壮族', '德昂族', '拉祜族'}

provinceEnd={'省',"自治区","市"}
cityEnd={"自治州","市","地区"}

areaEnd={"(?!发)区","市","自治县","县"}

def search_baiketriples(word="广东省"):
    g = line_generator(conf_dict['ontology_dumpfile'], encoding='utf8')
    for line in g:
        a,r,b=line.split("\t")
        if a ==word :print("found")

def search_dumps(word):
    n=0
    g = line_generator("dump_locations.json", encoding='utf8')
    for line in g:
        if word in line:n+=1
    print(n)

def dump_ontology_locations():
    g=line_generator(conf_dict['ontology_dumpfile'],encoding='utf8')

    # extractor=re.compile("^[^a-zA-Z0-9\[\]=·“”""].+([省]|自治区|市)$|^[^a-zA-Z0-9\[\]=·“”""].+(?<!([小城辖社特禁游地街墅园发情0-9雷人专校赛景展务渔战]))[区]$|^[^a-zA-Z0-9\[\]=·“”""].+[县]$|^[^a-zA-Z0-9\[\]=·“”""].+(?<!([城老故]))[乡]$|^[^a-zA-Z0-9\[\]=·“”""].+(?<!([小城]))[镇]$")
    #extractor=re.compile("^[^a-zA-Z0-9\[\]=·“”""].+([省]|自治区)$")

    of=open("dump_locations.json","w",encoding='utf8')

    original_entities,targets=make_china_location_entities()

    final_entities={}

    entity={}

    i=0
    lastA=None
    for line in g:
        a,r,b=line.split("\t")
        if lastA and lastA!=a:
            i+=1
            # if i >1000:break
            # OUTPUT
            original_entities[targets[lastA]].update(entity)
            if "洪山" in targets[lastA]:
                print("Dumped")
                print(original_entities[targets[lastA]])
            json.dump(original_entities[targets[lastA]],of,ensure_ascii=False)
            of.write("\n")
            final_entities[targets[lastA]]=original_entities[targets[lastA]]
            entity={}
            lastA=None
        if a in targets:
            lastA=a
        if lastA:
            if entity is not None:
                if "name" not in entity:
                    entity["name"]=a
                try:
                    entity[r].append(b)
                except KeyError:
                    entity[r]=[b]
    for t in targets:
        if t not in final_entities and targets[t] not in final_entities:
            final_entities[targets[t]]=original_entities[targets[t]]
            if "洪山" in targets[t]:print("Dumped")
            json.dump(original_entities[targets[t]], of, ensure_ascii=False)
            of.write("\n")
    # print(final_entities)

def make_neo4j_key(value):
    if value[0] in '1234567890':
        value="_"+value
    for c in "、，。?：/\\；”“{}[](),.?;:（）【】！@#￥%……&*!@#$%^&*":
        if c in value:value=value.replace(c,"")
    value=value.replace(" ","").replace("\u200b","")
    return value

def make_china_location_entities():
    entityDict={}
    g = line_generator("Locations.json", encoding='utf8')
    for line in g:
        line=json.loads(line)
        if line:
            entityDict[line['name']]=line

    final={}

    codeDict={}

    provGen=line_generator("Administrative-divisions-of-China/dist/provinces.csv", encoding='utf8')

    cityGen = line_generator("Administrative-divisions-of-China/dist/cities.csv", encoding='utf8')

    areaGen = line_generator("Administrative-divisions-of-China/dist/areas.csv", encoding='utf8')

    codeDict["provinceCode"]={}

    entities={}
    targets={}

    labels = provGen.__next__().split(",")
    # ii=0
    for record in provGen:
        # ii+=1
        # print(record)
        this={"type":"ProvinceName"}
        for i,value in enumerate(record.split(",")):
            this[labels[i]]=value.replace('"',"")


        short=this['name']
        for end in provinceEnd:
            if re.search("%s$"%end,short):
                short=short.replace(end,"")
        if not short: short = this['name']


        while True:
            hit = False
            for nation in nations:
                # print(re.search("%s$"%nation,short),"%s$"%nation,short)
                if re.search("%s$"%nation,short) and short!="内蒙古":
                    hit=True
                    short=short.replace(nation,"")
            if hit:continue
            else:break

        this['short']=short

        targets[this['short']]=this['name']
        targets[this['name']] = this['name']
        # print(this)
        entities[this['name']] = this
    # print(len(entities))
    # print(ii)
    labels = cityGen.__next__().split(",")
    for record in cityGen:
        # print("City",record)
        this={"type":"CityName"}
        for i,value in enumerate(record.split(",")):
            this[labels[i]]=value.replace('"',"")


        short=this['name']
        for end in cityEnd:
            if re.search("%s$"%end,short):
                # print("True")
                short=short.replace(end,"")
        if not short: short = this['name']


        while True:
            hit = False
            for nation in nations:
                # print(re.search("%s$"%nation,short),"%s$"%nation,short)
                if re.search("%s$"%nation,short):
                    hit=True
                    # print(short)
                    short=short.replace(nation,"")
                    # print(short)
            if hit:continue
            else:break

        this['short']=short
        # print(this)
        targets[this['short']]=this['name']
        targets[this['name']] = this['name']

        entities[this['name']] = this

    labels = areaGen.__next__().split(",")
    for record in areaGen:
        # print("City",record)
        this = {"type": "AreaName"}
        for i, value in enumerate(record.split(",")):
            this[labels[i]] = value.replace('"', "")

        short = this['name']
        for end in areaEnd:
            if re.search("%s$" % end, short):
                # print("True")
                short = short.replace(end, "")
        if not short:short=this['name']

        while True:
            hit = False
            for nation in nations:
                # print(re.search("%s$"%nation,short),"%s$"%nation,short)
                if re.search("%s$" % nation, short):
                    hit = True
                    # print(short)
                    short = short.replace(nation, "")
                    # print(short)
            if hit:
                continue
            else:
                break

        this['short'] = short
        # print(this)
        targets[this['short']] = this['name']
        targets[this['name']] = this['name']

        entities[this['name']] = this

    # labels = cityGen.__next__().split(",")
    # for record in cityGen:
    #     this = {"type": "ProvinceName"}
    #     for i, value in enumerate(record.split(",")):
    #         this[labels[i]] = value
    #     targets[this['name']] = this

    return entities,targets

def load_locations_to_kg():
    graph = Graph(uri=conf_dict['neo4j_address'], auth=(conf_dict['neo4j_user'], conf_dict['neo4j_pass']))

    for label in ("Location", "ProvinceName", "CityName", "AreaName"):
        graph.run("CREATE INDEX ON :%s(name)" % label)

    areaCode, provinceCode, cityCode = {}, {}, {}
    pendingToLink=[]
    with open("dump_locations.json","r") as dumpFile:

        while True:
            newLine=dumpFile.readline()
            if not newLine:break
            # if "洪山" in newLine :print("read")
            entity=json.loads(newLine)
            # print(entity['type'])
            if entity['type']=="ProvinceName":
                provinceCode[entity['code']]=entity['name']
            elif entity['type']=="CityName":
                cityCode[entity['code']]=entity['name']
            elif entity['type']=="AreaName":
                areaCode[entity['code']]=entity['name']

            this={}

            this['type']=entity['type']
            this['name']=entity['name']
            if "areaCode" in entity:this["areaCode"]=entity['areaCode']
            if "cityCode" in entity: this["cityCode"] = entity['cityCode']
            if "provinceCode" in entity: this["provinceCode"] = entity['provinceCode']

            pendingToLink.append(this)
            # if "洪山" in this['name']:print("graph")
            try:
                graph.run("MERGE (:Location:%s{_subgraph:'baike',%s});"%(entity['type'],",".join(map(lambda k:"%s:%s"%(make_neo4j_key(k),cypher_repr(";".join(entity[k]) if isinstance(entity[k],list) else entity[k])),(k for k in entity if k!="type")))))
            except Exception as e:
                print(repr("MERGE (:Location:%s{_subgraph:'baike',%s});"%(entity['type'],",".join(map(lambda k:"%s:%s"%(make_neo4j_key(k),cypher_repr(";".join(entity[k]) if isinstance(entity[k],list) else entity[k])),(k for k in entity if k!="type"))))))
                exit(-1)
    for this in pendingToLink:
        if "areaCode" in this:
            try:
                areaName=areaCode[this['areaCode']]
            except KeyError:
                pass
            else:
                graph.run("MATCH (a:Location),(b:AreaName) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:位于]->(b)"%(this['name'],areaName))
        elif "cityCode" in this:
            try:
                cityName=cityCode[this['cityCode']]
            except KeyError:
                pass
            else:
                graph.run("MATCH (a:Location),(b:CityName) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:位于]->(b)"%(this['name'],cityName))
        elif "provinceCode" in this:
            try:
                provinceName = provinceCode[this['provinceCode']]
            except KeyError:
                pass
            else:
                graph.run("MATCH (a:Location),(b:ProvinceName) WHERE a.name='%s' AND b.name='%s' MERGE (a)-[:位于]->(b)" % (this['name'], provinceName))
if __name__=="__main__":
   # print(make_china_location_entities()[1])
   dump_ontology_locations()
   # search_baiketriples("西藏自治区")
   load_locations_to_kg()
   # search_dumps("ProvinceName")