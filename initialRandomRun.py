import json
from Search import RandomSearch

file = open("init.json", 'r')
text = file.read()
data = json.loads(text)["data"]

searcher = RandomSearch()
# for eachSearch in data:
    # searcher.search(eachSearch["start"], eachSearch["end"])

singleData = data[3]
print(searcher.search(singleData["start"], singleData["end"]))

file.close()
