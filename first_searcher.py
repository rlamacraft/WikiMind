import json
from ClassifierTesting.ML_LinkClassifier import LinkClassifier
from wikipedia_api import get_random_article, SingleWikipediaSearch, BatchWikipediaSearch, LinkPageContainer
from searching_lists import OpenList, ClosedList, Results, ResultDataPoint
from random import randint
from urllib import parse
import plotly.graph_objs as go
import plotly as py

def append_to_init_json(results):
    file = open('init.json', 'r')
    json_data = json.loads(file.read())
    file.close()
    json_data["ML_depthThree"] = {
        'counts'    : results.counts(),
        'positions' : results.positions(),
        'scores'    : results.rounded_scores()
    }
    file = open('init.json', 'w')
    file.write(json.dumps(json_data))
    file.close()


def load_data_from_init_json():
    file = open("init.json", 'r')
    json_data = json.loads(file.read())
    file.close()
    return(json_data["ML_depthTwo"])


def format_data(data):
    x = []
    for i in range(0, len(data["counts"])):
        x.append([ data["counts"][i], data["positions"][i]])
    y = data["scores"]
    return((x,y))


def get_random_link_from_open_list(open_list):
    """Tournament Selection, but with a bias for links with better scores to improve algorithm dervied from iteratively collected data"""
    if len(open_list) == 0:
        raise IndexError("open list is empty")
    link_selection = sorted(open_list.get_random_selection(10, random_rate = 0.31))
    if len(link_selection) == 0:
        return(None)
    else:
        return(link_selection[0])


def generate_random_start(verbose = False):
    prev = LinkPageContainer(prev=None, link_text="START")
    random_link_container = LinkPageContainer(page=get_random_article(), prev=prev, score=1)
    random_link_container.link_text = random_link_container.title
    if verbose:
        print(random_link_container.page.title)
    return(random_link_container)


# follows a few (mostly) random links from a starting link_page_container
# INPUT: the (random) page to start at, the number of links to follow
# might throw IndexError
def generate_random_goal(generated_random_start, depth, classifier, verbose = False):
    selected_link_container = generated_random_start
    for i in range(0, depth):
        open_list = OpenList()
        links = []
        for (each_link_text, each_link_tag) in selected_link_container.page.links():
            new_container = LinkPageContainer(link_text=each_link_text, prev=selected_link_container)
            new_container.process_link_for_open_list(classifier)
            links.append(new_container)
        open_list.batch_push(links)
        selected_link = get_random_link_from_open_list(open_list)
        if verbose:
            print(selected_link.link_text)
        if i < depth - 1:
            selected_link_container = SingleWikipediaSearch(LinkPageContainer(link_text=selected_link.link_text, prev=selected_link.prev, score=selected_link.prev.score)).container
    return(LinkPageContainer(link_text=selected_link.link_text, prev=selected_link_container, score=selected_link.prev.score))


def report_match(head_of_chain, generated_random_goal):
    if head_of_chain.chain_equals(generated_random_goal):
        print("Found the same chain.")
    else:
        print("Found a different chain.")
        if head_of_chain.depth() < generated_random_goal.depth():
            print("And it's shorter!")
    print("The chain: " + head_of_chain.chain_as_str())


def search(start, goal, classifier, verbose = False):
    """searches from a given start page, to a given goal page, using a link classifier"""
    random_rate = 0.3
    just_give_up = 50000
    open_list = OpenList()
    closed_list = ClosedList()
    start.process_link_for_open_list(classifier)
    open_list.push(start)

    while not open_list.is_empty() and len(open_list) < just_give_up:
        random_selection = open_list.get_random_selection_of_fixed_length(closed_list, random_rate = random_rate)
        if len(random_selection) > 0 and verbose:
            print("len(open_list) = " + str(len(open_list)))

        for each_container in BatchWikipediaSearch(random_selection, verbose = False).containers:
            if verbose:
                print(str(each_container.depth()) + ": " + str(each_container.score) + ": " + str(round(each_container.open_list_key, 2)) + ": " + each_container.page.title + " from " + each_container.prev.link_text)
            closed_list.append(each_container.title, each_container)
            open_list_additions = []
            for (each_link_text, each_link_anchor) in each_container.page.links():
                each_link_container = LinkPageContainer(link_text=each_link_text, prev=each_container)
                found_chain = each_link_container.equals(goal)
                if found_chain:
                    report_match(each_link_container, goal)
                    closed_list.remove_chain(each_link_container.prev) # this is so we don't learn the good stuff as bad
                    each_link_container.set_score(classifier)
                    return((each_link_container, closed_list))
                else:
                    each_link_container.process_link_for_open_list(classifier)
                    # print(each_link_container.score)
                    open_list_additions.append(each_link_container)
            open_list.batch_push(open_list_additions)
    if verbose and len(open_list) >= just_give_up:
        print(str(len(open_list)))
        print("I give up")
    return((None, None))


def setup_classifier():
    (features_data_set, score_data_set) = format_data(load_data_from_init_json())
    classifier = LinkClassifier(["counts", "positions"], ["3", "4", "10"])
    classifier.learn(features_data_set, score_data_set)
    return(classifier)


def search_setup(collected_data):
    """creates and runs a search, and then learning from the results"""
    num_of_searches = 1
    classifier = setup_classifier()
    cumulative_closed_list_count = 0
    cumulative_closed_list_learnt_count = 0

    i = 0
    while i < num_of_searches:
        random_start = generate_random_start()
        try:
            random_goal = generate_random_goal(random_start, 5, classifier, verbose = False)
        except IndexError:
            print("Could not find initial chain")
            continue
        else:
            i += 1
            print("Goal: \n" + random_goal.chain_as_str(new_lines=True))
            print("---------------------------")
            (succesful_chain, useless_requests) = search(random_start, random_goal, classifier, verbose = True)
            if not succesful_chain == None:
                collected_data.learn_succesful_chain(succesful_chain, verbose = True)
            if not useless_requests == None:
                collected_data.learn_selection_useless_requests(useless_requests, verbose = True)
            print("---------------------------")
    return(collected_data)


def generate_plot(collected_data, filename):
    trace1 = go.Scatter(
        x = collected_data.counts(),
        y = collected_data.positions(),
        text = collected_data.texts(),
        mode='markers',
        hoverinfo='x+y+text',
        marker=dict(
            size='5',
            color = collected_data.scores(),
            colorscale='Viridis',
            showscale=True
        )
    )
    data = [trace1]
    py.offline.plot(data, filename=filename)


if __name__ == "__main__":
    collected_data = Results()
    search_setup(collected_data)
    generate_plot(collected_data, 'firstSearchTestOutput.html')
    # append_to_init_json(collected_data)
