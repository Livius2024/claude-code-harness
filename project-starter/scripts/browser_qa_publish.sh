#!/usr/bin/env bash
# Publish browser QA results on a PR: push the screenshots in $SRC/shots to
# the screenshots branch under pr-<n>/<run>/ (replacing that PR's older runs),
# then create or update the PR's single browser QA comment from
# $SRC/comment.md. Run by .github/workflows/browser-qa.yml.
#
# Env: GH_TOKEN (contents:write, pull-requests:write), REPO (owner/name),
# PR (number), RUN_KEY (<run id>-<attempt>), SRC (default qa-out),
# BRANCH (default browser-qa-screenshots), REMOTE (default the repo on
# github.com; the tests point it at a local repository).
set -euo pipefail

src=${SRC:-qa-out}
branch=${BRANCH:-browser-qa-screenshots}
marker='<!-- browser-qa -->'
: "${GH_TOKEN:?}" "${REPO:?}" "${PR:?}" "${RUN_KEY:?}"

if compgen -G "$src/shots/*.png" > /dev/null; then
  work=$(mktemp -d)
  git -C "$work" init -q
  git -C "$work" config user.name "github-actions[bot]"
  git -C "$work" config user.email "41898343+github-actions[bot]@users.noreply.github.com"
  git -C "$work" remote add origin "${REMOTE:-https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git}"

  # Each attempt rebuilds the commit on the branch's latest tip, so two PRs
  # publishing at the same time both land.
  for attempt in 1 2 3 4 5; do
    if git -C "$work" fetch -q --depth 1 origin "$branch" 2> /dev/null; then
      git -C "$work" checkout -q -f -B "$branch" FETCH_HEAD
    else
      git -C "$work" checkout -q -f --orphan "$branch"
    fi
    rm -rf "${work:?}/pr-$PR"
    mkdir -p "$work/pr-$PR/$RUN_KEY"
    cp "$src"/shots/*.png "$work/pr-$PR/$RUN_KEY/"
    git -C "$work" add -A
    git -C "$work" commit -q -m "Browser QA screenshots for PR #$PR (run $RUN_KEY)"
    if git -C "$work" push -q origin "HEAD:refs/heads/$branch"; then
      break
    fi
    if [ "$attempt" -eq 5 ]; then
      echo "Could not push the screenshots to $branch" >&2
      exit 1
    fi
    sleep $((attempt * 2))
  done
fi

comment_id=$(gh api --paginate "repos/$REPO/issues/$PR/comments" \
  --jq ".[] | select(.user.login == \"github-actions[bot]\" and (.body | startswith(\"$marker\"))) | .id" | tail -n 1)
if [ -n "$comment_id" ]; then
  gh api -X PATCH "repos/$REPO/issues/comments/$comment_id" -F "body=@$src/comment.md" > /dev/null
  echo "Updated the browser QA comment on PR #$PR"
else
  gh api "repos/$REPO/issues/$PR/comments" -F "body=@$src/comment.md" > /dev/null
  echo "Posted the browser QA comment on PR #$PR"
fi
