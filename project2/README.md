# Web Database Classification and Content Summaries
## Project 2

There are 2 parts to this project:
- [x] *Part A*: classify the web database (URL) that is input to the program
- [ ] *Part B*: collect a sample of the returned search results and build a content summary of the webpage from it

To run the code, use the following command:
```shell
python classify_web.py <Bing Account Key> <t_es> <t_ec> <url> [cached]
```
If `cached` is included in the run command, the Bing query results for the host URL are cached in a pickle file.

```
t_es (specificity threshold) = float value between 0 and 1
t_ec (coverage threshold) = +ve valued integer
```

For testing purposes, it is desirable to use the cached option so that Bing is not queried multiple times for the same host URL, as each key is limited to 5000 API calls per month

#### Tested with:
- www.fifa.com: Root/Sports/Soccer
- www.docker.com: Root/Computers/Programming

