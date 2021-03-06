import heapq # see https://docs.python.org/3/library/heapq.html
from math import floor, log
import random
from wikipedia_api import LinkPageContainer
from collections import defaultdict

class OpenList():
    """list of pages to be searched"""

    def __init__(self):
        self.heap = []
        self.map = {}

    # INPUT: LinkPageContainer
    def push(self, node):
        if node.link_text in self.map:
            existing_node = self.map[node.link_text]
            existing_node.update_open_list_key_to_merge_duplicate(node)
            self._heapify() # after changing the open list key we must re-heapify
        else:
            heapq.heappush(self.heap, node)
            self.map[node.link_text] = node

    # INPUT: List of LinkPageContainer
    def batch_push(self, nodes):
        must_heapify = False
        for node in nodes:
            if node.link_text in self.map:
                existing_node = self.map[node.link_text]
                existing_node.update_open_list_key_to_merge_duplicate(node)
                must_heapify = True
            else:
                heapq.heappush(self.heap, node)
                self.map[node.link_text] = node
        if must_heapify:
            self._heapify() # after changing the score we must re-heapify

    def pop(self):
        value = heapq.heappop(self.heap)
        return(value)

    def __str__(self):
        return(str(self.heap))

    def __len__(self):
        return(len(self.heap))

    def _empty(self):
        self.heap = []

    def _heapify(self):
        heapq.heapify(self.heap)

    def _get_random(self):
        random_index = random.randint(0, len(self) - 1)
        item = self.heap.pop(random_index)
        self._heapify() # after removing random elements we must fix the heap structure
        return(item)

    def get_random_selection(self, selection_count, random_rate = 0):
        num_of_random_links = floor(selection_count * random_rate)
        num_of_best_links = selection_count - num_of_random_links
        links = []
        for i in range(0, num_of_best_links):
            try:
                links.append(self.pop())
            except IndexError:
                break
        if len(self.heap) <= num_of_random_links:
            links.extend(self.heap)
            num_of_random_links = 0
            self._empty()
        for i in range(0, num_of_random_links):
            if len(self) <= 1:
                try:
                    links.append(self.pop())
                except IndexError:
                    break
            else:
                links.append(self._get_random())
        return(links)

    def is_empty(self):
        return(len(self) == 0)

    def get_random_selection_of_fixed_length(self, closed_list, count = 10, random_rate = 0):
        random_selection = []
        selection = [ "foo" ]
        while len(random_selection) < count and len(selection) > 0:
            #always return array of length count, if possible, to maximise return on each network call
            selection = self.get_random_selection(count - len(random_selection), random_rate = random_rate)
            random_selection.extend(selection)
        return(random_selection)

class ClosedList():
    """map of article title to data in order to avoid repeatedly getting page and learning"""

    def __init__(self):
        self._map = {}

    def __len__(self):
        return(len(self._map))

    def __getitem__(self, key):
        return(self._map[key])

    def pop(self, key):
        value = self[key]
        del(self._map[key])
        return(value)

    def pop_random(self):
        return(self.pop(random.choice(list(self.keys()))))

    def append(self, name, container):
        self._map[name] = container

    def keys(self):
        return(self._map.keys())

    def contains(self, name):
        return(name in self._map)

    def remove_chain(self, container):
        a = container
        while not a == None:
            try:
                del(self._map[a.link_text])
            except KeyError:
                break
                # do nothing, it just means the link has already been removed
            a = a.prev
        return()

class ResultDataPoint():

    def __init__(self, container, score):
        self.count = container.calculate_feature__count()
        self.position = container.calculate_feature__position()
        self.score = score
        self.text = container.prev.page.title + " -> " + container.link_text + ": " + str(self.score)

class Results():

    def __init__(self):
        self.data = []

    def __len__(self):
        return(len(self.data))

    def _useless_requests_learn_count(self, useless_requests):
        if len(useless_requests) > 0:
            return( round( log( len(useless_requests), 10 ) ** 4 ) )
        return(0)

    def _calculate_succesful_score(self, container, chain_depth):
        """Combines score and chain depth to produce a learning score,
        with the output bounded by 0 and LinkPageContainer.MAX_CLASS as the input score
        is to prevent predictions wandering out of this window with each iteration of the learning process
        """
        if chain_depth <= 0 or chain_depth > LinkPageContainer.CHAIN_MAX_DEPTH:
            raise ValueError("0 < chain_depth <= LinkPageContainer.CHAIN_MAX_DEPTH")
        if container.score <= 0 or container.score > LinkPageContainer.MAX_CLASS:
            raise ValueError("0 < container.score <= LinkPageContainer.MAX_CLASS")
        chain_depth_scalar = (LinkPageContainer.MAX_CLASS / 2) / LinkPageContainer.CHAIN_MAX_DEPTH
        offset = chain_depth_scalar * chain_depth
        scale = container.score / 2
        return(floor(scale + offset))

    def learn_succesful_chain(self, container, verbose = False):
        loop = container
        chain_depth = container.depth() + 1
        while not loop.prev.prev == None:
            learning_score = self._calculate_succesful_score(loop, chain_depth)
            self.data.append(ResultDataPoint(loop, learning_score))
            if verbose:
                print("learnt: " + loop.link_text + " from the successful chain.")
            loop = loop.prev

    def learn_selection_useless_requests(self, useless_requests, verbose = False):
        count = self._useless_requests_learn_count(useless_requests)
        learnt_count = 0
        while learnt_count < count:
            try:
                random_container = useless_requests.pop_random()
                self.data.append(ResultDataPoint(random_container, LinkPageContainer.MAX_CLASS))
                if verbose:
                    print("learnt: " + random_container.link_text + " from the useless requests.")
                learnt_count += 1
            except IndexError:
                return()

    def data_for_learning(self):
        return({
            "features"  : [ [ x.count, x.position ] for x in self.data ],
            "scores"    : [ x.score for x in self.data ]
        })

    def scores(self):
        return([ x.score for x in self.data ])

    def rounded_scores(self):
        return([ round(x.score) for x in self.data ])

    def counts(self):
        return([ x.count for x in self.data ])

    def positions(self):
        return([ x.position for x in self.data ])

    def texts(self):
        return([ x.text for x in self.data ])
