"""
RHYME LAB - ALL THE RULES IN ONE PLACE
======================================

This file holds every rule and setting Rhyme Lab uses. If you want a rule
changed, point to the section below (for example "MOUTH GROUPS") and say
what you want.

How sounds are written
----------------------
We use the sound codes from the CMU Pronouncing Dictionary (American English).
Every word is a list of sounds. Example:
    life  = L AY F        (L sound, the vowel "AY" as in "my", F sound)
    need  = N IY D
    don't = D OW N T

Vowels (15 of them):
    AA  hot, god      AE  cat, map      AH  cup, love     AO  long, law
    AW  down, now     AY  life, my      EH  dead, bed     ER  bird, her
    EY  day, say      IH  sit, big      IY  need, team    OW  hope, go
    OY  boy, voice    UH  book, good    UW  you, blue

Each one-syllable word is split into three parts:
    START   = the sounds before the vowel   (life -> L)
    VOWEL   = the one vowel sound           (life -> AY)
    ENDING  = the sounds after the vowel    (life -> F)
The "rhyme part" is VOWEL + ENDING          (life -> AY F)
"""

# ---------------------------------------------------------------------------
# 1. SETTINGS
# ---------------------------------------------------------------------------

# How many of the most common one-syllable words to keep.
# (Counted AFTER removing names, letters, etc. Most common first.)
COMMON_CUTOFF = 3000

# How many words the web page holds, so the "how rare" slider can go
# above the cutoff. (If fewer one-syllable words exist, it holds all of them.)
# The slider starts at COMMON_CUTOFF.
PAGE_MAX_WORDS = 50000

# How many suggestions (Bend candidates, Close vowel, Consonant match)
# to list per word in test-results.txt. The web page shows all of them.
MAX_BEND_CANDIDATES_SHOWN = 30

# Star colours on the page (P1 = best).
STAR_COLOURS = {
    1: "#ffd84a",   # yellow
    2: "#ff9b3d",   # orange
    3: "#e2cfa6",   # beige
}


# ---------------------------------------------------------------------------
# 2. VOWELS AND MOUTH GROUPS
# ---------------------------------------------------------------------------
# Mouth looks ONLY at the vowel.

MOUTH_GROUPS = {
    "Open":   ["AA", "AE", "AY", "AW", "AH"],        # not, map, life, now, cup
    "Slight": ["EY", "OW", "EH", "ER", "OY", "AO"],  # day, go, bed, bird, boy, law
    "Closed": ["IY", "IH", "UW", "UH"],              # need, sit, you, book
}

VOWELS = [v for group in MOUTH_GROUPS.values() for v in group]

# One example word per vowel, used on the page ("the 'god' vowel").
VOWEL_EXAMPLES = {
    "AA": "god", "AE": "cat", "AH": "cup", "AO": "law", "AW": "down",
    "AY": "life", "EH": "bed", "ER": "bird", "EY": "day", "IH": "sit",
    "IY": "need", "OW": "hope", "OY": "boy", "UH": "book", "UW": "you",
}


# ---------------------------------------------------------------------------
# 3. HARD / SHARP
# ---------------------------------------------------------------------------
# A word is SHARP if ANY of its sounds (start to end) is in this list.
# Otherwise it is HARD. This works on sounds, never spelling:
#   city (S IH T IY)  -> Sharp, because the C sounds like S
#   cat  (K AE T)     -> Hard,  because the C sounds like K
#   box  (B AA K S)   -> Sharp, the X contains an S sound

SHARP_SOUNDS = [
    "S",   # street, star, city
    "Z",   # zoo, his
    "SH",  # shine
    "ZH",  # vision, beige
    "CH",  # cheese
    "JH",  # jail, gentle (soft G)
]


# ---------------------------------------------------------------------------
# 4. SOUND FAMILIES (used by the Near rule)
# ---------------------------------------------------------------------------

# Voiced / unvoiced twins: the mouth does the same thing, only the voice
# is switched on or off. Example: D (voice on) and T (voice off).
VOICED_UNVOICED_TWINS = [
    ("B", "P"),
    ("D", "T"),
    ("G", "K"),
    ("V", "F"),
    ("DH", "TH"),   # DH = "this", TH = "thin"
    ("Z", "S"),
    ("ZH", "SH"),
    ("JH", "CH"),
]

# Sound families: sounds made in a similar way.
SOUND_FAMILIES = {
    "stops":      ["P", "B", "T", "D", "K", "G"],                 # air is stopped
    "nasals":     ["M", "N", "NG"],                                # sound through the nose
    "fricatives": ["F", "V", "TH", "DH", "S", "Z", "SH", "ZH", "HH"],  # hissing / rubbing air
    "affricates": ["CH", "JH"],                                    # stop + hiss (cheese, jail)
    "liquids":    ["L", "R"],                                      # flowing sounds
    "glides":     ["W", "Y"],
}


# ---------------------------------------------------------------------------
# 5. THE RHYME RULES
# ---------------------------------------------------------------------------
# Every pair is judged on its own (no chaining), and every rule is
# symmetric: if A is Twin to B, then B is Twin to A.
#
# If the VOWELS are different -> no rhyme, the word is not listed.
#
# TWIN: same vowel AND identical ending.
#       Words that sound exactly the same also count (die / dye).
#
# NEAR: same vowel, and the ending differs by ONE small change:
#       a) one sound swapped for its voiced/unvoiced twin  (need / street: D vs T)
#       b) one sound swapped for one from the same family  (hot / hop: T vs P, both stops)
#       c) one sound added or dropped                       (fat / fast: extra S)
#
# BEND CANDIDATE: same vowel, any other ending. Only a suggestion for you.
# BEND: starts empty. Only pairs YOU choose (comes in Step 3).

# OPEN ENDINGS: a word that ends on the vowel (cry, lie, ma) is Near to
# every word with the same vowel colour plus ANY consonants after it:
#   cry / crime (+M), line (+N), times (+MZ), grind (+ND), light (+T)
#   ma / god (+D)
# You chose True. Set to False to make those Bend candidates instead.
# (An ending that starts with R stays a Bend candidate, see below.)
NEAR_ALLOWS_ADDING_TO_OPEN_ENDING = True

# If the one added or dropped sound (rule c) is one of these, the pair is
# a Bend candidate instead of Near.
# You chose: an extra R is a Bend candidate (god / guard, god / card).
EXTRA_SOUNDS_THAT_MAKE_BEND = ["R"]

# VOWEL COLOURS: how YOU hear the vowels (a Latvian ear: A E I O U, long
# and short). Rhymes compare COLOURS, not the dictionary's 15 vowels.
# Two vowels with the same colour count as the same vowel everywhere.
VOWEL_COLOURS = {
    "AA": "Ā",   # long open a:  god = "gād", hot, father
    "AE": "Ā",   #               mad = "mād", cat, happy
    "AO": "Ā",   #               law, flawed, caught
    "AH": "A",   # short a:      mud = "mad", cup, sun, money = "manī"
    "EH": "E",   # bed, dead
    "ER": "E",   # bird, her
    "IY": "I",   # key, see, need
    "IH": "I",   # sit, big
    "OW": "O",   # go, hope, hold
    "UW": "U",   # you, blue
    "UH": "U",   # book, good
    "AY": "AI",  # glide a > i: life, my, pride
    "AW": "AU",  # glide a > u: down, now, proud
    "EY": "EI",  # glide e > i: day, say, pain
    "OY": "OI",  # glide o > i: boy, voice
}

# When BOTH words are longer than one syllable, these colours count as the
# same (money "manī" / happy "hapī"). As soon as one of the two words has
# one syllable, they stay different (god "gād" / mud "mad" / nomad).
LONGER_WORDS_SAME_COLOURS = [
    ("Ā", "A"),
]

# CLOSE VOWEL (a suggestion pool): colours that are close but not the same.
# A pair shows up there when the colours are listed together below AND the
# endings are Twin- or Near-close (god / mud).
CLOSE_COLOURS = [
    ("Ā", "A"),
]

# CONSONANT MATCH (a suggestion pool, one-syllable words only): DIFFERENT vowel, but the same
# consonant sounds before and after it ("the consonant frame").
#   god (G . D)  ->  good (G . D), guide (G . D)
# At least this many consonants must be shared:
CONSONANT_MATCH_MIN_SHARED = 2
# How many extra (or missing) consonants are allowed, anywhere:
#   god / gold (extra L), god / grade (extra R), hold / hole (missing D)
CONSONANT_MATCH_MAX_EXTRA = 1


# ---------------------------------------------------------------------------
# 6. WHICH WORDS ARE KEPT
# ---------------------------------------------------------------------------

# Short forms (don't, I'm, it's ...). The frequency list splits them in two
# ("don" + "'t"), so we estimate how common they are: we take the smaller
# count of the two halves. These endings are allowed:
SHORT_FORM_ENDINGS = ["'t", "'m", "'re", "'ll", "'ve", "'d"]

# "'s" is mostly used for "belongs to" (God's, man's), which we don't want.
# So "'s" short forms are kept only for these words:
ALLOWED_S_SHORT_FORMS = [
    "it's", "he's", "she's", "that's", "what's", "there's", "here's",
    "who's", "where's", "how's", "let's",
]

# Two pronunciations: the dictionary sometimes lists strange second
# pronunciations ("fried" also as "freed"). So every word keeps only its
# main pronunciation, EXCEPT these real double words, which keep both:
REAL_DOUBLE_WORDS = [
    "read", "live", "lives", "lead", "leads", "wind", "winds", "tear",
    "tears", "close", "use", "bow", "bows", "row", "rows", "wound", "dove",
    "does",
]

# Single letters are dropped, except these real words:
SINGLE_LETTER_WORDS_TO_KEEP = ["a", "i"]

# Filler sounds from subtitles that are not words:
FILLER_SOUNDS_TO_DROP = ["uh", "um", "hmm", "mm", "mmm", "er", "erm", "shh", "sh", "hm"]

# Names (and place names) to drop. Words that are ALSO normal words
# (will, mark, rose, hope, grace, bill ...) are NOT in this list.
# Add any name you spot in word-list.txt.
NAMES_TO_DROP = [
    # first names
    "john", "mike", "tom", "sam", "dan", "ben", "jim", "joe", "bob", "paul",
    "ted", "kate", "jane", "ann", "anne", "jake", "luke", "chris", "james",
    "scott", "carl", "fred", "greg", "josh", "kurt", "matt", "pete", "phil",
    "ron", "roy", "sean", "seth", "steve", "todd", "tim", "troy", "zack",
    "zach", "beth", "jen", "jess", "kim", "liz", "meg", "pam", "tess",
    "jill", "joan", "lynn", "claire", "don", "rick", "jeff", "jon", "len",
    "lou", "mitch", "ned", "neil", "rex", "rod", "stan", "ty", "vince",
    "walt", "wes", "brett", "brad", "chad", "clark", "craig", "dwight",
    "glenn", "hans", "jude", "kirk", "lars", "les", "moe", "nate", "quinn",
    "ralph", "rhys", "ross", "russ", "saul", "sid", "wayne", "zeke", "bert",
    "burt", "clyde", "dave", "doug", "fritz", "gus", "jacques", "jose",
    "juan", "keith", "abe", "bea", "bess", "cass", "dee", "deb", "fay",
    "gail", "gwen", "jules", "kay", "lyle", "mae", "maude", "nan", "nell",
    "paige", "rae", "ruth", "trish", "val", "viv", "jones", "smith", "hayes",
    # more names found in the first word-list.txt scan
    "george", "charles", "al", "ed", "bruce", "kyle", "blake", "cole", "jin",
    "li", "karl", "shawn", "shane", "graham", "mel", "holmes", "khan", "kang",
    "singh", "gibbs", "lloyd", "stuart", "mick", "tae", "yu", "wu", "finn",
    "wang", "jung", "claus", "bart", "lin", "jan", "chang", "chen", "boyd",
    "raj", "brooke", "choi", "hugh", "marc", "blair", "doyle", "lex", "gil",
    "shaw", "hal", "ming", "wong", "neal", "barnes", "burke", "jae", "joyce",
    "flynn", "reese", "kane", "sal", "joon", "kai", "shan", "yoon", "marge",
    "ling", "nam", "moore", "blanche", "reid", "claude", "niles", "fran",
    "trent", "jang", "xiao", "liu", "glen", "kat", "ike", "tate", "spock",
    "gabe", "schmidt", "schultz", "hyun", "jun", "holt", "steele", "franz",
    "clive", "cho", "jai", "thor", "mei", "hart", "dom", "brent", "clarke",
    "kitt", "nat", "chun", "lang", "stu", "floyd", "cruz", "briggs", "greene",
    "hughes", "fitz", "alf", "nash", "walsh", "zeus", "jeong", "zhang",
    "ching", "jeanne", "yan", "kris", "bryce", "liang", "wei", "dev", "tai",
    "dwayne", "wright", "hong", "kong", "han", "vic", "cal", "mo", "bo",
    # places
    "york", "france", "spain", "rome", "wales", "greece", "prague", "maine",
]

# Words you find offensive. You asked to KEEP them for now and hide them
# yourself later, so this list starts empty.
OFFENSIVE_WORDS_TO_DROP = []

# Foreign words that appear a lot in film subtitles:
FOREIGN_WORDS_TO_DROP = [
    "el", "los", "las", "le", "de", "da", "des", "et", "que", "oui", "il",
    "ja", "se", "si", "ou", "mi", "fu", "di", "en", "ne", "te", "au", "su",
    "lu", "po", "ga", "je", "wo", "gu", "joo", "tu", "sa", "wa", "ba", "ni",
    "ji", "ta", "ra", "co", "yi", "herr", "von", "san", "con", "mon", "non",
]

# Abbreviations and broken words:
ABBREVIATIONS_TO_DROP = ["ln", "ng", "st", "dr", "ms", "im", "pos", "com", "f'd", "ve", "re", "es"]

# Words that start with an apostrophe are dropped ('s, 'm), except these:
APOSTROPHE_START_WORDS_TO_KEEP = ["'cause", "'em", "'til", "'bout"]

# WEAK FORMS: the dictionary lists quick, unstressed ways to say small words
# ("the" as "thuh", "to" as "tuh", "a" as "uh"). When a word also has a
# normal, stressed pronunciation, we drop the weak one.
# Set to False to keep both.
DROP_WEAK_FORMS = True


# ---------------------------------------------------------------------------
# 6b. LONGER WORDS (more than one syllable)
# ---------------------------------------------------------------------------
# The rhyme part of a word starts at its main stress and runs to the end:
#     REM-e-dy   ->  EH . uh . ee        (3 syllables to match)
#     key        ->  ee                  (1 syllable to match)
#
# Two words are compared syllable by syllable FROM THE END:
#   - Only the VOWELS count. The consonants between them do not.
#       remedy / Kennedy / melody / serenity = all 3 syllables match.
#   - The stress of the other word does not matter: key / monkey / happy.
#   - Vowels are compared by COLOUR (see VOWEL_COLOURS), and in longer
#     words long ā and short a count the same (money / happy).
#   - The quick, unstressed "uh" (le-ga-lly, immu-ni-ty) is NOT a real A.
#     It only matches another quick "uh", and it may be skipped:
#       remedy (EH . uh . ee) / belly (EH . ee) = 2 syllables match.
#   - "Close" colours (see CLOSE_COLOURS) count as a loose match.
#
# The page groups rhymes by how many syllables OF THE SEARCHED WORD match
# (3 matched, 2 matched, 1 matched), each with Twin / Near / Bend:
#   TWIN            matched vowels the same, the very end the same
#   NEAR            matched vowels the same, the very end slightly different
#                   (same Near rules as for one-syllable words)
#   BEND CANDIDATE  matched vowels the same, the very end different;
#                   or (2+ syllables matched) a close vowel AND a different end
#   CLOSE VOWEL     one vowel only close, the very end the same or Near
# One-syllable pairs keep their own rules above (incl. Consonant match).

# The quick unstressed vowel that may be skipped in the middle of a word:
SKIPPABLE_WEAK_VOWEL = "AH"


# ---------------------------------------------------------------------------
# 7. THE MACHINERY (you don't need to read below this line)
# ---------------------------------------------------------------------------

def plain(sounds):
    """Remove stress numbers: AY1 -> AY."""
    return [s.rstrip("012") for s in sounds]


def count_vowels(sounds):
    return sum(1 for s in plain(sounds) if s in VOWELS)


def split_word(sounds):
    """Split a one-syllable word into (start, vowel, ending)."""
    p = plain(sounds)
    for i, s in enumerate(p):
        if s in VOWELS:
            return p[:i], s, p[i + 1:]
    raise ValueError("no vowel in %r" % sounds)


def mouth_of(vowel):
    for group, vowels in MOUTH_GROUPS.items():
        if vowel in vowels:
            return group
    return "?"


def ends_on(sounds):
    return "Vowel" if plain(sounds)[-1] in VOWELS else "Consonant"


def hard_or_sharp(sounds):
    return "Sharp" if any(s in SHARP_SOUNDS for s in plain(sounds)) else "Hard"


def _twins(a, b):
    return (a, b) in VOICED_UNVOICED_TWINS or (b, a) in VOICED_UNVOICED_TWINS


def _family(sound):
    for name, members in SOUND_FAMILIES.items():
        if sound in members:
            return name
    return None


def _show(ending):
    return " ".join(ending) if ending else "(vowel)"


def _ending_match(ea, eb):
    """
    Compare two endings (the sounds after the vowel).
    Returns ("Twin", reason), ("Near", reason) or (None, None).
    """
    if ea == eb:
        if not ea:
            return "Twin", "both end on the vowel"
        return "Twin", "same ending %s" % _show(ea)

    # NEAR (a) and (b): same length, exactly one sound different
    if len(ea) == len(eb):
        diffs = [(x, y) for x, y in zip(ea, eb) if x != y]
        if len(diffs) == 1:
            x, y = diffs[0]
            if _twins(x, y):
                return "Near", "ending %s vs %s, voiced/unvoiced twins" % (x, y)
            fam = _family(x)
            if fam and fam == _family(y):
                return "Near", "ending %s vs %s, same family (%s)" % (x, y, fam)

    # NEAR (c): one sound added or dropped
    if abs(len(ea) - len(eb)) == 1:
        longer, shorter = (ea, eb) if len(ea) > len(eb) else (eb, ea)
        if shorter or NEAR_ALLOWS_ADDING_TO_OPEN_ENDING:
            for i in range(len(longer)):
                if longer[:i] + longer[i + 1:] == shorter and longer[i] not in EXTRA_SOUNDS_THAT_MAKE_BEND:
                    return "Near", "ending %s vs %s, one extra sound %s" % (_show(ea), _show(eb), longer[i])

    # OPEN ENDING: one word ends on the vowel, the other adds any consonants
    if NEAR_ALLOWS_ADDING_TO_OPEN_ENDING and bool(ea) != bool(eb):
        added = ea or eb
        if added[0] not in EXTRA_SOUNDS_THAT_MAKE_BEND:
            return "Near", "one ends on the vowel, the other adds %s" % " ".join(added)
    return None, None


def colour(v):
    return VOWEL_COLOURS[v]


def same_vowel(a, b):
    """Same colour (one-syllable words)."""
    return colour(a) == colour(b)


def close_vowel(a, b):
    ca, cb = colour(a), colour(b)
    return (ca, cb) in CLOSE_COLOURS or (cb, ca) in CLOSE_COLOURS


def _long_colour(v, stress, merge):
    """Colour of a vowel inside a longer word: the quick "uh" is its own thing."""
    if v == SKIPPABLE_WEAK_VOWEL and stress == "0":
        return "weak"
    c = colour(v)
    if merge:
        for keep, also in LONGER_WORDS_SAME_COLOURS:
            if c == also:
                return keep
    return c


def _long_close(ca, cb):
    return (ca, cb) in CLOSE_COLOURS or (cb, ca) in CLOSE_COLOURS


def compare(sounds_a, sounds_b):
    """
    Judge one pair with the SAME-VOWEL rules. Returns (category, reason),
    where category is "Twin", "Near", "Bend candidate", or None (different
    vowel). The category is the same no matter which word comes first.
    """
    _, va, ea = split_word(sounds_a)
    _, vb, eb = split_word(sounds_b)
    if not same_vowel(va, vb):
        return None, "different vowel"
    if ea == eb and plain(sounds_a) == plain(sounds_b):
        return "Twin", "sounds identical (same-sound word)"
    cat, why = _ending_match(ea, eb)
    if cat:
        return cat, "same vowel %s, %s" % (va, why)
    return "Bend candidate", "same vowel %s, different ending (%s vs %s)" % (va, _show(ea), _show(eb))


def _extra_count(a, b):
    """0 if a and b are the same, 1 if one sound was added/dropped, else None."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) != 1:
        return None
    longer, shorter = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(longer)):
        if longer[:i] + longer[i + 1:] == shorter:
            return 1
    return None


def classify(sounds_a, sounds_b):
    """
    Judge one pair with ALL rules. Returns (code, reason), where code is
    "twin", "near", "bendc" (Bend candidate), "close" (Close vowel),
    "consm" (Consonant match) or None (not shown).
    """
    if count_vowels(sounds_a) > 1 or count_vowels(sounds_b) > 1:
        code, why, _ = classify_long(sounds_a, sounds_b)
        return code, why
    sa, va, ea = split_word(sounds_a)
    sb, vb, eb = split_word(sounds_b)
    if same_vowel(va, vb):
        cat, why = compare(sounds_a, sounds_b)
        return {"Twin": "twin", "Near": "near", "Bend candidate": "bendc"}[cat], why

    if close_vowel(va, vb):
        cat, why = _ending_match(ea, eb)
        if cat:
            return "close", "close vowels %s / %s, %s" % (va, vb, why)

    x, y = _extra_count(sa, sb), _extra_count(ea, eb)
    if x is not None and y is not None and x + y <= CONSONANT_MATCH_MAX_EXTRA:
        shared = min(len(sa), len(sb)) + min(len(ea), len(eb))
        if shared >= CONSONANT_MATCH_MIN_SHARED:
            frame = "%s . %s" % (" ".join(sa) or "-", " ".join(ea) or "-")
            if x + y == 0:
                return "consm", "different vowel, same consonants (%s)" % frame
            return "consm", "different vowel, consonants %s vs %s . %s, one extra" % (
                frame, " ".join(sb) or "-", " ".join(eb) or "-")
    return None, None


def parse_long(sounds):
    """
    Split a word (sounds WITH stress numbers) into its rhyme part:
    a list of (vowel, stress) from the main stress to the end, and the
    ending (sounds after the last vowel).
    """
    vowels, last = [], -1
    for i, s in enumerate(sounds):
        if s.rstrip("012") in VOWELS:
            vowels.append((s.rstrip("012"), s[-1] if s[-1] in "012" else "0"))
            last = i
    main = next((i for i, (v, st) in enumerate(vowels) if st == "1"), 0)
    return vowels[main:], plain(sounds[last + 1:])


def syllables_to_match(sounds):
    return len(parse_long(sounds)[0])


def classify_long(sounds_a, sounds_b):
    """
    Judge a pair where at least one word is longer than one syllable.
    Returns (code, reason, matched), where matched = how many syllables of
    word A's rhyme part were matched.
    """
    ra, ea = parse_long(sounds_a)
    rb, eb = parse_long(sounds_b)
    merge = count_vowels(sounds_a) > 1 and count_vowels(sounds_b) > 1
    ca = [_long_colour(v, st, merge) for v, st in ra]
    cb = [_long_colour(v, st, merge) for v, st in rb]
    i, j = len(ca) - 1, len(cb) - 1
    if not (ca[i] == cb[j] or _long_close(ca[i], cb[j])):
        return None, None, 0
    matched, close = 0, 0
    while i >= 0 and j >= 0:
        if ca[i] == cb[j] or _long_close(ca[i], cb[j]):
            matched += 1
            close += 0 if ca[i] == cb[j] else 1
            i, j = i - 1, j - 1
        elif i < len(ca) - 1 and ca[i] == "weak":
            i -= 1
        elif j < len(cb) - 1 and cb[j] == "weak":
            j -= 1
        else:
            break
    end, end_why = _ending_match(ea, eb)
    if plain(sounds_a) == plain(sounds_b):
        return "twin", "sounds identical (same-sound word)", matched
    what = "%d syllable%s match" % (matched, "" if matched == 1 else "s")
    if close == 0:
        if end == "Twin":
            return "twin", "%s, same end" % what, matched
        if end == "Near":
            return "near", "%s, %s" % (what, end_why), matched
        return "bendc", "%s, different end (%s vs %s)" % (what, _show(ea), _show(eb)), matched
    if close == 1 and end:
        return "close", "%s, one vowel only close, %s" % (what, end_why), matched
    if matched >= 2:
        return "bendc", "%s, vowels only close and different end" % what, matched
    return None, None, 0


def classify_full(sounds_a, sounds_b):
    """classify() plus how many syllables of word A matched (for the page)."""
    if count_vowels(sounds_a) > 1 or count_vowels(sounds_b) > 1:
        return classify_long(sounds_a, sounds_b)
    code, why = classify(sounds_a, sounds_b)
    return code, why, (1 if code in ("twin", "near", "bendc", "close") else 0)
