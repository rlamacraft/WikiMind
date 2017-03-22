import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class SinglePage:

    def __init__(self, id, title = None, html = None):
        self.id = id
        if not title == None:
            self.title = title
        if not html == None:
            self.html = html

    # don't reparse the document, just put the leftover soup in the fridge #ChefProgrammingLanguage
    def getSoup(self):
        try:
            return(self.soup)
        except AttributeError:
            try:
                self.soup = BeautifulSoup(self.html, 'html.parser')
                return(self.soup)
            except AttributeError:
                return(None)

    def links(self):
        soup = self.getSoup()
        links = []
        for eachATag in soup.findAll('a'):
            Url = str(eachATag.get('href'))
            parsedUrl = urlparse(Url)

            if(Url == parsedUrl.path):
                splitUrl = Url.split("/")
                if(len(splitUrl) == 3 and splitUrl[1] == "wiki" and "." not in splitUrl[2]):
                    links.append((splitUrl[2], eachATag))
        return(links)

# gets data for a batch of pages
# returns an dict: id -> SinglePage
def getPages(pages):
    response = { 'continue': 'init'}
    ret = {}
    while 'continue' in response:
        params = {
            'action'    : 'query',
            'format'    : 'json',
            'prop'      : 'revisions',
            'rvprop'    : 'content',
            'rvparse'   : 1,
            'titles'    : "|".join(pages),
            'contine'   : response
        }
        if not (response['continue'] == 'init'):
            params['continue'] = response['continue']['continue']
            params['rvcontinue'] = response['continue']['rvcontinue']
        headers = {
            'User-Agent': "yet-to-be-named-project; rlamacraft.co.uk"
        }
        response = requests.get("http://en.wikipedia.org/w/api.php", params=params, headers=headers).json()
        for pageid,eachPage in response['query']['pages'].items():
            pageInfo = SinglePage(pageid, title = eachPage['title'])
            if 'revisions' in eachPage:
                pageInfo.html = eachPage['revisions'][0]['*']
            if pageid in ret:
                if hasattr(pageInfo, 'html'):
                    setattr(ret[pageid], 'html', pageInfo.html)
            else:
                ret[pageid] = pageInfo
    return(ret)
