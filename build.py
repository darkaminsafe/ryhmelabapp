"""
RHYME LAB - BUILD SCRIPT (Step 1)

Downloads the two word lists (if not already downloaded), keeps the common
one-syllable words, applies rules.py, and writes:
    word-list.txt          every word kept, with its labels
    test-results.txt       rhymes for the test words
    syllable-families.txt  all ending-sound families, biggest first

Run it with:  python build.py
"""

import os
import sys
import urllib.request
from collections import defaultdict

import rules

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(HERE, "downloads")

SOURCES = {
    "cmudict.dict": "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict",
    "en_50k.txt": "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt",
}

TEST_WORDS = ["god", "life", "need", "hope", "hot", "hold", "down", "proud", "long", "dead"]


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
        if rules.count_vowels(sounds) != 1 or not is_clean(spelling):
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
    kept = [w for w in unique if rank[w["word"]] <= rules.COMMON_CUTOFF]
    for w in kept:
        w["rank"] = rank[w["word"]]
        start, vowel, ending = rules.split_word(w["raw"])
        w["vowel"], w["ending"] = vowel, ending
        w["mouth"] = rules.mouth_of(vowel)
        w["ends"] = rules.ends_on(w["raw"])
        w["sharp"] = rules.soft_or_sharp(w["raw"])
    kept.sort(key=lambda w: (w["rank"], w["sounds"]))

    # Words with two pronunciations get the sounds added to the name: read (R IY D)
    per_spelling = defaultdict(int)
    for w in kept:
        per_spelling[w["word"]] += 1
    for w in kept:
        w["label"] = w["word"] if per_spelling[w["word"]] == 1 else "%s (%s)" % (w["word"], " ".join(w["sounds"]))
    return kept


def labels(w):
    return "%s, ends on %s, %s" % (w["mouth"], w["ends"], w["sharp"])


def check_symmetry(words):
    """Every rule must give the same answer in both directions."""
    by_vowel = defaultdict(list)
    for w in words:
        by_vowel[w["vowel"]].append(w)
    problems = 0
    for group in by_vowel.values():
        for a in group:
            for b in group:
                if rules.compare(a["raw"], b["raw"])[0] != rules.compare(b["raw"], a["raw"])[0]:
                    problems += 1
    return problems


def write_word_list(words):
    with open(os.path.join(HERE, "word-list.txt"), "w", encoding="utf-8") as f:
        f.write("RHYME LAB - ALL KEPT WORDS (%d entries, top %d one-syllable words)\n" % (len(words), rules.COMMON_CUTOFF))
        f.write("Most common first. Rank / word / sounds / Mouth / Ends on / Soft-Sharp\n\n")
        for w in words:
            f.write("%5d  %-22s %-16s %-7s %-10s %s\n" % (
                w["rank"], w["label"], " ".join(w["sounds"]), w["mouth"], w["ends"], w["sharp"]))


def rhymes_for(start, words):
    groups = {"Twin": [], "Near": [], "Bend candidate": []}
    for w in words:
        if w["word"] == start["word"]:
            continue
        cat, reason = rules.compare(start["raw"], w["raw"])
        if cat:
            groups[cat].append((w, reason))
    return groups


def write_test_results(words):
    lines = []
    lines.append("RHYME LAB - TEST RESULTS")
    lines.append("Words checked: %d one-syllable words (top %d). Most common first in every list." % (len(words), rules.COMMON_CUTOFF))
    lines.append("Each rhyme shows: word, sounds, Mouth, Ends on, Soft/Sharp, and the reason.")
    lines.append("")
    for t in TEST_WORDS:
        starts = [w for w in words if w["word"] == t]
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
            for cat in ["Twin", "Near", "Bend candidate"]:
                items = groups[cat]
                shown = items[:rules.MAX_BEND_CANDIDATES_SHOWN] if cat == "Bend candidate" else items
                title = {"Twin": "TWIN", "Near": "NEAR", "Bend candidate": "BEND CANDIDATES (suggestions only)"}[cat]
                extra = " - showing top %d" % len(shown) if len(shown) < len(items) else ""
                lines.append("")
                lines.append("  %s: %d%s" % (title, len(items), extra))
                if not items:
                    lines.append("    (none)")
                for w, reason in shown:
                    lines.append("    %-20s %-14s %-36s %s" % (w["label"], " ".join(w["sounds"]), labels(w), reason))
            lines.append("")
            lines.append("  BEND: empty (only pairs you choose yourself, from Step 3)")
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


def main():
    download()
    words = build_words()
    problems = check_symmetry(words)
    write_word_list(words)
    write_test_results(words)
    write_families(words)
    print("Kept %d entries (%d words)." % (len(words), len({w['word'] for w in words})))
    print("Symmetry check:", "OK" if problems == 0 else "%d PROBLEMS" % problems)
    print("Wrote word-list.txt, test-results.txt, syllable-families.txt")


if __name__ == "__main__":
    main()
