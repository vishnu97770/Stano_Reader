"""
Context rules for candidate re-ranking.

CONTEXT_RULES maps a trigger word (the last word of the transcript, lowercased)
to a dict of {candidate_word: boost_amount}.

Boost amounts are in (0, 1].  They are added to the base confidence from the
Candidate Engine and the total is capped at 0.99.  Only words present in
candidate_dictionary.py are listed here — boosting an unknown word has no effect
since it will never appear in the candidate list.

To add a new rule: add an entry to CONTEXT_RULES.  No other file needs to change.
"""

# trigger word → {candidate word → boost}
CONTEXT_RULES: dict[str, dict[str, float]] = {
    # After a subject pronoun — most likely followed by a verb
    "i": {
        "do":    0.15,
        "get":   0.15,
        "give":  0.12,
        "go":    0.15,
        "put":   0.12,
        "pick":  0.10,
        "set":   0.10,
        "seek":  0.10,
        "pay":   0.10,
        "stop":  0.10,
        "fix":   0.10,
        "fetch": 0.08,
        "teach": 0.08,
        "check": 0.08,
        "push":  0.08,
        "pass":  0.08,
    },
    "they": {
        "do":    0.15,
        "get":   0.15,
        "give":  0.12,
        "go":    0.15,
        "set":   0.10,
        "stop":  0.10,
        "seek":  0.10,
        "fix":   0.08,
        "teach": 0.08,
        "pay":   0.10,
        "pick":  0.08,
        "check": 0.08,
        "push":  0.08,
    },

    # After the definite article — most likely followed by a noun
    "the": {
        "best":  0.15,
        "big":   0.12,
        "bad":   0.10,
        "case":  0.12,
        "cost":  0.10,
        "fact":  0.12,
        "base":  0.10,
        "boss":  0.10,
        "cat":   0.08,
        "test":  0.12,
        "bag":   0.08,
        "book":  0.10,
        "beast": 0.08,
        "gift":  0.10,
        "bus":   0.08,
        "guest": 0.10,
        "desk":  0.08,
        "vest":  0.08,
        "task":  0.10,
        "job":   0.10,
        "voice": 0.08,
    },

    # After the infinitive marker — followed by a verb
    "to": {
        "get":   0.15,
        "give":  0.15,
        "go":    0.15,
        "do":    0.15,
        "set":   0.12,
        "stop":  0.12,
        "put":   0.12,
        "pick":  0.10,
        "seek":  0.10,
        "fix":   0.12,
        "fetch": 0.10,
        "teach": 0.10,
        "pay":   0.10,
        "pack":  0.08,
        "push":  0.10,
        "pass":  0.08,
        "check": 0.10,
        "test":  0.10,
        "touch": 0.08,
    },

    # After the indefinite article — followed by a singular noun or adjective
    "a": {
        "big":  0.12,
        "bad":  0.10,
        "bit":  0.12,
        "bet":  0.10,
        "bat":  0.08,
        "bag":  0.10,
        "cat":  0.10,
        "bug":  0.08,
        "cup":  0.08,
        "gut":  0.08,
        "gift": 0.10,
        "task": 0.08,
        "desk": 0.08,
        "case": 0.10,
        "fact": 0.10,
        "test": 0.08,
        "book": 0.10,
        "bus":  0.08,
        "job":  0.10,
        "cost": 0.08,
        "vest": 0.08,
    },

    # After "just" — usually precedes a verb
    "just": {
        "get":   0.12,
        "go":    0.12,
        "do":    0.12,
        "give":  0.10,
        "set":   0.10,
        "stop":  0.10,
        "pay":   0.10,
        "put":   0.10,
        "pick":  0.08,
        "fix":   0.10,
        "fetch": 0.08,
        "check": 0.08,
        "push":  0.08,
    },

    # After demonstratives — usually followed by a noun or adjective
    "that": {
        "big":  0.10,
        "bad":  0.10,
        "best": 0.10,
        "fact": 0.10,
        "case": 0.10,
        "test": 0.08,
        "task": 0.08,
        "cost": 0.08,
        "bug":  0.08,
        "bit":  0.08,
        "book": 0.08,
        "gift": 0.08,
        "job":  0.08,
    },
    "this": {
        "big":  0.10,
        "bad":  0.10,
        "best": 0.10,
        "case": 0.12,
        "fact": 0.10,
        "test": 0.10,
        "task": 0.10,
        "cost": 0.08,
        "book": 0.08,
        "desk": 0.08,
        "job":  0.08,
        "gift": 0.08,
    },

    # After "do" — often followed by a demonstrative or continuation
    "do": {
        "this":  0.12,
        "that":  0.12,
        "the":   0.10,
        "check": 0.10,
        "best":  0.08,
        "get":   0.08,
        "go":    0.08,
    },
}
