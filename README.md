# Prospect: Adrian's daily prospecting skill for Claude

Every morning Claude uses Exa to find up to 5 Australian and New Zealand founder-led companies in Corient's ICP that have just raised money, posted a marketing hire, appointed a marketing leader or launched something. It finds the founder's email, writes each one a short personal email from Adrian, reviews it, and leaves it in Adrian's Gmail drafts with a numbered summary. Adrian reads the drafts, then tells Claude what to send. Nothing sends without him.

## Install (about 10 minutes, once)

You need a paid Claude plan (Pro, Max, Team or Enterprise) and the Claude desktop app for the daily schedule.

### 1. Turn on code execution

Claude > **Settings > Capabilities** > switch on **Code execution and file creation**. Skills need it. On a Team or Enterprise plan an owner switches on Skills for the organisation first.

### 2. Upload the skill

1. Download `prospect.zip` from this repo's latest release (or use the copy Amber emailed). Do not unzip it.
2. Claude > **Customize > Skills** > **+** > **Create skill** > **Upload a skill** > choose `prospect.zip`.
3. Make sure the **prospect** toggle is on.

### 3. Connect Gmail

**Customize > Connectors** > find **Gmail** > **Connect** > sign in with adrian@corient.com.au and allow access. Claude needs to read, draft, label and send.

### 4. Connect Exa

**Customize > Connectors** > search the directory for **Exa** and click **+**. If it is not listed, click **+ > Add custom connector**, name it `Exa`, URL `https://mcp.exa.ai/mcp`, then **Add**. Sign in to Exa when asked. The email lookups use Exa credits on that account; a normal run costs well under US$1.

### 5. Test it

Start a new chat and type:

> Run my prospect skill

It should say today's date, research, then report how many drafts are in Gmail. Open Gmail drafts and read the summary draft titled `prospects {date}`.

### 6. Schedule it daily

In the Claude desktop app, open a new task and type:

> Schedule a task that runs my prospect skill every weekday at 6:30am Perth time

Scheduled tasks run from the desktop app, so leave it installed and signed in.

If a scheduled run is missed, type "Run my prospect skill" any time.

## Daily use

1. Open Gmail. Read the `prospects {date}` summary and the drafts. Edit any draft directly in Gmail if you like.
2. In Claude, say one of:
   - `send all`
   - `send 1 and 3`
   - `edit 2: warmer opening, mention their Perth office`
   - `skip 4`
3. Claude sends exactly those drafts, relabels them, and confirms.

A company is never drafted twice within 180 days, and anyone already in your Gmail is skipped.

## What is in the skill

| File | What it does |
|---|---|
| `prospect/SKILL.md` | The run and send steps |
| `prospect/references/icp-and-scoring.md` | ICP, Exa query, signal windows, points, cost limits |
| `prospect/references/writing-the-email.md` | Voice, email shape, approved claims, review |
| `prospect/references/triggers.md` | Signal freshness rules (shared with Corient's outreach skill) |
| `prospect/references/personalisation-buckets.md` | Where a good first line comes from (shared) |
| `prospect/references/suppression.csv` | Do-not-contact domains (clients, open deals, opt-outs) |
| `prospect/scripts/lint_outreach.py` | Mechanical copy check every draft must pass |
| `golden/baseline.json` | 9 fixed test cases the skill must always get right |

## Updating (Amber)

```bash
./tools/package.sh
```

This refreshes the shared files from `~/.claude/skills/outreach`, checks the example email still passes the linter, and builds `dist/prospect.zip`. Commit, tag a release with the zip, and Adrian re-uploads it in **Customize > Skills** (delete the old one first).

`suppression.csv` ships empty. Fill it with client, open-deal and opt-out domains (one per line, `domain,source`) before the next release.
