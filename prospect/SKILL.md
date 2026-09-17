---
name: prospect
description: Adrian's daily Corient prospecting run. Uses Exa to find up to 5 Australian and New Zealand founder-led companies in Corient's ICP with a fresh buying signal (funding, a marketing hire, a new marketing leader, a launch), finds and verifies the founder's email, writes each a short personal email from Adrian, reviews it, and leaves it in Adrian's Gmail drafts with a numbered summary. Also handles "send all", "send 1 and 3", "edit 2", "skip 4" for those drafts. Use when Adrian says "run prospect", "find me prospects", "prospecting run", "send the prospect drafts", or a scheduled daily task runs it.
---

# Prospect

Two modes. **Run** finds prospects and writes Gmail drafts. **Send** sends the drafts Adrian names. A run never sends anything.

Needs the Gmail connector and the Exa connector. If either is missing, stop and say which one to connect (Customize > Connectors).

Today's date matters for every signal window. State it at the start of the run.

## Run

Read `references/icp-and-scoring.md` and `references/writing-the-email.md` first.

### 1. Load what to skip

- Search Gmail for threads labelled `Prospect/Ready`, `Prospect/Sent` or `Prospect/Skipped` from the last 180 days. Collect their recipient domains.
- Read `references/suppression.csv`.
- If the `Prospect/Ready`, `Prospect/Sent` and `Prospect/Skipped` labels do not exist, create them.

### 2. Research

One Exa `agent_run` per segment (B2B tech, B2C tech, premium consumer), effort low, using the query, exclusions and output schema in `icp-and-scoring.md`. Run them one after another; if a run reports it is still running, call `agent_run` again with its run ID until it completes.

### 3. Qualify and score

For each company, in order:

1. ICP check. Fail, drop.
2. Drop signals outside their window. No signal left, drop. Funding under 7 days old with nothing else: hold, mention in the summary as "recheck after {date}".
3. Suppression: domain in `suppression.csv` or the skip list from step 1, drop. Then search Gmail for the domain (`{domain}` across all mail including sent and drafts). Any existing thread, drop.
4. Decision maker must be the founder, CEO or a new marketing leader. If Exa returned someone else, drop.
5. Score. Keep 5 points and up, top 5 only.

### 4. Find and verify emails

One Exa `agent_run` email lookup for the survivors (see `icp-and-scoring.md`). Apply the domain-match rule. No verified email: move to "LinkedIn only".

### 5. Write and review

For each prospect with a verified email, write the email and review it exactly as `writing-the-email.md` says. Failed twice: "LinkedIn only".

### 6. Put it in Gmail

For each passing email:

- `create_draft` to the prospect with the subject and body (plain text, sign-off included).
- Apply the label `Prospect/Ready` to the draft's thread.

Then one summary draft to Adrian himself (adrian@corient.com.au), subject `prospects {d Mon}`, plain text:

```
{n} drafts ready in Gmail. Read them there, edit anything you like, then tell Claude "send all", "send 1 and 3", "edit 2: ...", or "skip 4".

1. {First Last}, {Title}, {Company} ({domain}), score {s}
   Why now: {signal summary}, {published date}
   Source: {source_url}
   Email: {address}

LinkedIn only (no verified email or failed review):
- {First Last}, {Company}, {LinkedIn URL}, reason: {reason}

Held for later: {company, recheck after date}
Dropped: {count} outside ICP or window, {count} already known
Exa cost this run: US${x}
```

Label the summary draft's thread `Prospect/Summary` (create the label if needed) so it is never mistaken for a prospect.

### 7. Report

End the run with one short message: how many drafts, who, and "say send all, send 1 and 3, edit 2, or skip 4". If nothing qualified, say that plainly. Zero drafts is a valid day.

## Send

Only when Adrian's own message says send, edit or skip. Never from a scheduled run.

1. Find the latest `Prospect/Summary` draft and read the numbered list. Match each number to its recipient address.
2. Find the draft for each address among drafts labelled `Prospect/Ready`. Re-read it with `get_draft` so any edit Adrian made in Gmail is what goes out.
3. Act:
   - **send all** or **send 1 and 3**: `send_message` with the draft ID. Relabel the thread `Prospect/Sent` and remove `Prospect/Ready`.
   - **edit 2: {instruction}**: rewrite, run the review again, `update_draft`, show Adrian the new version, and wait for "send 2".
   - **skip 4**: relabel `Prospect/Skipped`, remove `Prospect/Ready`, delete nothing.
4. A number that does not exist or a draft that has already gone: say so, send nothing for that number.
5. Confirm in one short message what was sent, to whom, and what is still waiting.

If Adrian says only "send" and it is unclear which drafts he means, ask once: "All {n}, or which numbers?"

## Never

- Send without Adrian naming the drafts in his own message.
- Draft to an email whose domain does not match the company.
- Invent a signal, a date, a quote, or anything about Adrian's life.
- Email anyone already in Adrian's Gmail or in `suppression.csv`.
- Exceed 5 drafts, 3 research runs, 15 email lookups or US$2 of Exa cost in a run.
