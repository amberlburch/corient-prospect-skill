#!/usr/bin/env bash
# Build dist/prospect.zip for upload in Claude > Customize > Skills.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="$HOME/.claude/skills/outreach"
if [ -d "$SRC" ]; then
  cp "$SRC/references/triggers.md" "$SRC/references/personalisation-buckets.md" prospect/references/
  cp "$SRC/scripts/lint_outreach.py" prospect/scripts/
fi

if grep -rn $'—\|–' prospect/SKILL.md prospect/references/icp-and-scoring.md prospect/references/writing-the-email.md; then
  echo "dash found in skill copy" >&2; exit 1
fi

sample=$(mktemp)
printf 'Subject: the first marketing hire\n\nHi Sam, a seed round and a Head of Growth ad in the same month usually means the board wants a number by Christmas. That is a lot to put on one person, and good ones take months to find. We embed a CMO with a pod of specialists, so you get a whole marketing team for about the cost of that one hire. What does the new hire need to prove in their first 90 days?\n' > "$sample"
python3 prospect/scripts/lint_outreach.py --channel email --first-touch --file "$sample" > /dev/null
rm -f "$sample"

rm -rf dist && mkdir -p dist
zip -rq dist/prospect.zip prospect -x '*.DS_Store' '*__pycache__*'
unzip -l dist/prospect.zip
