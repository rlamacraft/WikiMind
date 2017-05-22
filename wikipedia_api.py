import requests
from bs4 import BeautifulSoup
from urllib import parse
from urllib.parse import urlparse
import re
import math
from enum import Enum


class LinkPageContainer:
    """Wrapper container for a link, its parsed page, and associated data. Acts as a single node in a chain of links."""

    MAX_CLASS = 100
    DUPLICATE_SUBTRACTING_FACTOR = 0.05
    CHAIN_MAX_DEPTH = 20

    def __init__(self, link_text = None, page = None, prev = None, score= None):
        if not link_text == None:
            self.link_text = link_text.replace("_", " ")
        else:
            self.link_text = None
        self.set_page(page)
        self.prev = prev
        self.score = score

    def set_page(self, page):
        self.page = page
        if not page == None:
            self.title = page.title.replace("_", " ")
        else:
            self.title = None

    def __lt__(self, other):
        """comparator, so that containers can be used as nodes of a heap, which is the implementation of the open list"""
        return(self.open_list_key < other.open_list_key)

    def chain_equals(self, other_container):
        """Checks if the chain, starting at self and ending at a None node, is equal to another passed chain"""
        if not self.depth() == other_container.depth():
            return(False)
        a = self
        b = other_container
        while not a == None and not b == None:
            if not a.link_text == b.link_text:
                return(False)
            a = a.prev
            b = b.prev
        return(True)

    def equals(self, other_container):
        """Checks if the node, self, contains identical link text to a passed node and is, as such, equal."""
        if other_container == None:
            return(False)
        elif self.link_text == other_container.link_text:
            return(True)
        return(False)

    def depth(self):
        """Calculates the depth of the node, self: which is the number of parent nodes between itself and the root."""
        count = -1
        a = self
        while not a == None:
            count += 1
            a = a.prev
        return(count)

    def _classify_link(self, classifier):
        """Classify the current link, based on the data collected, using the machine-learning classifier"""
        if self.prev == None or self.link_text == None or self.prev.page == None:
            return(LinkPageContainer.MAX_CLASS)
        position = self.calculate_feature__position()
        count = self.calculate_feature__count()
        return(classifier.predict([count, position]))

    def calculate_feature__position(self):
        return(self.prev.page.first_position_of_link_text(self.link_text))

    def calculate_feature__count(self):
        return(self.prev.page.num_of_occurance_of_link_text(self.link_text))

    def process_link_for_open_list(self, classifier):
        link_class = self._classify_link(classifier)
        self.open_list_key = link_class
        self.score = link_class

    def set_score(self, classifier):
        self.score = self._classify_link(classifier)

    def update_open_list_key_to_merge_duplicate(self, duplicate):
        average_key_value = min( self.open_list_key, duplicate.open_list_key )
        self.open_list_key = max( average_key_value - LinkPageContainer.DUPLICATE_SUBTRACTING_FACTOR, 0.0 )

    def chain_as_str(self, new_lines=False):
        """Prints the current node, with all of its ancestors, that form the chain"""
        buffer = ""
        if not self.title == None:
            buffer += self.title
        else:
            buffer += self.link_text
        node = self.prev
        indent = self.depth() - 1
        while not node.prev == None:
            if new_lines:
                buffer = "\n" + (" " * indent) + buffer
            buffer = node.title + " -> " + buffer
            node = node.prev
            indent -= 1
        return(buffer)


class SingleWikipediaSearch:

    def __init__(self, link_page_container):
        self.container = link_page_container
        results = get_pages([link_page_container.link_text])
        for each_result_id, each_result in results.items(): #there's only one result
            self.container.set_page(each_result)

    def links(self):
        return(self.page.links())


class BatchWikipediaSearch:

    def __init__(self, link_page_containers, verbose = False):
        self.containers = link_page_containers
        container_maps = {x.link_text:x for x in link_page_containers}
        for (each_page_id, each_page) in get_pages(container_maps, verbose = verbose).items():
            container_maps[each_page.title].set_page(each_page)

    def get_page_by_title(self, title):
        for each_page_id, each_page in self.pages.items():
            if title == each_page.title:
                return(each_page)
        return(None)


class SinglePage:

    _LINK_PATTERN = re.compile(".*/wiki/(.*)")

    def __init__(self, id, title = None, html = None):
        self.id = id
        if not title == None:
            self.title = title.replace("_", " ")
        if not html == None:
            self.html = html

    def _get_soup(self):
        return(BeautifulSoup(self.html, 'html.parser'))

    def links(self):
        """gets all of the links of the page, outputted as a tuple: (String, BeautifulSoup's A Tag)"""
        soup = self._get_soup()
        links = []
        for each_a_tag in soup.find_all('a'):
            Url = str(each_a_tag.get('href'))
            parsed_url = urlparse(Url)

            if Url == parsed_url.path and "." not in Url and ":" not in Url:
                regex_match = SinglePage._LINK_PATTERN.match(Url)
                if regex_match:
                    encoded_link_text = regex_match.group(1)
                    decoded_link_text = parse.unquote(encoded_link_text)
                    links.append((decoded_link_text, each_a_tag))
        return(links)

    def first_position_of_link_text(self, text):
        """finds the first occurance of the given text in the HTML of the page, as a percentage of the whole document"""
        try:
            position_in_html = self.html.find(text)
        except AttributeError:
            try:
                print("could not get html for: " + self.title)
            except AttributeError:
                print("could not get html for: " + self.id)
            return(0)
        if(position_in_html >= 0):
            distance_down_page = position_in_html / len(self.html)
            return(math.ceil(distance_down_page * 10000) / 10000)
        return(0)

    def num_of_occurance_of_link_text(self, text):
        try:
            return(self.html.count(text))
        except AttributeError:
            return(0)

def fetch_data(params, continue_break = 100):
    """performs a request to the wikipedia API"""
    response = { 'continue': 'init' }
    ret = {}
    continue_count = 0
    while 'continue' in response and continue_count < continue_break:
        if not (response['continue'] == 'init'):
            for each_continue_key,each_continue_value in response['continue'].items():
                params[each_continue_key] = each_continue_value
        headers = {
            'User-Agent': "WikiMind; rlamacraft.co.uk"
        }
        response = requests.get("http://en.wikipedia.org/w/api.php", params=params, headers=headers).json()
        for pageid,each_page in response['query']['pages'].items():
            page_info = SinglePage(pageid, title = each_page['title'])
            if 'revisions' in each_page:
                page_info.html = each_page['revisions'][0]['*']
            if pageid in ret:
                if hasattr(page_info, 'html'):
                    setattr(ret[pageid], 'html', page_info.html)
            else:
                ret[pageid] = page_info
        continue_count += 1
    return(ret)

def get_pages(pages, verbose = False):
    """gets data for a batch of pages
    returns a dict: id -> SinglePage
    """
    if verbose:
        print(pages)
        print("request = " + "|".join(pages))
    if pages == []:
        return({})
    return(fetch_data({
        'action'    : 'query',
        'format'    : 'json',
        'prop'      : 'revisions',
        'rvprop'    : 'content',
        'rvparse'   : 1,
        'titles'    : "|".join(pages)
    }))

def get_random_article():
    """gets a random Wikipedia article. Output: SinglePage"""
    random_article = fetch_data({
        'action'    : 'query',
        'format'    : 'json',
        'prop'      : 'revisions',
        'rvprop'    : 'content',
        'rvparse'   : 1,
        'generator' : 'random',
        'grnnamespace' : 0
    }, continue_break = 1)
    for pageid,page in random_article.items():
        return(page)
