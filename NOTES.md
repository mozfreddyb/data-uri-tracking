# Currently/Recently
- Working on status tracking
- pushed a commit to try that prints to stdout "ERROR DataUriUsageTracking"
- https://treeherder.mozilla.org/#/jobs?repo=try&revision=6087d958cb9622726c7c0ca605520ecfdd4b8701

# Next steps
- wait for a job to complete and see if that's meaningfully reported in the job's bug_suggstion JSON response
- -  e.g., insert (numerical) JOB ID into https://treeherder.mozilla.org/api/project/try/jobs/%s/bug_suggestions/
- identify a way to count errors and filter by job_type_symbol (e.g., R5) or job_group_name (e.g., Reftests)


# Completed
- 
