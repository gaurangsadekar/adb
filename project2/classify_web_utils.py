from __future__ import print_function
import urllib, urllib2, base64
import json
import sys
import string
import os
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
    num_matches = results["WebTotal"]
    search_res = results["Web"]
    return (num_matches, search_res)

'''
each node has the following structure:
    sub-categories
    parent
    is_leaf
    probes
    new node creation
        category_node = {}
        category_node["parent"] = parent_category
        category_node["sub_categories"] = set()
        category_node["is_leaf"] = True
        category_node["probes"] = []
'''
# constants in category nodes
PARENT = "parent"
SUB_CATEGORIES = "sub_categories"
IS_LEAF = "is_leaf"
PROBES = "probes"

def make_new_category(parent_name):
    category_node = {}
    category_node[PARENT] = parent_name
    category_node[SUB_CATEGORIES] = set()
    category_node[IS_LEAF] = True
    category_node[PROBES] = []
    return category_node

def build_category_hierarchy():
    tree = {}
    # read queries from the category files
    # build a dict with query probes for each category
    category_path = "./categories/"
    hierarchy = ["root", "computers", "health", "sports"]
    # root has no parent
    tree["Root"] = make_new_category(None)

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

    # mark all nodes in hierarchy is non-leaves
    for category_name in hierarchy:
        tree[category_name.title()][IS_LEAF] = False
    return tree

def main():
    account_key = sys.argv[1]
    t_es = float(sys.argv[2])
    t_ec = int(sys.argv[3])
    host_url = sys.argv[4]





if __name__ == "__main__":
    main()
