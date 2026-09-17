"""
lint_outreach — mechanical gate for cold outreach copy.

Every rule here is already a number in
`reference/clients/corient/outreach-sequencing-playbook.md`. This module turns those
numbers into a check that runs, so the drafter cannot forget them and cannot grade its
own homework.

FAIL blocks handover. WARN is advisory: it names a risk the playbook measures but does
not treat as disqualifying.

Pure stdlib. No network, no dependencies, no writes.

CLI:
    python3 lint_outreach.py --channel email --file draft.md
    cat draft.md | python3 lint_outreach.py --channel linkedin
    python3 lint_outreach.py --channel linkedin --file draft.md --json

Exit codes: 0 clean (WARNs allowed), 1 at least one FAIL, 2 bad invocation or empty input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

# --- rules lifted from the playbook -----------------------------------------

# Playbook section 3: "The 13-word blocklist".
BLOCKLIST = [
    "delve", "hone", "garner", "leverage", "unlock", "unleash", "dive in",
    "paradigm", "robust", "synergy", "seamless", "transformative", "best practices",
]

# Playbook section 3 + the house overrides. Each entry is (label, regex).
AI_TELLS = [
    ("hope-this-finds-you", r"(?i)hope (?:this|you)\b[^.?!]{0,40}\b(?:finds you well|are well|is well)"),
    ("i-noticed", r"(?i)\bI (?:noticed|came across|stumbled upon|happened to see)\b"),
    ("just-bumping", r"(?i)\b(?:just )?(?:bumping|circling back|following up on my|touching base|checking in on)\b"),
    ("compliment-opener", r"(?i)^\s*(?:love|loving|impressive|amazing|huge fan|big fan|congrats on the amazing)\b"),
    ("reaching-out-throat-clear", r"(?i)\bI (?:wanted|just wanted|am reaching out|wanted to reach out)\b"),
    ("at-your-convenience", r"(?i)\bat your earliest convenience\b"),
    ("quick-question-subject", r"(?i)^\s*quick question\s*$"),
]

# Playbook: "no contrast constructions, anywhere". Negate-then-affirm only. A plain
# comparative ("easier shown than described") is not this pattern and must not trip.
CONTRAST_SCAFFOLDS = [
    ("not-x-but-y", r"(?i)\b(?:it'?s|this is|that'?s|they'?re|we'?re|you'?re)\s+not\s+[^.?!]{2,60}?,?\s+(?:it'?s|this is|that'?s|they'?re|we'?re|you'?re)\s"),
    ("isnt-x-its-y", r"(?i)\b(?:isn'?t|aren'?t|wasn'?t)\s+[^.?!]{2,60}?,\s*(?:it'?s|they'?re|that'?s)\s"),
    ("not-just-but", r"(?i)\bnot (?:just|only|merely|simply)\b[^.?!]{2,60}?\bbut\b"),
    ("never-was-the", r"(?i)\b(?:was|were) never the\b[^.?!]{2,60}?\bis the\b"),
    ("less-about-more-about", r"(?i)\bless about\b[^.?!]{2,60}?\bmore about\b"),
]

CTA_PHRASES = [
    r"(?i)\bdo you have\s+\d+\s*(?:minutes|mins)\b",
    r"(?i)\b(?:book|grab|schedule|set up|lock in)\s+(?:a|some)\b",
    r"(?i)\b(?:shall|should)\s+we\s+(?:find|grab|book)\b",
    r"(?i)\bworth\s+a\s+(?:chat|call|look|conversation)\b",
    r"(?i)\bopen to\b[^.?!]{0,40}\b(?:call|chat|intro|conversation)\b",
    r"(?i)\bhere'?s (?:my|the) (?:calendar|link|booking)\b",
]

TRACKING_PARAMS = ["utm_", "fbclid", "gclid", "mc_eid", "?ref=", "&ref=", "mkt_tok"]

# Length bands. FAIL above the ceiling (the measured penalty is in long copy). Below the
# floor is a WARN: the house's own approved live sequence runs shorter than the vendor
# floor and outperforms, so short copy is a flag, not a defect.
LENGTH_BANDS = {
    "email": {"floor": 50, "ceiling": 80, "unit": "words"},
    "linkedin": {"floor": 45, "ceiling": 90, "unit": "words"},
    "connection-note": {"floor": 0, "ceiling": 300, "unit": "chars"},
}

CHANNELS = tuple(LENGTH_BANDS)

VARIABLE_TOKEN = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")
URL = re.compile(r"https?://\S+|\bwww\.\S+")
SENTENCE_SPLIT = re.compile(r"(?<=[.?!])\s+")


# --- helpers -----------------------------------------------------------------

def normalise(text: str) -> str:
    """Variable tokens render as one word each. Count them as one word, not as noise."""
    return VARIABLE_TOKEN.sub("Name", text)


def split_subject(text: str, channel: str) -> tuple[str | None, str]:
    """Pull a leading `Subject:` line off email copy. Returns (subject, body)."""
    if channel != "email":
        return None, text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body = "\n".join(lines[:i] + lines[i + 1:]).strip()
            return subject, body
    return None, text


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9'’]+", normalise(text))


def sentences(text: str) -> list[str]:
    parts = [s.strip() for s in SENTENCE_SPLIT.split(normalise(text).strip()) if s.strip()]
    return parts


def syllables(word: str) -> int:
    word = word.lower().strip("'’")
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ee", "ye")) and count > 1:
        count -= 1
    return max(count, 1)


def fk_grade(text: str) -> float | None:
    w, s = words(text), sentences(text)
    if not w or not s:
        return None
    syl = sum(syllables(x) for x in w)
    return 0.39 * (len(w) / len(s)) + 11.8 * (syl / len(w)) - 15.59


def has_emoji(text: str) -> list[str]:
    found = []
    for ch in text:
        if ch in "‍️":
            continue
        cat = unicodedata.category(ch)
        if cat == "So" or (0x1F000 <= ord(ch) <= 0x1FAFF):
            found.append(ch)
    return found


# --- checks ------------------------------------------------------------------

class Result:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, check: str, status: str, detail: str, hint: str = "") -> None:
        self.rows.append({"check": check, "status": status, "detail": detail, "hint": hint})

    @property
    def failed(self) -> bool:
        return any(r["status"] == "FAIL" for r in self.rows)


def check_punctuation(body: str, subject: str | None, res: Result) -> None:
    whole = f"{subject or ''}\n{body}"
    em = whole.count("—")
    en = whole.count("–")
    emoji = has_emoji(whole)
    if em or en or emoji:
        bits = []
        if em:
            bits.append(f"{em} em-dash")
        if en:
            bits.append(f"{en} en-dash")
        if emoji:
            bits.append(f"emoji {' '.join(emoji)}")
        res.add("punctuation", "FAIL", ", ".join(bits),
                "Replace dashes with a full stop, comma or colon. Delete emoji.")
    else:
        res.add("punctuation", "PASS", "no em-dash, en-dash or emoji")


def check_blocklist(body: str, subject: str | None, res: Result) -> None:
    whole = f"{subject or ''}\n{body}"
    hits = [w for w in BLOCKLIST if re.search(rf"(?i)\b{re.escape(w)}\b", whole)]
    if hits:
        res.add("blocklist", "FAIL", ", ".join(hits),
                "Replace each with a plain word, a number, or an outcome.")
    else:
        res.add("blocklist", "PASS", "none of the 13 blocklist words")


def check_ai_tells(body: str, subject: str | None, res: Result) -> None:
    whole = f"{subject or ''}\n{body}"
    hits = [label for label, pat in AI_TELLS if re.search(pat, whole, re.MULTILINE)]
    if hits:
        res.add("ai-tells", "FAIL", ", ".join(hits),
                "Delete the phrase. Open on the recipient, not on yourself.")
    else:
        res.add("ai-tells", "PASS", "no measured AI-tell phrases")


def check_contrast(body: str, res: Result) -> None:
    hits = [label for label, pat in CONTRAST_SCAFFOLDS if re.search(pat, body)]
    if hits:
        res.add("contrast-scaffold", "FAIL", ", ".join(hits),
                "State the affirmative directly. Drop the negation that does no work.")
    else:
        res.add("contrast-scaffold", "PASS", "no negate-then-affirm construction")


def check_length(body: str, channel: str, res: Result) -> None:
    band = LENGTH_BANDS[channel]
    size = len(body.strip()) if band["unit"] == "chars" else len(words(body))
    label = f"{size} {band['unit']}"
    if size > band["ceiling"]:
        res.add("length", "FAIL", f"{label} (ceiling {band['ceiling']})",
                "Cut to one idea and one ask. Long copy is the measured reply killer.")
    elif size < band["floor"]:
        res.add("length", "WARN", f"{label} (floor {band['floor']})",
                "Under the vendor floor. Fine if every word earns its place.")
    else:
        res.add("length", "PASS", f"{label} (band {band['floor']} to {band['ceiling']})")


def check_subject(subject: str | None, channel: str, res: Result) -> None:
    if channel != "email":
        return
    if subject is None:
        res.add("subject", "FAIL", "no `Subject:` line found",
                "Email drafts must carry a subject line for the gate to check it.")
        return
    if re.match(r"(?i)^\s*(re|fwd|fw)\s*:", subject):
        res.add("subject", "FAIL", "fake Re:/Fwd: prefix",
                "Remove it. Replies drop to ~3% and it breaches CAN-SPAM.")
        return
    sw = subject.split()
    problems = []
    if not 1 <= len(sw) <= 4:
        problems.append(f"{len(sw)} words (want 1 to 4)")
    if subject != subject.lower():
        problems.append("not lowercase")
    if problems:
        res.add("subject", "FAIL", "; ".join(problems),
                "1 to 4 lowercase words that look like an internal note.")
    else:
        res.add("subject", "PASS", f'"{subject}"')


def check_pronouns(body: str, res: Result) -> None:
    you = len(re.findall(r"(?i)\b(?:you|your|you'?re|you'?ve|yours)\b", body))
    i = len(re.findall(r"\bI\b|\bI'?(?:m|ve|d|ll)\b|\b(?:my|mine)\b", body))
    first = sentences(body)[0] if sentences(body) else ""
    problems = []
    if you < i:
        problems.append(f"you={you} vs I={i}")
    if re.match(r"^\s*I\b", first):
        problems.append("first line opens with I")
    if problems:
        res.add("pronouns", "FAIL", "; ".join(problems),
                "Rewrite the sentence around them. Never open on I.")
    else:
        res.add("pronouns", "PASS", f"you={you}, I={i}")


def check_links(body: str, first_touch: bool, res: Result) -> None:
    links = URL.findall(body)
    if first_touch and links:
        res.add("links", "FAIL", f"{len(links)} link(s) in a first touch",
                "No links in message 1. They cost placement and buy nothing.")
        return
    if len(links) > 1:
        res.add("links", "FAIL", f"{len(links)} links (max 1)", "Keep one link.")
        return
    tracked = [p for link in links for p in TRACKING_PARAMS if p in link]
    if tracked:
        res.add("links", "FAIL", f"tracking params: {', '.join(sorted(set(tracked)))}",
                "Strip tracking. Open-tracking pixels stay off.")
        return
    res.add("links", "PASS", f"{len(links)} link(s), no tracking")


def check_asks(body: str, res: Result) -> None:
    asks = []
    for s in sentences(body):
        if s.rstrip().endswith("?") or any(re.search(p, s) for p in CTA_PHRASES):
            asks.append(s)
    if len(asks) > 1:
        res.add("asks", "FAIL", f"{len(asks)} asks: " + " | ".join(a[:45] for a in asks),
                "One ask per message. Competing asks halve the reply.")
    else:
        res.add("asks", "PASS", f"{len(asks)} ask")


def check_readability(body: str, res: Result) -> None:
    grade = fk_grade(body)
    if grade is None:
        res.add("readability", "WARN", "not measurable")
        return
    if grade > 5.0:
        long_ones = [s[:60] for s in sentences(body) if len(words(s)) > 20]
        detail = f"grade {grade:.1f} (want <= 5.0)"
        if long_ones:
            detail += "; long: " + " | ".join(long_ones)
        res.add("readability", "WARN", detail,
                "Cut the commas. One clause per sentence.")
    else:
        res.add("readability", "PASS", f"grade {grade:.1f}")


def check_rule_of_three(body: str, res: Result) -> None:
    if re.search(r"(?i)[^.?!]+,[^.?!,]+,\s*and\s+[^.?!]+[.?!]", body):
        res.add("rule-of-three", "WARN", "three-item list in body copy",
                "Two items or four reads human. Three reads written.")
    else:
        res.add("rule-of-three", "PASS", "no rule-of-three list")


def check_variance(body: str, res: Result) -> None:
    lens = [len(words(s)) for s in sentences(body)]
    if len(lens) < 3:
        res.add("sentence-variance", "PASS", f"{len(lens)} sentence(s), variance n/a")
        return
    mean = sum(lens) / len(lens)
    if mean == 0:
        res.add("sentence-variance", "PASS", "empty")
        return
    sd = (sum((x - mean) ** 2 for x in lens) / len(lens)) ** 0.5
    cv = sd / mean
    if cv < 0.15:
        res.add("sentence-variance", "WARN", f"cv {cv:.2f}, lengths {lens}",
                "Uniform sentence length reads machine-made. Break one short.")
    else:
        res.add("sentence-variance", "PASS", f"cv {cv:.2f}")


def lint(text: str, channel: str, first_touch: bool) -> Result:
    res = Result()
    subject, body = split_subject(text, channel)
    check_punctuation(body, subject, res)
    check_blocklist(body, subject, res)
    check_ai_tells(body, subject, res)
    check_contrast(body, res)
    check_length(body, channel, res)
    check_subject(subject, channel, res)
    check_pronouns(body, res)
    check_links(body, first_touch, res)
    check_asks(body, res)
    check_readability(body, res)
    check_rule_of_three(body, res)
    check_variance(body, res)
    return res


# --- cli ---------------------------------------------------------------------

def render(res: Result, channel: str) -> str:
    width = max(len(r["check"]) for r in res.rows)
    lines = [f"outreach lint: {channel}", ""]
    for r in res.rows:
        lines.append(f"  {r['status']:<4}  {r['check']:<{width}}  {r['detail']}")
    hints = [r for r in res.rows if r["hint"] and r["status"] in ("FAIL", "WARN")]
    if hints:
        lines += ["", "repairs:"]
        for r in hints:
            lines.append(f"  {r['check']}: {r['hint']}")
    fails = sum(1 for r in res.rows if r["status"] == "FAIL")
    warns = sum(1 for r in res.rows if r["status"] == "WARN")
    lines += ["", f"{fails} FAIL, {warns} WARN"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Mechanical gate for cold outreach copy")
    p.add_argument("--channel", required=True, choices=CHANNELS)
    p.add_argument("--file", help="path to the draft; omit to read stdin")
    p.add_argument("--first-touch", action="store_true",
                   help="message 1 of a sequence: no links allowed at all")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)

    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("empty input: nothing to lint", file=sys.stderr)
        return 2

    res = lint(text, args.channel, args.first_touch)
    if args.json:
        print(json.dumps({"channel": args.channel, "checks": res.rows,
                          "failed": res.failed}, indent=2))
    else:
        print(render(res, args.channel))
    return 1 if res.failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
