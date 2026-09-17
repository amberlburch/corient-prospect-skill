# ICP, research query and scoring

## ICP

All of these, or the company is out:

- Headquartered in Australia or New Zealand.
- Founder-led, 5 to 100 staff.
- One of three segments:

| Segment | Industries | Revenue |
|---|---|---|
| B2B tech | IT services, software, internet | $1m to $10m |
| B2C tech | internet, consumer software, e-learning | $1m to $10m |
| Premium consumer | apparel and fashion, cosmetics, consumer goods, health, wellness and fitness | $2m to $15m |

- The person emailed is the founder, CEO or a marketing leader appointed in the last 45 days. Never a CTO, engineer, investor or advisor.

Out, always: enterprises, government, agencies and consultancies (they compete with Corient), companies Corient already works with, and anything in `suppression.csv`.

## Research (Exa `agent_run`, effort low, one run per segment)

Query shape, filled per segment:

> Find up to 8 founder-led companies headquartered in Australia or New Zealand with 5 to 100 staff in {segment industries} that, between {today minus 45 days} and {today}, announced a funding round (pre-seed to Series B), appointed a new Head of Marketing, CMO or VP Growth, posted a marketing or growth role (Head of Marketing, Growth Marketing, Performance Marketing, Marketing Manager, Brand Manager, Ecommerce Manager), launched a product, or expanded into a new market. Prefer StartupDaily, SmartCompany, AFR, Business News WA, Scoop Business, company blogs and careers pages, Seek and LinkedIn. Every signal needs a source URL and its publication date. Name the founder or CEO, their title and LinkedIn URL.

Pass domains already labelled `Prospect/Ready`, `Prospect/Sent` or `Prospect/Skipped` in the last 180 days as `input.exclusion`, one object per domain: `{"domain": "..."}`.

Output schema:

```json
{"type":"object","properties":{"companies":{"type":"array","maxItems":8,"items":{"type":"object","properties":{
  "company":{"type":"string"},"domain":{"type":"string"},"segment":{"type":"string"},
  "headcount_estimate":{"type":"string"},"hq":{"type":"string"},
  "signals":{"type":"array","maxItems":2,"items":{"type":"object","properties":{
    "type":{"type":"string","enum":["marketing_hire","funding","new_marketing_leader","launch","expansion","founder_post"]},
    "summary":{"type":"string"},"source_url":{"type":"string"},"published":{"type":"string"}}}},
  "decision_maker":{"type":"string"},"title":{"type":"string"},"linkedin_url":{"type":"string"}}}}}}
```

## Email lookup (Exa `agent_run`, survivors only)

Pass the survivors as `input.data` with name, company, domain and LinkedIn. Query:

> For each person, find their work email using email enrichment. Return an email only if enrichment or a published source provides it. Never construct one from a name pattern.

**Domain-match rule.** The part after `@` must equal the company domain (a subdomain of it is fine). Anything else means a previous employer or a different person: no draft, list as "LinkedIn only". The 17 Sep 2026 test returned a founder's email at her previous agency, rated "High". Confidence ratings do not override this rule.

## Signal windows

Measured from the publication date to today. Outside the window, the signal does not count.

| Signal | Window | Points |
|---|---|---|
| Marketing or growth role posted (they are pricing one hire right now, the offer's exact comparison) | 0 to 30 days | 4 |
| Funding round | 7 to 45 days. Under 7 days: hold and recheck on a later run | 3 |
| New marketing leader | 14 to 45 days | 3 |
| Launch | 3 to 30 days | 2 |
| Market or retail expansion | 14 to 60 days | 2 |
| Founder's own post on growth or marketing | 1 to 14 days | 2 |

Bonus points:

- +2 when the second signal explains the first, for example funding plus a marketing hire (the money plus the plan), or a launch plus a growth hire. Two unrelated facts get no bonus.
- +1 when the person emailed is the founder or CEO.

## Decision

- Score 5 or more: draft.
- Take the top 5 by score. Ties go to the freshest signal.
- Nobody at 5: no drafts today. Say so in the summary. That is a correct outcome.

## Cost limits per run

No more than 3 research runs and 15 email lookups. If Exa reports a combined cost above US$2, stop, draft nothing more and say why in the summary. The 17 Sep 2026 test cost US$0.025 per research run and US$0.02 per email found.
