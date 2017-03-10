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

def fetch_log(url):
    response = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, timeout=30)
    response.raise_for_status()
    return response.text

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
    # this picks the topmost commit (commit message is the try syntax)
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

REVISION = '6087d958cb9622726c7c0ca605520ecfdd4b8701'
csetresults = getCSetResults('try', REVISION)
results = csetresults['results']

# this is where we collect results
affected_groups = {}


retry_urls = []

for r in results:
    # looping through results for all jobs that ran for this push.
    # get bug suggestions: https://treeherder.mozilla.org/api/project/try/jobs/82734186/bug_suggestions/
    jobinfo_url = 'https://treeherder.mozilla.org/api/project/try/jobs/%s/' % r['id']
    jobinfo = fetch_json(jobinfo_url)
    if jobinfo['state'] != "completed":
        #retry_urls.append(jobinfo_url)
        #continue
        raise SystemExit("[!] This try run is not finished, go away you fool.")
    for logentry in jobinfo['logs']:
        # logs array contains full log 'builds-4h' and 'errorsummary_json'.
        # error summary does not (yet!) reliably contain all errors, so picking full log
        if logentry['name'] != 'errorsummary_json':
            # this is the full log.
            logurl = logentry['url']
            logtext = fetch_log(logurl)
            errorcount = 0
            for line in logtext.split("\n"):
                if "DataUriUsageTracking" in line:
                    errorcount += 1
            if errorcount > 0:

                if jobinfo['job_group_symbol'] in affected_groups:
                    # add to list
                    affected_groups[ jobinfo['job_group_symbol'] ][ jobinfo['job_type_symbol'] ] = errorcount
                else:
                    # create empty list
                    affected_groups[ jobinfo['job_group_symbol'] ] = { jobinfo['job_type_symbol'] : errorcount }
                print "Group {}, type {} has {} errors".format(jobinfo['job_group_symbol'], jobinfo['job_type_symbol'], affected_groups[ jobinfo['job_group_symbol'] ][ jobinfo['job_type_symbol'] ])

print "Dumping into 'result.json'"
import json
json.dump(affected_groups, file("result.json", "w"))
print "Done"