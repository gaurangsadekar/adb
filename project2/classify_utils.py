from __future__ import print_function
import urllib, urllib2, base64
import json
import sys
import string

# takes account key, host_url and search query
# returns number of matches for query and the 10 web search results returned
def bing_web_search(account_key, host_url, search_query):
    query_str = "site:" + host_url + " " + search_query
    query_enc = urllib.quote("'{}'".format(query_str))
    bing_url = "https://api.datamarket.azure.com/Data.ashx/Bing/SearchWeb/v1/Composite?Query=" + query_enc + "&$top=10&$format=json"
    account_key_enc = base64.b64encode(account_key + ':' + account_key)
    headers = {"Authorization" : "Basic " + account_key_enc}
    req = urllib2.Request(bing_url, headers = headers)
    response = urllib2.urlopen(req)
    json_resp = json.load(response)
    results = json_resp["d"]["results"][0]
    num_matches = int(results["WebTotal"])
    search_res = map(lambda r: r["Url"], results["Web"])
    return (num_matches, search_res)

'''
each node has the following structure:
    sub-categories: set(sub-categories)
    parent: string parent's name
    is_leaf: boolean
    probes: queries for this category
    should include matches and top 4 results of each query
'''
# constants in category nodes
PARENT = "parent"
SUB_CATEGORIES = "sub_categories"
IS_LEAF = "is_leaf"
PROBES = "probes"
COVERAGE = "coverage"
SPECIFICITY = "specificity"
ROOT = "Root"

def make_new_category(parent_name):
    category_node = {}
    category_node[PARENT] = parent_name
    category_node[SUB_CATEGORIES] = set()
    category_node[IS_LEAF] = True
    category_node[PROBES] = []
    category_node[COVERAGE] = 0
    category_node[SPECIFICITY] = 0.0
    return category_node

def build_category_hierarchy():
    tree = {}
    # read queries from the category files
    # build a dict with query probes for each category
    category_path = "./categories/"
    hierarchy = ["Root", "Computers", "Health", "Sports"]
    # root has no parent
    tree[ROOT] = make_new_category(None)
    # special case for root
    tree[ROOT][SPECIFICITY] = 1.0

    for filename in hierarchy:
        with open(category_path + filename + ".txt", "r") as f:
            rules = f.readlines()
            parent_name = filename.title()
            for rule in rules:
                r = rule.strip().split(" ")
                category_name = r[0]
                query_probe = " ".join(r[1:])
                if category_name in tree:
                    tree[category_name][PROBES].append(query_probe)
                else:
                   node = make_new_category(parent_name)
                   node[PROBES].append(query_probe)
                   tree[category_name] = node
                   tree[parent_name][SUB_CATEGORIES].add(category_name)

    # mark all nodes in hierarchy as non-leaves
    for category_name in hierarchy:
        tree[category_name.title()][IS_LEAF] = False
    return tree

