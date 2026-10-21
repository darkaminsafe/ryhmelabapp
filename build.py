"""
RHYME LAB - BUILD SCRIPT

Downloads the two word lists (if not already downloaded), keeps the common
one-syllable words, applies rules.py, and writes:
    rhyme-lab.html         the page you open on a computer (made from page-template.html)
    rhyme-lab-claude.html  the same page, shaped for publishing as a private Claude page
    word-list.txt          every word kept, with its labels
    test-results.txt       rhymes for the test words
    syllable-families.txt  all ending-sound families, biggest first

Run it with:  python build.py
"""

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections import defaultdict

import rules

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(HERE, "downloads")

SOURCES = {
    "cmudict.dict": "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict",
    "en_50k.txt": "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt",
}

TEST_WORDS = ["god", "life", "need", "hope", "hot", "hold", "down", "proud", "long", "dead", "remedy", "key", "homesick"]
TEST_MAX_RANK = 10000   # rhymes for the test words come from the 10,000 most common words


def download():
    os.makedirs(DOWNLOADS, exist_ok=True)
    for name, url in SOURCES.items():
        path = os.path.join(DOWNLOADS, name)
        if os.path.exists(path):
            continue
        print("Downloading", name, "...")
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as e:
            sys.exit("DOWNLOAD FAILED for %s (%s): %s" % (name, url, e))


def load_frequency():
    counts = {}
    with open(os.path.join(DOWNLOADS, "en_50k.txt"), encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2:
                counts[parts[0]] = int(parts[1])
    return counts


def load_cmu():
    """Returns a list of (spelling, sounds) - one item per pronunciation."""
    entries = []
    with open(os.path.join(DOWNLOADS, "cmudict.dict"), encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip()
            if not line:
                continue
            word, *sounds = line.split()
            word = word.split("(")[0]          # read(2) -> read
            entries.append((word, sounds))
    return entries


def frequency_of(word, counts):
    """How often the word appears. Short forms are estimated (see rules.py)."""
    if word in counts:
        return counts[word]
    if "'" in word and not word.startswith("'"):
        first, rest = word.split("'", 1)
        ending = "'" + rest
        if ending in rules.SHORT_FORM_ENDINGS or word in rules.ALLOWED_S_SHORT_FORMS:
            if first in counts and ending in counts:
                return min(counts[first], counts[ending])
    return None


def is_clean(word):
    if word in rules.NAMES_TO_DROP or word in rules.OFFENSIVE_WORDS_TO_DROP:
        return False
    if word in rules.FILLER_SOUNDS_TO_DROP or word in rules.FOREIGN_WORDS_TO_DROP:
        return False
    if word in rules.ABBREVIATIONS_TO_DROP:
        return False
    if word.startswith("'") and word not in rules.APOSTROPHE_START_WORDS_TO_KEEP:
        return False
    if len(word) == 1 and word not in rules.SINGLE_LETTER_WORDS_TO_KEEP:
        return False
    # letters and apostrophes only (no digits, dots, hyphens)
    return all(c.isalpha() or c == "'" for c in word) and any(c.isalpha() for c in word)


def build_words():
    counts = load_frequency()
    words = []
    for spelling, sounds in load_cmu():
        if rules.count_vowels(sounds) < 1 or not is_clean(spelling):
            continue
        freq = frequency_of(spelling, counts)
        if freq is None:
            continue
        words.append({"word": spelling, "sounds": rules.plain(sounds), "raw": sounds, "freq": freq})

    # Weak forms: drop an unstressed pronunciation if a stressed one exists
    if rules.DROP_WEAK_FORMS:
        has_stressed = {w["word"] for w in words if any(s[-1] in "12" for s in w["raw"])}
        words = [w for w in words
                 if w["word"] not in has_stressed or any(s[-1] in "12" for s in w["raw"])]

    # Main pronunciation only, except the real double words (see rules.py)
    seen_spelling, main_only = set(), []
    for w in words:
        if w["word"] in rules.REAL_DOUBLE_WORDS or w["word"] not in seen_spelling:
            main_only.append(w)
        seen_spelling.add(w["word"])
    words = main_only

    # Remove exact duplicate pronunciations of the same spelling
    seen, unique = set(), []
    for w in words:
        key = (w["word"], tuple(w["sounds"]))
        if key not in seen:
            seen.add(key)
            unique.append(w)

    # Rank by spelling (all pronunciations of a word share its rank)
    freq_of = {w["word"]: w["freq"] for w in unique}
    spellings = sorted(freq_of, key=lambda s: -freq_of[s])
    rank = {s: i + 1 for i, s in enumerate(spellings)}
    kept = [w for w in unique if rank[w["word"]] <= rules.PAGE_MAX_WORDS]
    for w in kept:
        w["rank"] = rank[w["word"]]
        rhyme, ending = rules.parse_long(w["raw"])
        w["vowel"], w["ending"] = rhyme[0][0], ending
        w["syl"] = rules.count_vowels(w["raw"])
        w["mouth"] = rules.mouth_of(w["vowel"])
        w["ends"] = rules.ends_on(w["raw"])
        w["sharp"] = rules.hard_or_sharp(w["raw"])
    kept.sort(key=lambda w: (w["rank"], w["sounds"]))

    # Rank among one-syllable words only (used for the text files)
    one = sorted({w["word"] for w in kept if w["syl"] == 1}, key=lambda x: rank[x])
    rank1 = {x: i + 1 for i, x in enumerate(one)}
    for w in kept:
        w["rank1"] = rank1.get(w["word"])

    # Words with two pronunciations get the sounds added to the name: read (R IY D)
    per_spelling = defaultdict(int)
    for w in kept:
        per_spelling[w["word"]] += 1
    for w in kept:
        w["label"] = w["word"] if per_spelling[w["word"]] == 1 else "%s (%s)" % (w["word"], " ".join(w["sounds"]))
    return kept


def labels(w):
    return "%s, ends on %s, %s" % (w["mouth"], w["ends"], w["sharp"])


def sample_rows(words, n_common=100, n_long=100):
    """The words used for the checks: the most common ones plus a fixed random set of longer words."""
    import random
    rows = words[:n_common]
    longer = [w for w in words if w["syl"] > 1]
    rows += random.Random(1).sample(longer, min(n_long, len(longer)))
    return rows


def check_symmetry(rows, cols):
    """Every rule must give the same category in both directions."""
    problems = 0
    for a in rows:
        for b in cols:
            if rules.classify(a["raw"], b["raw"])[0] != rules.classify(b["raw"], a["raw"])[0]:
                problems += 1
    return problems


def write_word_list(words):
    with open(os.path.join(HERE, "word-list.txt"), "w", encoding="utf-8") as f:
        f.write("RHYME LAB - ALL KEPT WORDS (%d entries, top %d one-syllable words)\n" % (len(words), rules.COMMON_CUTOFF))
        f.write("Most common first. Rank / word / sounds / Mouth / Ends on / Hard-Sharp\n\n")
        for w in words:
            f.write("%5d  %-22s %-16s %-7s %-10s %s\n" % (
                w["rank1"], w["label"], " ".join(w["sounds"]), w["mouth"], w["ends"], w["sharp"]))


GROUP_TITLES = {
    "twin": "TWIN",
    "near": "NEAR",
    "bendc": "BEND CANDIDATES (suggestions only)",
    "close": "CLOSE VOWEL (suggestions, check by ear)",
    "consm": "CONSONANT MATCH (suggestions: other vowel, same consonants)",
}


def rhymes_for(start, words):
    groups = {code: [] for code in GROUP_TITLES}
    for w in words:
        if w["word"] == start["word"]:
            continue
        code, reason, matched = rules.classify_full(start["raw"], w["raw"])
        if code:
            groups[code].append((w, reason, matched))
    for items in groups.values():
        items.sort(key=lambda t: (-t[2], t[0]["rank"]))   # most syllables matched first
    return groups


def write_test_results(words, all_words=None):
    lines = []
    lines.append("RHYME LAB - TEST RESULTS")
    lines.append("Rhymes from the %d most common words (all lengths). Most syllables matched first, then most common." % TEST_MAX_RANK)
    lines.append("Each rhyme shows: word, sounds, Mouth, Ends on, Hard/Sharp, and the reason.")
    lines.append("")
    for t in TEST_WORDS:
        starts = [w for w in (all_words or words) if w["word"] == t]
        if not starts:
            lines.append("=" * 70)
            lines.append("%s: NOT FOUND in the kept words" % t.upper())
            lines.append("")
            continue
        for s in starts:
            lines.append("=" * 70)
            lines.append("%s   sounds: %s   rhyme part: %s %s" % (
                s["label"].upper(), " ".join(s["sounds"]), s["vowel"], " ".join(s["ending"])))
            lines.append("    %s   (common rank %d)" % (labels(s), s["rank"]))
            lines.append("=" * 70)
            groups = rhymes_for(s, words)
            for cat, title in GROUP_TITLES.items():
                items = groups[cat]
                shown = items if cat in ("twin", "near") else items[:rules.MAX_BEND_CANDIDATES_SHOWN]
                extra = " - showing top %d" % len(shown) if len(shown) < len(items) else ""
                lines.append("")
                lines.append("  %s: %d%s" % (title, len(items), extra))
                if not items:
                    lines.append("    (none)")
                for w, reason, matched in shown:
                    lines.append("    %-20s %-14s %-36s %s" % (w["label"], " ".join(w["sounds"]), labels(w), reason))
            lines.append("")
            lines.append("  BEND and CONSONANT: empty here (only pairs you choose yourself on the page)")
            lines.append("")
    with open(os.path.join(HERE, "test-results.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_families(words):
    families = defaultdict(list)
    for w in words:
        families[(w["vowel"],) + tuple(w["ending"])].append(w)
    ordered = sorted(families.items(), key=lambda kv: (-len(kv[1]), kv[1][0]["rank"]))
    with open(os.path.join(HERE, "syllable-families.txt"), "w", encoding="utf-8") as f:
        f.write("RHYME LAB - SYLLABLE FAMILIES\n")
        f.write("Total families: %d   (from %d one-syllable words)\n" % (len(families), len(words)))
        f.write("A family = the vowel + everything after it. All words in a family are Twins.\n")
        f.write("Biggest first.  Sounds / most common example / number of words\n\n")
        for key, members in ordered:
            f.write("%-14s %-14s %d\n" % (" ".join(key), members[0]["label"], len(members)))


def page_settings():
    """The rule settings from rules.py, handed to the page."""
    return {
        "vowels": rules.VOWELS,
        "mouthGroups": rules.MOUTH_GROUPS,
        "vowelExamples": rules.VOWEL_EXAMPLES,
        "sharpSounds": rules.SHARP_SOUNDS,
        "twins": rules.VOICED_UNVOICED_TWINS,
        "families": rules.SOUND_FAMILIES,
        "nearAllowsOpen": rules.NEAR_ALLOWS_ADDING_TO_OPEN_ENDING,
        "extraBend": rules.EXTRA_SOUNDS_THAT_MAKE_BEND,
        "closeVowels": rules.CLOSE_VOWELS,
        "sameVowels": rules.SAME_VOWELS,
        "skippable": rules.SKIPPABLE_WEAK_VOWEL,
        "consMinShared": rules.CONSONANT_MATCH_MIN_SHARED,
        "consMaxExtra": rules.CONSONANT_MATCH_MAX_EXTRA,
        "starColours": rules.STAR_COLOURS,
        "commonCutoff": rules.COMMON_CUTOFF,
    }


def write_page(words):
    data = {
        "built": datetime.date.today().isoformat(),
        "settings": page_settings(),
        "words": [[w["label"], w["word"], " ".join(w["raw"]), w["rank"]] for w in words],
    }
    with open(os.path.join(HERE, "page-template.html"), encoding="utf-8") as f:
        page = f.read()
    page = page.replace("__RHYME_LAB_DATA__", json.dumps(data, separators=(",", ":")))
    with open(os.path.join(HERE, "rhyme-lab.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # The Claude version: Claude adds the outer page frame itself, so it gets
    # only the title, the style and the body.
    title = page[page.index("<title>"):page.index("</title>") + len("</title>")]
    style = page[page.index("<style>"):page.index("</style>") + len("</style>")]
    body = page[page.index("<body>") + len("<body>"):page.rindex("</body>")]
    with open(os.path.join(HERE, "rhyme-lab-claude.html"), "w", encoding="utf-8") as f:
        f.write(title + "\n" + style + "\n" + body)


CODE_LETTER = {"twin": "T", "near": "N", "bendc": "B", "close": "C", "consm": "M", None: "-"}


def cross_check(rows, cols):
    """
    The page has its own copy of the rules (for the browser). Run that copy
    with Node.js and compare it with rules.py (category AND syllables
    matched) for every row word against every column word.
    Skipped if Node.js is missing.
    """
    node = shutil.which("node")
    if not node:
        return "SKIPPED (Node.js not installed)"
    with open(os.path.join(HERE, "page-template.html"), encoding="utf-8") as f:
        page = f.read()
    block = page.split("// RULES-START")[1].split("// RULES-END")[0]
    script = block + """
const fs = require("fs");
const d = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const R = makeRules(d.settings);
const A = d.rows.map(R.parse), B = d.cols.map(R.parse);
const L = {twin: "T", near: "N", bendc: "B", close: "C", consm: "M"};
const out = A.map(a => B.map(b => { const [c, , m] = R.classify(a, b); return (L[c] || "-") + m; }).join(","));
fs.writeFileSync(process.argv[3], out.join("\\n"));
"""
    tmp = tempfile.mkdtemp()
    try:
        js, data_in, data_out = (os.path.join(tmp, n) for n in ("check.js", "in.json", "out.txt"))
        with open(js, "w") as f:
            f.write(script)
        with open(data_in, "w") as f:
            json.dump({"settings": page_settings(), "rows": [" ".join(w["raw"]) for w in rows],
                       "cols": [" ".join(w["raw"]) for w in cols]}, f)
        subprocess.run([node, js, data_in, data_out], check=True)
        with open(data_out) as f:
            page_rows = [r.split(",") for r in f.read().split("\n")]
        problems = []
        for i, a in enumerate(rows):
            for j, b in enumerate(cols):
                code, _, matched = rules.classify_full(a["raw"], b["raw"])
                py = CODE_LETTER[code] + str(matched)
                if page_rows[i][j] != py:
                    problems.append("%s / %s: rules.py says %s, page says %s" % (a["label"], b["label"], py, page_rows[i][j]))
        if problems:
            return "%d PROBLEMS, for example: %s" % (len(problems), "; ".join(problems[:5]))
        return "OK (%d pairs compared)" % (len(rows) * len(cols))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    download()
    page_words = build_words()
    words = [w for w in page_words if w["syl"] == 1 and w["rank1"] <= rules.COMMON_CUTOFF]
    common = [w for w in page_words if w["rank"] <= TEST_MAX_RANK]
    rows = sample_rows(page_words)
    problems = check_symmetry(rows[:40] + rows[-40:], common)
    write_word_list(words)
    write_test_results(common, page_words)
    write_families(words)
    write_page(page_words)
    print("Kept %d entries (%d words) for the text files." % (len(words), len({w['word'] for w in words})))
    print("The page holds %d entries (%d words)." % (len(page_words), len({w['word'] for w in page_words})))
    print("Symmetry check:", "OK" if problems == 0 else "%d PROBLEMS" % problems)
    check = cross_check(rows, common)
    print("Page rules vs rules.py:", check)
    print("Wrote rhyme-lab.html, rhyme-lab-claude.html, word-list.txt, test-results.txt, syllable-families.txt")
    if "PROBLEMS" in check:
        sys.exit("STOPPED: the page and rules.py disagree. Do not use this rhyme-lab.html.")


if __name__ == "__main__":
    main()
