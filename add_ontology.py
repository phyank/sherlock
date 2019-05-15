# from tools import *
from py2neo import Graph
from  tools_pypy import *

conf_dict=get_local_settings()


wordnet={"行政区划":"地理位置","位置":"地理位置","所属地区":"地理位置","位于":"地理位置"}

nations={'基诺', '门巴族', '布朗', '毛南', '珞巴', '土家', '普米', '裕固族', '僳僳','傈僳', '维吾尔', '景颇', '哈萨克', '独龙族', '塔塔尔族', '僳僳族', '傈僳族', '回族', '蒙古族', '鄂温克族', '塔塔尔', '怒族', '彝族', '苗族', '达斡尔族', '拉祜', '布朗族', '毛南族', '阿昌', '独龙', '仡佬', '德昂', '俄罗斯', '水族', '高山族', '高山', '畲族', '哈萨克族', '阿昌族', '土家族', '蒙古', '东乡', '乌孜别克', '藏族', '佤族', '土族', '达斡尔', '侗族', '塔吉克族', '朝鲜', '赫哲族', '黎族', '撒拉', '撒拉族', '仫佬族', '布依', '鄂温克', '赫哲', '羌族', '仫佬', '柯尔克孜', '鄂伦春', '乌孜别克族', '鄂伦春族', '珞巴族', '景颇族', '保安族', '朝鲜族', '汉族', '京族', '东乡族', '傣族', '裕固', '哈尼', '满族', '布依族', '维吾尔族', '基诺族', '纳西族', '普米族', '纳西', '柯尔克孜族', '保安', '锡伯族', '俄罗斯族', '塔吉克', '锡伯', '门巴', '哈尼族', '白族', '瑶族', '仡佬族', '壮族', '德昂族', '拉祜族'}

provinceEnd={'省',"自治区","市"}
cityEnd={"自治州","市","地区"}

areaEnd={"(?!发)区"}

def search(word="广东省"):
    g = line_generator(conf_dict['ontology_dumpfile'], encoding='utf8')
    for line in g:
        a,r,b=line.split("\t")
        if a ==word :print("found")

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

    print(final_entities)
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

    areaGen = line_generator("Administrative-divisions-of-China/dist/provinces.csv", encoding='utf8')

    codeDict["provinceCode"]={}

    entities={}
    targets={}

    labels = provGen.__next__().split(",")
    for record in provGen:
        this={"type":"ProvinceName"}
        for i,value in enumerate(record.split(",")):
            this[labels[i]]=value.replace('"',"")


        short=this['name']
        for end in provinceEnd:
            if re.search("%s$"%end,short):
                short=short.replace(end,"")


        while True:
            hit = False
            for nation in nations:
                # print(re.search("%s$"%nation,short),"%s$"%nation,short)
                if re.search("%s$"%nation,short):
                    hit=True
                    short=short.replace(nation,"")
            if hit:continue
            else:break

        this['short']=short

        targets[this['short']]=this['name']
        targets[this['name']] = this['name']
        # print(this)
        entities[this['name']] = this

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
        for end in cityEnd:
            if re.search("%s$" % end, short):
                # print("True")
                short = short.replace(end, "")

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

    areaCode, provinceCode, cityCode = {}, {}, {}
    pendingToLink=[]
    with open("dump_locations.json","r") as dumpFile:

        while True:
            newLine=dumpFile.readline()
            if not newLine:break

            entity=json.loads(newLine)
            if entity['type']=="ProvinceName":
                provinceCode[entity['code']]=entity['name']
            elif entity['type']=="CityName":
                cityCode[entity['code']]=entity['name']
            elif entity['type']=="AreaName":
                areaCode[entity['code']]=entity['name']

            this={}

            this['type']=entity['type']
            if "areaCode" in entity:this["areaCode"]=entity['areaCode']
            if "cityCode" in entity: this["cityCode"] = entity['cityCode']
            if "provinceCode" in entity: this["provinceCode"] = entity['provinceCode']

            pendingToLink.append(this)

            graph.run("MERGE (:Location:%s{name:'%s'});"%(entity['type'],entity['name']))

if __name__=="__main__":
   # make_china_location_entities()
    dump_ontology_locations()
   #  search("广东")