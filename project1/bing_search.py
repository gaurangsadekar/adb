from __future__ import print_function
import urllib, urllib2, base64
import json
import sys

def bing_query_results(search_query):
    search_query_enc = urllib.quote_plus("'{}'".format(search_query))
    bingUrl = "https://api.datamarket.azure.com/Bing/Search/Web?Query=" + search_query_enc + "&$top=10&$format=json"

    accountKey = "mbw46R+7k+Lf+GGFAE+yVER05KjxvEywUXPTLKTrlpg"
    accountKeyEnc = base64.b64encode(accountKey + ':' + accountKey)
    headers = {"Authorization" : "Basic " + accountKeyEnc}
    req = urllib2.Request(bingUrl, headers = headers)
    response = urllib2.urlopen(req)
    # content contains the xml/json response from Bing
    json_resp = json.load(response)
    return json_resp["d"]["results"]

def mark_relevance(search_results):
    relevant_results = []
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

def main():
    # get input from command line
    desired_prec = float(sys.argv[1])
    input_query = " ".join(sys.argv[2:])
    search_results = bing_query_results(input_query)
    if len(search_results) < 10:
        exit("< 10 search results")

    relevants = mark_relevance(search_results)

    search_prec = len(filter(lambda x : x, relevants)) / 10.0
    print("Precision achieved:", search_prec)
    if search_prec >= desired_prec:
        exit("Desired precedence reached, stopping search")
    elif search_prec == 0.0:
        exit("Zero precision in search results, quitting")

    marked_results = zip(search_results, relevants)
    # keep only the relevant results
    relevant_results = filter(lambda (result, relevant): relevant, marked_results)

    # to tf-idf things to the relevant results, no need to use irrelevant docs
if __name__ == "__main__":
    main()
