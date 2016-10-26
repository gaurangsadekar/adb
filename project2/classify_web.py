from __future__ import print_function
from classify_utils import *
import os
import sys
import pickle

'''
for every query probe in the category,
hit bing and get the num_matches and top4 results for each probe
add the num_matches to coverage of the category
and make a dict of query to matched URLs for the probes
'''
def get_bing_results_for_hierarchy(tree, category_name, account_key, host_url):
    print("Getting Bing Results for Category:", category_name)
    probe_to_sample = {}
    for query in tree[category_name][PROBES]:
        num_matches, search_urls = bing_web_search(account_key, host_url, query)
        print("Query String:", query, "No. of matches:", num_matches)
        tree[category_name][COVERAGE] += num_matches
        probe_to_sample[query] = search_urls
    # changing the type of the probes
    tree[category_name][PROBES] = probe_to_sample

    for sub_category_name in tree[category_name][SUB_CATEGORIES]:
        get_bing_results_for_hierarchy(tree, sub_category_name, account_key, host_url)

def classify(category_name, tree, t_es, t_ec):
    result = []
    if tree[category_name][IS_LEAF]:
        result.append(category_name)
    else:
        total_child_coverage = 0
        for sub_category_name in tree[category_name][SUB_CATEGORIES]:
            total_child_coverage += tree[sub_category_name][COVERAGE]

        parent_spec = tree[category_name][SPECIFICITY]
        for sub_category_name in tree[category_name][SUB_CATEGORIES]:
            print("Category:", sub_category_name)
            cov = tree[sub_category_name][COVERAGE]
            spec = parent_spec * cov / total_child_coverage
            tree[sub_category_name][SPECIFICITY] = spec
            print("Coverage:", cov)
            print("Specificity:", spec)
            if spec >= t_es and cov >= t_ec:
                result.extend(classify(sub_category_name, tree, t_es, t_ec))
        if not result:
            result.append(category_name)
    return result

def main():
    account_key = sys.argv[1]
    t_es = float(sys.argv[2])
    t_ec = int(sys.argv[3])
    host_url = sys.argv[4]
    cached = True if len(sys.argv) == 6 and sys.argv[5] == "cached" else False
    tree = build_category_hierarchy()
    # gets all bing related results for the given 'database' ie. host url
    # and puts relevant info in the tree itself
    # from which we can compute specificity and classify the url
    print("Classifying....")
    if cached:
        filename = host_url + "-cached.p"
        if filename not in os.listdir("."):
            get_bing_results_for_hierarchy(tree, ROOT, account_key, host_url)
            pickle.dump(tree, open(filename, "w"))
        else:
            tree = pickle.load(open(filename, "r"))
    else:
        get_bing_results_for_hierarchy(tree, ROOT, account_key, host_url)

    labels = classify(ROOT, tree, t_es, t_ec)
    paths = []

    for label in labels:
        nodes = []
        category_name = label
        while category_name is not None:
            nodes.append(category_name)
            category_name = tree[category_name][PARENT]
        paths.append("/".join(reversed(nodes)))

    print("Classification for URL", host_url)
    map(lambda path: print(path), paths)

if __name__ == "__main__":
    main()
