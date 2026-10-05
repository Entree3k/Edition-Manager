"""Audio detectors: channel layout and codec."""

from __future__ import annotations

import re

from . import MovieContext, provider


def _audio_streams(movie: dict):
    for media in movie.get("Media", []):
        for part in media.get("Part", []):
            for stream in part.get("Stream", []):
                if stream.get("streamType") == 2:
                    yield stream


_CHANNEL_LAYOUTS = {1: "1.0", 2: "2.0", 3: "2.1", 4: "4.0", 5: "5.0", 6: "5.1", 7: "6.1", 8: "7.1"}


@provider("AudioChannels", "audio_channels")
def audio_channels(ctx: MovieContext) -> str | None:
    best = 0
    for stream in _audio_streams(ctx.movie):
        channels = stream.get("channels", 0)
        if channels and channels > best:
            best = channels
    if best == 0:
        return None
    return _CHANNEL_LAYOUTS.get(best, f"{best}-ch")


@provider("AudioCodec", "audio_codec")
def audio_codec(ctx: MovieContext) -> str | None:
    # Pick the "best" audio stream: most channels, then highest bitrate.
    best = None
    for stream in _audio_streams(ctx.movie):
        cand = {
            "channels": stream.get("channels", 0) or 0,
            "bitrate": stream.get("bitrate", 0) or 0,
            "text": " ".join(str(stream.get(k) or "") for k in
                             ("displayTitle", "title", "codec", "profile", "audioProfile")),
        }
        if best is None or (cand["channels"], cand["bitrate"]) > (best["channels"], best["bitrate"]):
            best = cand
    if best is None:
        return None

    blob = best["text"].upper()
    # Strip channel-layout noise so e.g. "5.1" doesn't confuse codec matching.
    blob = re.sub(r"\b(?:MONO|STEREO)\b", "", blob)
    blob = re.sub(r"\b(?:\d{1,2}\.\d|\d{1,2}\s*CH|CHANNELS?)\b", "", blob)
    blob = re.sub(r"\b(?:L\s?R|SURROUND|MULTICHANNEL)\b", "", blob)
    blob = re.sub(r"\s+", " ", blob).strip()

    has_atmos = any(k in blob for k in ("ATMOS", "JOC", "DOLBY ATMOS"))
    if any(k in blob for k in ("DTS:X", "DTSX", "DTS X")):
        return "DTS:X"
    if any(k in blob for k in ("AURO-3D", "AURO 3D", "AURO3D", "AURO")):
        return "Auro-3D"

    base = _base_codec(blob)
    if base is None:
        return "Dolby Atmos" if has_atmos else None
    if has_atmos and base in ("Dolby Digital Plus", "Dolby TrueHD"):
        return f"{base} Atmos"
    return base


def _base_codec(text: str) -> str | None:
    if any(k in text for k in ("E-AC-3", "EAC3", "DDP", "DD+", "DOLBY DIGITAL PLUS")):
        return "Dolby Digital Plus"
    if any(k in text for k in ("AC3", "AC-3", "DOLBY DIGITAL")):
        return "Dolby Digital"
    if any(k in text for k in ("TRUEHD", "TRUE-HD", "DOLBY TRUEHD")):
        return "Dolby TrueHD"
    if any(k in text for k in ("DTS-HD MA", "DTSHD MA", "DTS-HD.MA", "DTS HD MA")):
        return "DTS-HD MA"
    if any(k in text for k in ("DTS-HD HRA", "DTSHD HRA", "DTS-HR", "DTS HD HRA")):
        return "DTS-HD HRA"
    if "DTS" in text:
        return "DTS"
    if "FLAC" in text:
        return "FLAC"
    if any(k in text for k in ("PCM", "LPCM")):
        return "PCM"
    if "OPUS" in text:
        return "Opus"
    if "ALAC" in text:
        return "ALAC"
    if "VORBIS" in text:
        return "Vorbis"
    if "AAC" in text:
        return "AAC"
    return None
