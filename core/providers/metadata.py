"""Plex-metadata detectors: people, genre, country, language, rating cert, duration."""

from __future__ import annotations

from . import MovieContext, provider


def _first_tag(movie: dict, key: str) -> str | None:
    items = movie.get(key, [])
    names = [item.get("tag") for item in items if item.get("tag")]
    return names[0] if names else None


@provider("ContentRating", "content_rating")
def content_rating(ctx: MovieContext) -> str | None:
    return ctx.movie.get("contentRating") or None


@provider("Director", "director")
def director(ctx: MovieContext) -> str | None:
    return _first_tag(ctx.movie, "Director")


@provider("Writer", "writer")
def writer(ctx: MovieContext) -> str | None:
    return _first_tag(ctx.movie, "Writer")


@provider("Genre", "genre")
def genre(ctx: MovieContext) -> str | None:
    return _first_tag(ctx.movie, "Genre")


@provider("Studio", "studio")
def studio(ctx: MovieContext) -> str | None:
    return _first_tag(ctx.movie, "Studio") or ctx.movie.get("studio") or None


@provider("Duration", "duration")
def duration(ctx: MovieContext) -> str | None:
    dur_ms = ctx.movie.get("duration")
    if not dur_ms:
        return None
    total_minutes = int(dur_ms // 60000)
    hours, mins = divmod(total_minutes, 60)
    return f"{hours}hr {mins}min" if hours else f"{mins}min"


@provider("DurationMinutes", "duration_minutes")
def duration_minutes(ctx: MovieContext) -> str | None:
    dur_ms = ctx.movie.get("duration")
    if not dur_ms:
        return None
    return f"{int(dur_ms // 60000)}min"


@provider("ShortFilm", "short_film")
def short_film(ctx: MovieContext) -> str | None:
    dur_ms = ctx.movie.get("duration")
    if dur_ms and int(dur_ms // 60000) < 40:
        return "Short Film"
    return None


# ---- Country ---------------------------------------------------------------

_COUNTRY_SHORT_NAMES = {
    "United States of America": "United States",
    "Czech Republic": "Czechia",
    "Macedonia, The Former Yugoslav Republic of": "Macedonia",
    "Federal Republic of Germany": "Germany",
    "Republic of Moldova": "Moldova",
    "Russian Federation": "Russia",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "Korea, Republic of": "South Korea",
    "Republic of Korea": "South Korea",
    "Korea, Democratic People's Republic of": "North Korea",
    "Hong Kong SAR China": "Hong Kong",
    "Macau SAR China": "Macau",
    "Taiwan, Province of China": "Taiwan",
    "Viet Nam": "Vietnam",
    "Lao People's Democratic Republic": "Laos",
    "Iran, Islamic Republic of": "Iran",
    "Islamic Republic of Iran": "Iran",
    "Syrian Arab Republic": "Syria",
    "Republic of the Union of Myanmar": "Myanmar",
    "People's Republic of China": "China",
    "United Arab Emirates": "UAE",
    "Kingdom of Saudi Arabia": "Saudi Arabia",
    "Bolivarian Republic of Venezuela": "Venezuela",
    "Venezuela, Bolivarian Republic of": "Venezuela",
}

# Countries that often appear first purely for financing reasons; prefer the
# next listed country when one of these leads.
_FINANCING_HUBS = {
    "uae", "united arab emirates", "qatar", "luxembourg", "liechtenstein",
    "malta", "monaco", "saudi arabia", "hong kong", "singapore",
    "cayman islands", "bahamas",
}


@provider("Country", "country")
def country(ctx: MovieContext) -> str | None:
    raw_tags = [c.get("tag") for c in ctx.movie.get("Country", []) or [] if c.get("tag")]
    mapped = [_COUNTRY_SHORT_NAMES.get(tag, tag).strip() for tag in raw_tags if tag.strip()]
    if not mapped:
        return None
    for tag in mapped:
        if tag.lower() not in _FINANCING_HUBS:
            return tag
    return mapped[0]


# ---- Language ----------------------------------------------------------------

# Native/raw language names (as Plex reports them) -> English display name.
_LANGUAGE_NAMES = {
    'Afrikaans': 'Afrikaans', 'Akan': 'Akan', 'Shqip': 'Albanian', 'አማርኛ': 'Amharic',
    'العربية': 'Arabic', 'Aragonés': 'Aragonese', 'հայերեն': 'Armenian', 'অসমীয়া': 'Assamese',
    'Asturianu': 'Asturian', 'Azərbaycan': 'Azerbaijani', 'Башҡортса': 'Bashkir',
    'Euskara': 'Basque', 'Беларуская': 'Belarusian', 'বাংলা': 'Bengali', 'Bosanski': 'Bosnian',
    'Brezhoneg': 'Breton', 'Български': 'Bulgarian', 'ဗမာစာ': 'Burmese', 'Català': 'Catalan',
    'Cebuano': 'Cebuano', 'ᏣᎳᎩ': 'Cherokee', '中文': 'Chinese', '广东话': 'Cantonese',
    '普通话': 'Mandarin', 'Corsu': 'Corsican', 'Hrvatski': 'Croatian', 'Čeština': 'Czech',
    'Dansk': 'Danish', 'ދިވެހި': 'Dhivehi', 'Nederlands': 'Dutch', 'ཇོང་ཁ': 'Dzongkha',
    'English': 'English', 'Esperanto': 'Esperanto', 'Eesti': 'Estonian', 'Føroyskt': 'Faroese',
    'Fiji Hindi': 'Fiji Hindi', 'Filipino': 'Filipino', 'Suomi': 'Finnish', 'Français': 'French',
    'Frysk': 'Frisian', 'Fulfulde': 'Fulah', 'Galego': 'Galician', 'ქართული': 'Georgian',
    'Deutsch': 'German', 'Ελληνικά': 'Greek', 'Kalaallisut': 'Greenlandic', 'ગુજરાતી': 'Gujarati',
    'Kreyòl ayisyen': 'Haitian Creole', 'Hausa': 'Hausa', 'ʻŌlelo Hawaiʻi': 'Hawaiian',
    'עברית': 'Hebrew', 'हिन्दी': 'Hindi', 'Hmong': 'Hmong', 'Hungarian': 'Hungarian',
    'Magyar': 'Hungarian', 'magyar': 'Hungarian', 'Íslenska': 'Icelandic', 'Igbo': 'Igbo',
    'Ilokano': 'Ilokano', 'Bahasa Indonesia': 'Indonesian', 'Gaeilge': 'Irish',
    'Italiano': 'Italian', '日本語': 'Japanese', 'Basa Jawa': 'Javanese', 'ಕನ್ನಡ': 'Kannada',
    'Қазақ тілі': 'Kazakh', 'ភាសាខ្មែរ': 'Khmer', 'Kinyarwanda': 'Kinyarwanda',
    'Kiswahili': 'Swahili', '한국어': 'Korean', 'Kurdî': 'Kurdish', 'Кыргызча': 'Kyrgyz',
    'ລາວ': 'Lao', 'Latviešu': 'Latvian', 'Lietuvių': 'Lithuanian',
    'Lëtzebuergesch': 'Luxembourgish', 'Македонски': 'Macedonian', 'Malagasy': 'Malagasy',
    'Bahasa Melayu': 'Malay', 'മലയാളം': 'Malayalam', 'Malti': 'Maltese', 'Māori': 'Maori',
    'मराठी': 'Marathi', 'Монгол': 'Mongolian', 'myn': 'Mayan', "Mayaq'ik": 'Mayan',
    'नेपाली': 'Nepali', 'Norsk': 'Norwegian', 'norsk': 'Norwegian', 'Occitan': 'Occitan',
    'ଓଡ଼ିଆ': 'Odia', 'Afaan Oromoo': 'Oromo', 'پښتو': 'Pashto', 'فارسی': 'Persian',
    'Polski': 'Polish', 'Português': 'Portuguese', 'ਪੰਜਾਬੀ': 'Punjabi', 'Quechua': 'Quechua',
    'Română': 'Romanian', 'Rumantsch': 'Romansh', 'Русский': 'Russian', 'Samoan': 'Samoan',
    'Sängö': 'Sango', 'Gaelic': 'Scottish Gaelic', 'Српски': 'Serbian', 'Sesotho': 'Sesotho',
    'Setswana': 'Setswana', 'Shona': 'Shona', 'සිංහල': 'Sinhala', 'Slovenčina': 'Slovak',
    'Slovenščina': 'Slovenian', 'Soomaaliga': 'Somali', 'Español': 'Spanish',
    'Basa Sunda': 'Sundanese', 'Svenska': 'Swedish', 'Tagalog': 'Tagalog', 'தமிழ்': 'Tamil',
    'Татарча': 'Tatar', 'తెలుగు': 'Telugu', 'ไทย': 'Thai', 'བོད་ཡིག': 'Tibetan',
    'Tigrinya': 'Tigrinya', 'Türkçe': 'Turkish', 'Türkmen': 'Turkmen',
    'Українська': 'Ukrainian', 'اردو': 'Urdu', 'Uyghur': 'Uyghur', 'Tiếng Việt': 'Vietnamese',
    'Cymraeg': 'Welsh', 'Wolof': 'Wolof', 'isiXhosa': 'Xhosa', 'ייִדיש': 'Yiddish',
    'Yorùbá': 'Yoruba', 'isiZulu': 'Zulu',
}

_UNKNOWN_LANGUAGES = {"Unknown", "Undetermined", "Undetermined language"}


@provider("Language", "language")
def language(ctx: MovieContext) -> str | None:
    audio_tracks = []
    for media in ctx.movie.get("Media", []):
        for part in media.get("Part", []):
            for stream in part.get("Stream", []):
                if stream.get("streamType") == 2 and stream.get("language"):
                    audio_tracks.append(stream["language"])

    if len(audio_tracks) > 1 and ctx.config.skip_multiple_audio_tracks:
        return None

    for lang in audio_tracks:
        name = _LANGUAGE_NAMES.get(lang, lang)
        if name not in _UNKNOWN_LANGUAGES and name not in ctx.config.excluded_languages:
            return name
    return None
