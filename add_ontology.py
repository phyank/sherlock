# from tools import *
from  tools_pypy import *

conf_dict=get_local_settings()


wordnet={"行政区划":"地理位置","位置":"地理位置","所属地区":"地理位置","位于":"地理位置"}

nations={'布依族',
         '维吾尔族', '门巴族', '基诺族', '纳西族', '普米族', '鄂温克', '柯尔克孜族', '羌族', '俄罗斯', '水族', '高山族', '裕固族', '锡伯族', '俄罗斯族', '畲族',
         '哈萨克族', '塔吉克', '哈尼族', '白族', '维吾尔', '瑶族', '阿昌族', '土家族', '柯尔克孜', '鄂伦春', '哈萨克', '乌孜别克族', '仡佬族', '壮族', '鄂伦春族', '独龙族', '珞巴族', '乌孜别克', '景颇族', '藏族', '僳僳族', '回族', '德昂族', '蒙古族', '鄂温克族', '保安族', '塔塔尔族', '塔塔尔', '佤族', '土族', '怒族', '彝族', '苗族', '朝鲜族', '汉族', '侗族', '塔吉克族', '赫哲族', '黎族', '达斡尔', '达斡尔族', '拉祜族', '京族', '东乡族', '傣族', '撒拉族', '布朗族', '仫佬族', '毛南族', '满族'}

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
if __name__=="__main__":
   make_china_location_entities()
   #  search("广东")