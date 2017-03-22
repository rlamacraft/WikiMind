from wikipediaApi import getPages
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class SingleWikipediaSearch:

    def __init__(self, name):
        results = getPages([name])
        for eachResultId, eachResult in results.items(): #there's only one result
            self.page = eachResult

    def links(self):
        return(self.page.links())
