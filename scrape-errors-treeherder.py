# mostly copied from https://github.com/mozilla/ouija/blob/master/src/updatedb.py
# for reference: https://treeherder.mozilla.org/api/
# and of course open treeherder view + devtools network and see what api's are called when clicking on a job

import requests

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'ouija',
}

def fetch_json(url):
    response = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()

def getResultSetID(branch, revision):
    url = "https://treeherder.mozilla.org/api/project/%s/resultset/" \
          "?format=json&full=true&revision=%s" % (branch, revision)
    return fetch_json(url)

def getCSetResults(branch, revision):
    """
    https://tbpl.mozilla.org/php/getRevisionBuilds.php?branch=mozilla-inbound&rev=3435df09ce34.
    no caching as data will change over time.  Some results will be in asap, others will take
    up to 12 hours (usually < 4 hours)
    """
    rs_data = getResultSetID(branch, revision)
    results_set_id = rs_data['results'][0]['id']

    done = False
    offset = 0
    count = 2000
    num_results = 0
    retVal = {}
    while not done:
        url = "https://treeherder.mozilla.org/api/project/%s/jobs/" \
              "?count=%s&offset=%s&result_set_id=%s"
        data = fetch_json(url % (branch, count, offset, results_set_id))
        if len(data['results']) < 2000:
            done = True
        num_results += len(data['results'])
        offset += count

        if retVal == {}:
            retVal = data
        else:
            retVal['results'].extend(data['results'])
            retVal['meta']['count'] = num_results

    return retVal

REVISION = 'a8774a1bf36810bb338ff2382e2b400a452bfca2'
csetresults = getCSetResults('try', REVISION)
results = csetresults['results']

for r in results:
    # get bug suggestions: https://treeherder.mozilla.org/api/project/try/jobs/82734186/bug_suggestions/
    url = 'https://treeherder.mozilla.org/api/project/try/jobs/%s/bug_suggestions/' % r['id']
    data = fetch_json(url)
    previous_search_terms = ''
    for line in data:
        if line['search_terms'] != previous_search_terms:
            print line['search']
        previous_search_terms = line['search_terms']