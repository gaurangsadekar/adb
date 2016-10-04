from __future__ import print_function
import urllib, urllib2, base64
import json
import sys
import string
from collections import Counter
import math

new_results=[]
stoplist=[]
dict = {}

def bing_query_results(search_query):
    search_query_enc = urllib.quote_plus("'{}'".format(search_query))
    bingUrl = "https://api.datamarket.azure.com/Bing/Search/Web?Query=" + search_query_enc + "&$top=10&$format=json"

    accountKey = "mbw46R+7k+Lf+GGFAE+yVER05KjxvEywUXPTLKTrlpg"
    accountKeyEnc = base64.b64encode(accountKey + ':' + accountKey)
    headers = {"Authorization" : "Basic " + accountKeyEnc}
    req = urllib2.Request(bingUrl, headers = headers)
    response = urllib2.urlopen(req,)
    # content contains the xml/json response from Bing
    json_resp = json.load(response)
    return json_resp["d"]["results"]

def mark_relevance(search_results):
    relevant_results = []
    count=0
    for i in range(len(search_results)):
        curr = search_results[i]
        print ("URL:", curr["Url"])
        print ("Title:", curr["Title"])
        print ("Description:", curr["Description"])
        user_resp = raw_input("Is this result relevant?[Y/N]")
        if user_resp == 'Y' or user_resp == 'y':
            count= count+1
            new_results.append(curr["Title"] +curr["Description"])
    return count #number of relevant results.

#takes the file from the site and stores a list of stopwords. Added some more stop words.
def create_stopwordlist():
    file1 = urllib2.urlopen("http://www.cs.columbia.edu/~gravano/cs6111/Proj1/stop.txt") #open('stop.txt','r')
    for line in file1:
        w=line.strip()
        for word in w:
            stoplist.append(word);
    stoplist.extend(("a","an","the","is","to", "of", "in", "into","upto","will","has","be","shall","would","could","may","on","and","for","been"))

#Takes a string anc calculates the frequency of word,the count of documents the word has appeared in, and termfrequency
def calculate_freq(s):
    exclude = set(string.punctuation)
    s = "".join(ch for ch in s if ch not in exclude)
    word_array=[]
    for word in s.lower().split():
        if word not in stoplist:
                word_array.append(word)
    c = Counter(word_array)
    maxVal= max(c[word] for word in c)
    #print (maxVal)
    for word in c:
        #print '%s : %d' % (word, c[word])
        if dict.has_key(word) is False:
            dict.setdefault(word,[c[word]]).append(1)
            dict.get(word).append(float(c[word]/maxVal))
        else:
            dict.get(word)[0]=dict.get(word)[0]+c[word] #count of words
            dict.get(word)[1]= dict.get(word)[1]+1 #count of documents
            dict.get(word)[2]=float(dict.get(word)[0]/maxVal) # term frequency
            #print(word)
            #print(dict.get(word)[2])

def calculate_tfidf(relevance):
    create_stopwordlist()
    for string in new_results:
        calculate_freq(string)
    #print (dict)

    tfidf=[[]]
    for key in dict:
        tf=float(dict.get(key)[2])
        idf=float (math.log (float(relevance/ dict.get(key)[1])))
        value=tf*(idf)
        tfidf.append([key,value])
        #print ('%s : %f : %f' % (key,tf,idf))
        #print(idf)
        #print(tf)

    #print(tfidf)

def main():
    # get input from command line
    desired_prec = float(sys.argv[1])
    input_query = " ".join(sys.argv[2:])
    search_results = bing_query_results(input_query)
    if len(search_results) < 10:
        exit("< 10 search results")

    relevance= mark_relevance(search_results)

    search_prec = relevance/ 10.0
    print("Precision achieved:", search_prec)
    if search_prec >= desired_prec:
        exit("Desired precedence reached, stopping search")
    elif search_prec == 0.0:
        exit("Zero precision in search results, quitting")

    calculate_tfidf(relevance)
    
    # to tf-idf things to the relevant results, no need to use irrelevant docs
if __name__ == "__main__":
    main()