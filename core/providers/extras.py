"""Special-features detector: summarises a movie's Plex extras."""

from __future__ import annotations

from . import MovieContext, provider

_TITLE_KEYWORDS = [
    (("gag reel", "bloopers", "outtakes"), "Gag Reel"),
    (("deleted scene", "deleted footage"), "Deleted Scenes"),
    (("behind the scenes", "making of", "on set"), "Behind the Scenes"),
    (("interview", "q&a", "qa"), "Interviews"),
    (("commentary", "audio commentary"), "Commentary Track"),
    (("featurette", "featurettes"), "Featurette"),
    (("screen test", "camera test"), "Screen Test"),
    (("promo", "tv spot", "spot"), "Promo / TV Spot"),
    (("storyboard",), "Storyboard"),
]

_SUBTYPE_KEYWORDS = [
    ("deleted", "Deleted Scenes"),
    ("behind", "Behind the Scenes"),
    ("interview", "Interviews"),
    ("featurette", "Featurette"),
    ("commentary", "Commentary Track"),
]

# Too vague to be worth listing in an edition title.
_EXCLUDED = {"Trailer", "Special Features"}


def _classify(extra: dict) -> str:
    title = (extra.get("title") or "").lower()
    subtype = (extra.get("subtype") or extra.get("type") or "").lower()

    for keywords, label in _TITLE_KEYWORDS:
        if any(k in title for k in keywords):
            return label
    for keyword, label in _SUBTYPE_KEYWORDS:
        if keyword in subtype:
            return label
    if "scene" in subtype and "alt" in subtype:
        return "Alternate Scene"
    if "trailer" in subtype or "trailer" in title:
        return "Trailer"
    return "Special Features"


@provider("SpecialFeatures", "special_features")
def special_features(ctx: MovieContext) -> str | None:
    rating_key = ctx.movie.get("ratingKey")
    if not rating_key:
        return None

    extras_list = ctx.plex.extras(rating_key)
    if not extras_list:
        return None

    seen = []
    for extra in extras_list:
        label = _classify(extra)
        if label not in seen:
            seen.append(label)

    kinds = [k for k in seen if k not in _EXCLUDED][:3]
    return " · ".join(kinds) if kinds else None
