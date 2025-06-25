#!/bin/bash
# Usage: ./protect_branches.sh <owner> <repo>
OWNER=$1
REPO=$2
for BRANCH in dev qa stage prod; do
  gh api -X PUT \
    -H "Accept: application/vnd.github+json" \
    /repos/$OWNER/$REPO/branches/$BRANCH/protection \
    -f required_status_checks.strict=true \
    -f required_status_checks.contexts='[]' \
    -f enforce_admins=true \
    -f required_pull_request_reviews.dismiss_stale_reviews=true \
    -f required_pull_request_reviews.required_approving_review_count=1 \
    -f restrictions='null'
done 