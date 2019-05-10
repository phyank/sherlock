from kg import *

with open("critical", "r", encoding="utf8") as pfile:
    lines = pfile.readlines()

regExractor = RegExtractor(patterns=lines)

print(regExractor.findall("戒具有未影响审判哺乳期已满"))