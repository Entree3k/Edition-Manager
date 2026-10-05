"""Filename-based detectors: cut/edition and boutique release label."""

from __future__ import annotations

import re

from . import MovieContext, provider

# ---- Cut / edition -------------------------------------------------------

_CUT_PATTERNS = [
    (r"director'?s[ ._-]?cut|dirs[ ._-]?cut|dir[ ._-]?cut", "Director's Cut"),
    (r"extended( [._-]?(cut|edition|version))?", "Extended"),
    (r"(final)[ ._-]?cut", "Final Cut"),
    (r"(ultimate)[ ._-](cut|edition)?", "Ultimate Edition"),
    (r"(assembly|recut)[ ._-]?(cut|edition)?", "Assembly Cut"),
    (r"(special|collector'?s)[ ._-]?(edition|cut)?", "Special Edition"),
    (r"(workprint)[ ._-]?(cut|edition)?", "Workprint"),
    (r"(redux)[ ._-]?(cut|edition)?", "Redux"),
    (r"(festival|cannes|sundance)[ ._-]?cut", "Festival Cut"),
    (r"(theatrical|international|us[ ._-]?theatrical|tv[ ._-]?(cut|version)|network[ ._-]?cut)", "Theatrical Cut"),
    (r"(fan[ ._-]?edit|despecialized|fan[ ._-]?restoration)", "Fan Edit"),
    (r"\b(unrated|uncut)\b", "Unrated"),
    (r"imax(?![ ._-]?enhanced)", "IMAX"),
    (r"(\d{1,3})(st|nd|rd|th)?[ ._-]?anniversary", "Anniversary Edition"),
    (r"remaster", "Remastered"),
    (r"restored", "Restored"),
]


@provider("Cut", "cut")
def cut(ctx: MovieContext) -> str | None:
    name_low = ctx.file_name.lower()
    for pattern, label in _CUT_PATTERNS:
        if re.search(pattern, name_low):
            return label
    return None


# ---- Boutique release label ------------------------------------------------

_SEP = r"(?:[.\s_\-\[\]\(\)]+)"
_CC_PATTERN = r"(?<![a-z0-9])cc(?![a-z0-9])"

_LABEL_PATTERNS = [
    (re.compile(r"(?<![a-z0-9])criterion(\.collection)?(?![a-z0-9])", re.I), "Criterion"),
    (re.compile(r"(?<![a-z0-9])janus(?![a-z0-9])", re.I), "Criterion"),
    # "CC" heuristic for Criterion — skipped when the name mentions captions/subs.
    (re.compile(_CC_PATTERN, re.I), "Criterion"),
    (re.compile(rf"(?<![a-z0-9])arrow({_SEP}?video)?(?![a-z0-9])", re.I), "Arrow Video"),
    (re.compile(rf"(?<![a-z0-9])scream{_SEP}?factory(?![a-z0-9])", re.I), "Scream Factory"),
    (re.compile(rf"(?<![a-z0-9])shout!?{_SEP}?factory(?![a-z0-9])", re.I), "Shout Factory"),
    (re.compile(rf"(?<![a-z0-9])dark{_SEP}?star{_SEP}?pictures(?![a-z0-9])", re.I), "Dark Star Pictures"),
    (re.compile(rf"(?<![a-z0-9])kino({_SEP}?lorber)?(?![a-z0-9])", re.I), "Kino Lorber"),
    (re.compile(rf"(?<![a-z0-9])vinegar({_SEP}?syndrome)?(?![a-z0-9])", re.I), "Vinegar Syndrome"),
    (re.compile(r"(?<![a-z0-9])severin(?![a-z0-9])", re.I), "Severin Films"),
    (re.compile(rf"(?<![a-z0-9])second{_SEP}?sight(?![a-z0-9])", re.I), "Second Sight Films"),
    (re.compile(r"(?<![a-z0-9])88\s*films?(?![a-z0-9])", re.I), "88 Films"),
    (re.compile(r"(?<![a-z0-9])radiance(?![a-z0-9])", re.I), "Radiance Films"),
    (re.compile(r"(?<![a-z0-9])eureka(?![a-z0-9])", re.I), "Masters of Cinema"),
    (re.compile(rf"(?<![a-z0-9])(masters{_SEP}?of{_SEP}?cinema|moc)(?![a-z0-9])", re.I), "Masters of Cinema"),
    (re.compile(r"(?<![a-z0-9])imprint(?![a-z0-9])", re.I), "Imprint Films"),
    (re.compile(rf"(?<![a-z0-9])via{_SEP}?vision(?![a-z0-9])", re.I), "Imprint Films"),
    (re.compile(r"(?<![a-z0-9])indicator(?![a-z0-9])", re.I), "Indicator Films"),
    (re.compile(r"(?<![a-z0-9])powerhouse(?![a-z0-9])", re.I), "Indicator Films"),
    (re.compile(rf"(?<![a-z0-9])blue{_SEP}?underground(?![a-z0-9])", re.I), "Blue Underground"),
    (re.compile(rf"(?<![a-z0-9])cult{_SEP}?epics?(?![a-z0-9])", re.I), "Cult Epics"),
    (re.compile(r"(?<![a-z0-9])arbelos(?![a-z0-9])", re.I), "Arbelos Films"),
]

_LABEL_PRIORITY = {
    "Criterion": 100, "Arrow Video": 95, "Shout Factory": 92, "Scream Factory": 91,
    "Kino Lorber": 90, "Vinegar Syndrome": 88, "Severin Films": 86,
    "Second Sight Films": 84, "88 Films": 82, "Radiance Films": 80,
    "Masters of Cinema": 78, "Imprint Films": 76, "Indicator Films": 74,
    "Blue Underground": 72, "Dark Star Pictures": 70, "Cult Epics": 68,
    "Arbelos Films": 66,
}

_CC_BAN = re.compile(r"(closed\.?captions?|caption|subs?|subtitles?)", re.I)


@provider("Release", "release")
def release(ctx: MovieContext) -> str | None:
    low = ctx.file_name.lower()
    if not low:
        return None

    found = set()
    for pattern, label in _LABEL_PATTERNS:
        if pattern.pattern == _CC_PATTERN and _CC_BAN.search(low):
            continue
        if pattern.search(low):
            found.add(label)
    if not found:
        return None
    return max(found, key=lambda label: _LABEL_PRIORITY.get(label, 0))
