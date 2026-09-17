# Writing the email

The email is from Adrian Huber, CEO and founder of Corient, to a founder he has never met. Its only job is to earn a reply. It is a note from one founder to another who noticed something real, not a pitch.

## Adrian's voice

Before the first draft of a run, read 10 of Adrian's own recent sent emails to people outside Corient (Gmail search `in:sent -to:corient.com.au newer_than:180d`, skip calendar replies and one-liners). Note how he opens, how long his sentences run, the words he reaches for, how he signs off, and where his humour or warmth shows. Write like that.

- Personality comes from those emails, never from invention. If his real mail shows no humour, the email carries none.
- Professional, warm, direct. Plain Australian English.
- If fewer than 5 usable sent emails exist, write in a plain, warm founder voice and say "voice examples thin" in the summary.

## Shape

Subject: 1 to 4 lowercase words that read like an internal note, for example `the marketing hire` or `after the raise`. Never `Re:` or `Fwd:`.

Body: 50 to 80 words, excluding the sign-off. Four moves, in order:

1. **Why today.** Open on the signal, argued, not reported. Say what it probably means for them, framed as a hunch. Never open with "I", "Congrats" or a compliment.
2. **A human line.** One short sentence of Adrian: a light observation or a bit of warmth in his own register.
3. **The offer, one sentence, second last.** Corient embeds a CMO with a pod of specialists: a marketing team for the cost of one hire. Rephrase to fit the signal (for a marketing hire: they are pricing one hire right now). Never the price, never the name of the growth system, never a list of services.
4. **One question.** A curious question about their plan, not a meeting request. No "15 minutes", no "book a call", no calendar link.

Sign-off, exactly, on its own lines:

```
Adrian
Corient · ABN 50 671 799 081 · reply "stop" and I won't follow up
```

## Hard rules

- No links, no attachments, no images, no tracking.
- No dashes of any kind (em-dash or en-dash). Use commas and full stops.
- No emojis.
- Never state a fact about their internal setup (their spend, their stack, their team's skills, their results). Published facts and clearly marked hunches only.
- Approved claims only: the embedded CMO plus pod of specialists, "a marketing team for the cost of one hire", and "a proprietary evidence-gated growth system" (method description). Anything else about Corient's results, clients or numbers is out.
- No blocklist words: delve, hone, garner, leverage, unlock, unleash, dive in, paradigm, robust, synergy, seamless, transformative, best practices.
- No "I noticed", "I came across", "hope this finds you well", "just reaching out", "circling back".
- No "it's not X, it's Y" constructions.

## Worked shape (structure only, not Adrian's words)

```
Subject: the first marketing hire

Hi Sam, a seed round and a Head of Growth ad in the same month usually means the board wants a number by Christmas. That's a lot to put on one person. {Adrian's human line}. We embed a CMO with a pod of specialists, so you get a whole marketing team for about the cost of that one hire. What does the new hire need to prove in their first 90 days?

Adrian
Corient · ABN 50 671 799 081 · reply "stop" and I won't follow up
```

## Review (every draft, before it reaches Gmail)

1. **Mechanical.** Save the draft (subject line plus body, no sign-off) to a file and run:

   `python3 scripts/lint_outreach.py --channel email --first-touch --file draft.md`

   Exit 0 passes. Any FAIL must be fixed. WARNs are allowed.

   If code execution is unavailable, check by hand: subject 1 to 4 lowercase words; body 80 words or fewer; no dashes, links or emojis; no blocklist word or banned phrase; exactly one question; more "you/your" than "I/my"; first sentence does not start with "I".

2. **Three reviews.** Score the draft three times, each time taking a different lens, reading only the draft and the prospect record:
   - **Fit.** The signal is real, dated inside its window, belongs to this company, and the opening argues from it.
   - **Voice.** It reads like Adrian's sent emails, warm and specific, and would not embarrass him if forwarded.
   - **Claims.** Only approved claims, nothing asserted about their internal setup, one question, the offer line is one sentence and not a pitch.

   All three must pass. A failed draft gets one rewrite against the notes. If it fails again, drop it and list the person as "LinkedIn only" with the reason.
