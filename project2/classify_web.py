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
    num_matches = results["WebTotal"]
    search_res = results["Web"]
    return (num_matches, search_res)

def main():
    account_key = sys.argv[1]
    t_es = float(sys.argv[2])
    t_ec = int(sys.argv[3])
    host_url = sys.argv[4]

    # read queries from the category files
    # query bing for each of them one by one
if __name__ == "__main__":
    main()
