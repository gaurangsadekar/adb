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
        print(query, len(search_urls))
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

def createDocumentSample(tree, nodes):
    samples = {}
    prev=None
    for node in nodes:
        if prev is not None:
            links=set()
            for url in samples[prev]:
                links.add(url)            
            for sub_category_name in tree[node][SUB_CATEGORIES]:    
                for query in tree[sub_category_name][PROBES]:
                    count=0
                    for url in tree[sub_category_name][PROBES][query]:
                        if (count==4):
                            break
                        links.add(url)
                        count+=1;              
            samples[node]=list(links)
            prev=node
        else:
            links=set()
            missinglinks=0
            if tree[node][IS_LEAF] is False:
                for sub_category_name in tree[node][SUB_CATEGORIES]: 
                    for query in tree[sub_category_name][PROBES]:
                        count=0
                        for url in tree[sub_category_name][PROBES][query]:
                            if(count==4):
                                break
                            links.add(url)
                            count+=1;
            samples[node]=list(links)
            prev=node
    return samples

def is_ascii(string):
    return all(ord(char) < 128 for char in string)

def createDocumentSummaries(samples, nodes, host_url,tree):
    words ={}
    program = "getWordsLynx"
    if program+".class" in os.listdir("."):
        compile_command = "javac " + program + ".java"
        os.system(compile_command)

    for node in nodes:
        if tree[node][IS_LEAF]:
            pass            
        total_docs=len(samples[node])
        print ("Generating content summary for ", node)
        if (total_docs>0):
            for i in range(total_docs):
                url = samples[node][i]
                print("Getting content for ", url)
                command = "java " + program + " " + url + " words.txt"
                if(is_ascii(command)):
                    os.system(command)   
                file1 = open("words.txt", "r")
                for l in file1:
                    l=l.strip()
                    words[l]=words.get(l,0)+1
        filename = node+"-" +host_url+".txt"
        file = open(filename,"w")
        for (word, count) in sorted(words.iteritems(), key= lambda t :t[0]):
            line = word + "#" + str(count) + "\n"
            file.write(line)


def main():
    account_key = sys.argv[1]
    t_es = float(sys.argv[2])
    t_ec = int(sys.argv[3])
    host_url = sys.argv[4]
    cached = True if len(sys.argv) == 6 and sys.argv[5] == "cached" else False
    print("Building category hierarchy")
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
        samples={}
        while category_name is not None:
            nodes.append(category_name)
            category_name = tree[category_name][PARENT]
        # for node in reversed(nodes):
        paths.append("/".join(reversed(nodes)))
        
    print("Classification for URL", host_url)
    map(lambda path: print(path), paths)

    for label in labels:
        nodes = []
        category_name = label
        samples={}
        while category_name is not None:
            nodes.append(category_name)
            category_name = tree[category_name][PARENT]
        samples=createDocumentSample(tree,nodes)
        createDocumentSummaries(samples,nodes,host_url,tree)

if __name__ == "__main__":
    main()
