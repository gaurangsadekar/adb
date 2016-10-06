from __future__ import print_function
import urllib, urllib2, base64
import json
import sys
import string
import numpy as np

exclude = set(string.punctuation)

def bing_query_results(search_query):
    search_query_enc = urllib.quote_plus("'{}'".format(search_query))
    bingUrl = "https://api.datamarket.azure.com/Bing/Search/Web?Query=" + search_query_enc + "&$top=10&$format=json"

    accountKey = "mbw46R+7k+Lf+GGFAE+yVER05KjxvEywUXPTLKTrlpg"
    #accountKey = "2dyKIv94jDETd7ClbVKoHvJSWFJ73ZvZRc7rjpBdkG8"
    accountKeyEnc = base64.b64encode(accountKey + ':' + accountKey)
    headers = {"Authorization" : "Basic " + accountKeyEnc}
    req = urllib2.Request(bingUrl, headers = headers)
    response = urllib2.urlopen(req)
    # content contains the xml/json response from Bing
    json_resp = json.load(response)
    return json_resp["d"]["results"]

def mark_relevance(search_results):
    relevant_results = []
    # no rigorous input validation
    # everything except Y or y is considered as n
    for i in range(len(search_results)):
        curr = search_results[i]
        print ("URL:", curr["Url"])
        print ("Title:", curr["Title"])
        print ("Description:", curr["Description"])
        user_resp = raw_input("Is this result relevant?[Y/N]")
        rel = False
        if user_resp == 'Y' or user_resp == 'y':
            rel = True
        relevant_results.append(rel)
    return relevant_results

stop_set = []
file1 = urllib2.urlopen("http://www.cs.columbia.edu/~gravano/cs6111/Proj1/stop.txt")
stoplist = [ l.strip() for l in file1 ]
stoplist.extend(["a","an","the","is","to", "of", "in", "into","upto","will","has","be","shall","would","could","may","on","and","for","been"])
set(stoplist)

def remove_punctuation(word):
    return "".join(ch for ch in word if ch not in exclude)

# create a dictionary of all words except the stop words
# this is given a cleaned list of search results
# this dictionary is used globally
word_dict = []
def create_dictionary(word_lists):
    for words in word_lists:
        for word in words:
            if word not in stop_set and word not in word_dict:
                word_dict.append(word)

# computes the tf-idf from all the search results
# using titles and descriptions
# returns a numpy array of weight vectors for every result
def compute_tfidf(titles, descs, num_res):
    # 1 vector of size word_dict per search result
    term_frequencies = []
    for i in range(num_res):
        doc_tf = []
        for word in word_dict:
            count = titles[i].count(word) + descs[i].count(word)
            doc_tf.append(count)
        term_frequencies.append(doc_tf)

    # 1 vector, size of word dict
    doc_freqs = []
    for word in word_dict:
        count = 0
        for i in range(num_res):
            if word in titles[i] or word in descs[i]:
                count += 1
        doc_freqs.append(count)

    N = float(num_res)
    # compute idf from document frequencies
    idfs = map(lambda freq: np.log(N / freq), doc_freqs)
    np_tfs = np.array(term_frequencies)
    return np_tfs * idfs

def main():
    # get input from command line
    desired_prec = float(sys.argv[1])
    query = sys.argv[2:]
    input_query = " ".join(query)

    while (True):
        print("Bing Search Results:")
        print("====================")
        search_results = bing_query_results(input_query)
        if len(search_results) < 10:
            print("< 10 search results")
            break

        relevants = mark_relevance(search_results)
        num_res = len(search_results)
        num_relevant = len(filter(lambda x : x, relevants))
        num_irrelevant = num_res - num_relevant
        search_prec =  num_relevant / 10.0
        print("Precision achieved:", search_prec)
        if search_prec == 0.0:
            print("Zero precision in search results, quitting")
            break
        elif search_prec >= desired_prec:
            print("Desired precedence reached, stopping search")
            break

        titles = []
        descs = []
        for res in search_results:
            title = remove_punctuation(res["Title"]).lower().split()
            desc = remove_punctuation(res["Description"]).lower().split()
            titles.append(title)
            descs.append(desc)

        create_dictionary(titles)
        create_dictionary(descs)
        # initialized vector for input query
        query_vec = [(1 if word in query else 0) for word in word_dict]
        # unnormalized tf-idf
        tfidf = compute_tfidf(titles, descs, num_res)
        # normalized tf-idf
        norms = np.linalg.norm(tfidf, axis=1)
        print(norms)
        normalized_tfidf = (tfidf.T / norms).T
        _, num_words = normalized_tfidf.shape
        # Rocchio's Algorithm
        # the algorithm uses the initial query, relevant documents and irrelevant docs
        # to augment the query in the next iteration
        # using the normalized tf-idf vectors, and 3 coefficients alpha, beta and gamma
        # which are set empirically
        relevant_sum = np.zeros(num_words)
        irrelevant_sum = np.zeros(num_words)
        for i in range(len(relevants)):
            if relevants[i]:
                relevant_sum += normalized_tfidf[i]
            else:
                irrelevant_sum += normalized_tfidf[i]
        relevant_sum = relevant_sum / num_relevant
        irrelevant_sum = irrelevant_sum / num_irrelevant

        alpha = 1 # weight of original query
        beta = 0.75 # weight of relevant results
        gamma = 0.25 # weight of irrelevant results
        # since we want the query to remain at least the same in spirit,
        # we give it the heighest weighting
        # we don't punish irrelevant results too severely, giving them some weight rather than 0
        query_vec_next = alpha * query_vec + beta * relevant_sum - gamma * irrelevant_sum
        # find top 2 words in the next vector that are not in the original words
        # see what words are given from the word list
        print(query_vec_next)
        break

if __name__ == "__main__":
    main()
