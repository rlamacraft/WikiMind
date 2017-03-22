import random
from wikipedia import SingleWikipediaSearch
import time

def compose(thisLink, thisNode):
    ret = thisLink
    while not thisNode.prev == None:
        ret += " <- " + thisNode.name
        thisNode = thisNode.prev
    return(ret)

class ListNode:

    def __init__(self, _name, prev):
        self.name = _name
        self.prev = prev


class RandomSearch():

    def search(self, begin, end):
        openList = []
        openList.append(ListNode(begin, ListNode("", None)))
        closedList = []

        while len(openList) > 0:
            print("----------------------------")
            rand = random.randint(0, len(openList) - 1)
            thisNode = openList.pop(rand)
            print("searching " + thisNode.name)
            print("from " + thisNode.prev.name)
            wiki = SingleWikipediaSearch(thisNode.name)
            print("num of links: " + str(len(wiki.links())))
            for (eachLink,_) in wiki.links():
                if eachLink == end:
                    print("found it!")
                    return(compose(eachLink, thisNode))
                else:
                    openList.append(ListNode(eachLink, thisNode))
            closedList.append(thisNode)
            print("size of open list: " + str(len(openList)))
            time.sleep(5)

        return("count not find it")
