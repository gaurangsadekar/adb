from __future__ import print_function
import urllib, urllib2, base64
import json
import sys
import string
import numpy as np

# generating the transcript file
transcript = []

# using implementation provided on course webpage
def bing_query_results(accountKey, search_query):
    search_query_enc = urllib.quote_plus("'{}'".format(search_query))
    bingUrl = "https://api.datamarket.azure.com/Bing/Search/Web?Query=" + search_query_enc + "&$top=10&$format=json"

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
        print("Result", i + 1, ":")
        transcript.append("Result " + str(i + 1))
        curr = search_results[i]
        curr_url = "URL:" + curr["Url"]
        curr_title = "Title:" + curr["Title"]
        curr_desc = "Description:" + curr["Description"]
        print (curr_url)
        print (curr_title)
        print(curr_desc)
        user_resp = raw_input("Is this result relevant?[Y/N]")
        rel = False
        if user_resp == 'Y' or user_resp == 'y':
            rel = True
        relevant_results.append(rel)

        rel_str = "RELEVANT: "
        if rel:
            transcript.append(rel_str + "YES")
        else:
            transcript.append(rel_str + "NO")
        transcript.append("[")
        transcript.append("  " + curr_url)
        transcript.append("  " + curr_title)
        transcript.append("  " + curr_desc)
        transcript.append("]")
        transcript.append("\n")

    return relevant_results

# create a set of stop words from stop words list
file1 = open("stopwords.txt", "r")
stoplist = [ l.strip() for l in file1 ]
stop_set = set(stoplist)

def remove_punctuation(word):
    splitters = set(['.', '-', ':', ';', '/', '\\', '\''])
    return "".join([(ch if ch not in splitters else ' ') for ch in word])

# create a dictionary of all words except the stop words
# this is given a cleaned list of search results
# this dictionary is used globally
def create_dictionary(word_lists, word_dict):
    for words in word_lists:
        for word in words:
            if (word not in stop_set) and (word not in word_dict):
                word_dict.append(word)

# computes the tf-idf from all the search results
# using titles and descriptions
# returns a numpy array of weight vectors for every result
def compute_tfidf(titles, descs, word_dict, num_res):
    # 1 vector of size word_dict per search result
    term_frequencies = []
    for i in range(num_res):
        doc_tf = []
        tdd = []
        for word in word_dict:
            title_count = titles[i].count(word)
            desc_count = descs[i].count(word)

            # to make sure that if words in a title and description are the same
            # count them once. Otherwise the model is wrongly biased to links
            # where the title and description are the same
            multiplier = 1.0
            if title_count ==  desc_count:
                multiplier = 0.5
            count = (title_count + desc_count) * multiplier
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
    np_tfs = np.array(term_frequencies, dtype=float)
    return np_tfs * idfs

def main():
    # get input from command line
    account_key = sys.argv[1]
    desired_prec = float(sys.argv[2])
    query = sys.argv[3:]
    query = [s.lower() for s in query]

    transcript_name = " ".join(query)
    round_num = 0
    while (True):
        input_query = " ".join(query)
        search_results = bing_query_results(account_key, input_query)
        round_num += 1
        transcript.append("=====================================")
        transcript.append("ROUND " + str(round_num))
        print("Query:", input_query)
        transcript.append("QUERY " + input_query)
        transcript.append("\n")
        print("Desired Precision:", desired_prec)
        print("Bing Search Results:")
        print("====================")
        if len(search_results) < 10:
            print("< 10 search results")
            break

        relevants = mark_relevance(search_results)
        num_res = len(search_results)
        num_relevant = len(filter(lambda x : x, relevants))
        num_irrelevant = num_res - num_relevant
        search_prec =  float(num_relevant) / num_res
        print("FEEDBACK SUMMARY")
        print("================")
        print("Precision achieved:", search_prec)
        transcript.append("PRECISION " + str(search_prec))
        if search_prec == 0.0:
            print("Zero precision in search results, quitting")
            break
        elif search_prec >= desired_prec:
            print("Desired precedence reached, stopping search")
            break

        print("Below desired precision", desired_prec)

        titles = []
        descs = []
        for res in search_results:
            title = remove_punctuation(res["Title"].lower()).encode("ascii", "ignore").split()
            desc = remove_punctuation(res["Description"].lower()).encode("ascii", "ignore").split()
            titles.append(title)
            descs.append(desc)

        word_dict = []
        create_dictionary(titles, word_dict)
        create_dictionary(descs, word_dict)
        # initialized vector for input query
        query_vec = [(1.0 if word in query else 0.0) for word in word_dict]
        # unnormalized tf-idf
        tfidf = compute_tfidf(titles, descs, word_dict, num_res)
        # normalized tf-idf
        norms = np.linalg.norm(tfidf, axis=1)
        normalized_tfidf = (tfidf.T / norms).T
        _, num_words = normalized_tfidf.shape

        # Rocchio's Algorithm
        # the algorithm uses the initial query, relevant documents and irrelevant docs
        # to augment the query in the next iteration
        # using the normalized tf-idf vectors
        # and 3 coefficients alpha, beta and gamma which are set empirically
        relevant_sum = np.zeros(num_words, dtype=float)
        irrelevant_sum = np.zeros(num_words, dtype=float)
        for i in range(len(relevants)):
            if relevants[i]:
                relevant_sum += normalized_tfidf[i,:]
            else:
                irrelevant_sum += normalized_tfidf[i,:]
        relevant_sum = relevant_sum / num_relevant
        irrelevant_sum = irrelevant_sum / num_irrelevant

        alpha = 1 # weight of original query
        beta = 0.75 # weight of relevant results
        gamma = 0.25 # weight of irrelevant results
        # since we want the query to remain at least the same in spirit,
        # we give it the heighest weighting
        query_vec_next = alpha * query_vec + beta * relevant_sum - gamma * irrelevant_sum
        # find top 2 words in the next vector that are not in the original words
        sorted_indices = np.argsort(query_vec_next)
        # get the top words to add to the query, except those in the query already
        candidate_words = [word_dict[i] for i in reversed(sorted_indices) if word_dict[i] not in query]
        # add the top 2 candidates to the query
        query.extend(candidate_words[:2])

    # write transcript to file
    filename = "transcript_" + transcript_name + ".txt"
    transcript_str = "\n".join(transcript)
    f = open("transcripts/" + filename, "w")
    f.write(transcript_str.encode("utf-8"))
    f.close()

if __name__ == "__main__":
    main()
