import json
from ML_LinkClassifier import LinkClassifier

def loadDataFromInitJson():
    file = open("init.json", 'r')
    jsonData = json.loads(file.read())
    file.close()
    return(jsonData["ML_init"])


def formatData(data):
    x = []
    for i in range(0, len(data["counts"])):
        x.append([ data["counts"][i], data["positions"][i]])
    y = data["scores"]
    return((x,y))


if __name__ == "__main__":
    (x,y) = formatData(loadDataFromInitJson())
    testClassifier = LinkClassifier(["counts", "positions"], ["5", "6", "7"])

    testClassifier.learn(x,y)
    print("count: 5, position: 0.3: " + str(testClassifier.predict([5, 0.3])))
    print("count: 50, position: 0.7: " + str(testClassifier.predict([50, 0.7])))
    testClassifier.createPdf("test")
