"""Video/file detectors: resolution, codec, dynamic range, frame rate, bitrate, size, source."""

from __future__ import annotations

import re

from . import MovieContext, provider


@provider("Resolution", "resolution")
def resolution(ctx: MovieContext) -> str | None:
    resolutions = set()
    for media in ctx.movie.get("Media", []):
        res = media.get("videoResolution")
        if res:
            res = res.upper()
            if res.isdigit():
                res += "p"
            resolutions.add(res)
    if not resolutions:
        return None
    order = ["480P", "576P", "720P", "1080P", "2K", "4K", "8K"]
    ordered = sorted(resolutions, key=lambda r: order.index(r) if r in order else len(order))
    return " · ".join(ordered)


_VIDEO_CODECS = {
    "hevc": "H.265", "h265": "H.265", "h.265": "H.265", "hvc1": "H.265",
    "h264": "H.264", "h.264": "H.264", "avc": "H.264", "avc1": "H.264",
    "av1": "AV1", "vp9": "VP9", "vp8": "VP8",
    "mpeg2": "MPEG-2", "mpeg-2": "MPEG-2", "mpeg4": "MPEG-4", "mpeg-4": "MPEG-4",
    "xvid": "XviD", "divx": "DivX", "vc1": "VC-1", "vc-1": "VC-1",
    "prores": "ProRes", "dnxhd": "DNxHD", "dnxhr": "DNxHR", "theora": "Theora",
}


@provider("VideoCodec", "video_codec")
def video_codec(ctx: MovieContext) -> str | None:
    media_list = ctx.movie.get("Media", [])
    if not media_list:
        return None
    codec = media_list[0].get("videoCodec")
    if not codec:
        return None
    return _VIDEO_CODECS.get(codec.lower(), codec.upper())


@provider("FrameRate", "frame_rate")
def frame_rate(ctx: MovieContext) -> str | None:
    media_list = ctx.movie.get("Media", [])
    if not media_list:
        return None
    fr = media_list[0].get("videoFrameRate") or media_list[0].get("frameRate")
    if not fr:
        return None
    try:
        val = float(str(fr).lower().replace("p", ""))
        if abs(val - round(val)) < 0.01:
            return f"{int(round(val))}fps"
        return f"{val:.2f}fps"
    except ValueError:
        return f"{fr}fps"


@provider("Bitrate", "bitrate")
def bitrate(ctx: MovieContext) -> str | None:
    # Bitrate of the largest part (the one we treat as the main file).
    max_size, best = 0, None
    for media in ctx.movie.get("Media", []):
        for part in media.get("Part", []):
            size = part.get("size", 0)
            if size > max_size:
                max_size = size
                best = media.get("bitrate")
    if best is None:
        return None
    try:
        kbps = float(best)
    except (TypeError, ValueError):
        return None
    if kbps >= 1000:
        return f"{kbps / 1000.0:.1f} Mbps"
    return f"{int(kbps)} Kbps"


@provider("Size", "size")
def size(ctx: MovieContext) -> str | None:
    max_size = 0
    for media in ctx.movie.get("Media", []):
        for part in media.get("Part", []):
            max_size = max(max_size, part.get("size", 0))
    if max_size <= 0:
        return None
    gib = max_size / 1024 ** 3
    if gib >= 1:
        return f"{gib:.1f} GB"
    return f"{max_size / 1024 ** 2:.0f} MB"


# ---- Dynamic range -----------------------------------------------------------

# Filename token patterns, delimiter-guarded to avoid false positives ("DVDRip" != DV).
_SEP = r"(?:[.\s_\-\[\]\(\)]+)"
_PAT_DV = re.compile(
    rf"(?<![a-z0-9])(?:(?:dv(?!d|dr|drip|dremux|db|bd|br))|dovi|dolby{_SEP}vision)(?![a-z0-9])", re.I)
_PAT_HDR10PLUS = re.compile(r"(?<![a-z0-9])(?:hdr10\+|hdr10plus)(?![a-z0-9])", re.I)
_PAT_HDR10 = re.compile(r"(?<![a-z0-9])hdr10(?!\+)(?![a-z0-9])", re.I)
_PAT_HLG = re.compile(r"(?<![a-z0-9])hlg(?![a-z0-9])", re.I)
_PAT_HDR = re.compile(r"(?<![a-z0-9])hdr(?!10\+?)(?![a-z0-9])", re.I)
_PAT_SDR = re.compile(r"(?<![a-z0-9])sdr(?![a-z0-9])", re.I)

_DR_PRIORITY = {
    "Dolby Vision · HDR10": 6, "Dolby Vision": 5, "HDR10+": 4,
    "HDR10": 3, "HLG": 2, "HDR": 1, None: 0,
}


def _better(current, candidate):
    return candidate if _DR_PRIORITY.get(candidate, 0) > _DR_PRIORITY.get(current, 0) else current


def _low(value) -> str:
    return str(value).strip().lower() if value is not None else ""


def _is_hdr10_from_color(stream) -> bool:
    trc = _low(stream.get("colorTrc"))
    prim = _low(stream.get("colorPrimaries"))
    return trc in ("smpte2084", "pq", "pq_transfer") and "bt2020" in prim


def _dr_from_stream(stream) -> str | None:
    disp_low = _low(stream.get("displayTitle") or stream.get("title") or "")
    vdr = _low(stream.get("videoDynamicRange"))
    vdrt = _low(stream.get("videoDynamicRangeType"))
    trc = _low(stream.get("colorTrc"))

    is_dv = (
        "dolby vision" in disp_low or "dovi" in disp_low or " dv " in f" {disp_low} "
        or "doviprofile" in stream or vdr == "dolby vision" or vdrt == "dolby vision"
    )
    if is_dv:
        has_hdr10_base = (
            "hdr10+" not in disp_low
            and ("hdr10" in disp_low or vdr == "hdr10" or vdrt == "hdr10"
                 or _is_hdr10_from_color(stream))
        )
        return "Dolby Vision · HDR10" if has_hdr10_base else "Dolby Vision"
    if "hdr10+" in disp_low or vdrt == "hdr10+" or vdr == "hdr10+":
        return "HDR10+"
    if "hdr10" in disp_low or vdr == "hdr10" or vdrt == "hdr10" or _is_hdr10_from_color(stream):
        return "HDR10"
    if "hlg" in disp_low or vdr == "hlg" or vdrt == "hlg" or trc in ("arib-std-b67", "hlg"):
        return "HLG"
    if " hdr" in f" {disp_low}" or vdr == "hdr" or vdrt == "hdr":
        return "HDR"
    return None


@provider("DynamicRange", "dynamic_range")
def dynamic_range(ctx: MovieContext) -> str | None:
    """Best dynamic-range label from stream metadata, falling back to filename tokens."""
    best = None
    for media in ctx.movie.get("Media", []):
        for part in media.get("Part", []):
            for stream in part.get("Stream", []):
                if stream.get("streamType") == 1:
                    best = _better(best, _dr_from_stream(stream))
    if best:
        return best

    file_best = None
    for media in ctx.movie.get("Media", []):
        for part in media.get("Part", []):
            fname = part.get("file") or ""
            if not fname:
                continue
            has_dv = bool(_PAT_DV.search(fname))
            has_hdr10 = bool(_PAT_HDR10.search(fname))
            if has_dv and has_hdr10:
                cand = "Dolby Vision · HDR10"
            elif has_dv:
                cand = "Dolby Vision"
            elif _PAT_HDR10PLUS.search(fname):
                cand = "HDR10+"
            elif has_hdr10:
                cand = "HDR10"
            elif _PAT_HLG.search(fname):
                cand = "HLG"
            elif _PAT_HDR.search(fname) and not _PAT_SDR.search(fname):
                cand = "HDR"
            else:
                cand = None
            file_best = _better(file_best, cand)
    return file_best


# ---- Source ------------------------------------------------------------------

_SOURCES = {
    r"\b(REMUX|BDREMUX|BD-REMUX)\b": "Remux",
    r"\b(BLURAY|BD|BLU-RAY|BD1080P)\b": "Blu-ray",
    r"\bBDRIP\b": "Blu-ray Rip",
    r"\bWEB-DL|WEBDL\b": "Web-DL",
    r"\bWEBRIP\b": "WebRip",
    r"\bVODRIP\b": "VOD Rip",
    r"\bHDRIP\b": "HD Rip",
    r"\bHR-HDTV|HRHDTV\b": "HR-HDTV",
    r"\bHDTV\b": "HDTV",
    r"\bPDTV\b": "PDTV",
    r"\bDVD\b": "DVD",
    r"\bDVDRIP\b": "DVD Rip",
    r"\bDVDSCR\b": "DVD Screener",
    r"\bR5\b": "R5",
    r"\bLDRIP\b": "LD Rip",
    r"\bPPVRIP\b": "PPV Rip",
    r"\bSDTV\b": "SDTV",
    r"\bTVRIP\b": "TV Rip",
    r"\bVHSRIP\b": "VHS Rip",
    r"\bHDTC|HD-TC\b": "HDTC",
    r"\bTC\b": "TC",
    r"\bHDCAM|HD-CAM\b": "HDCAM",
    r"\bHQCAM|HQ-CAM\b": "HQCAM",
    r"\bTS\b": "TS",
    r"\bCAM\b": "CAM",
}


def _match_source(text: str) -> str | None:
    for pattern, label in _SOURCES.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


@provider("Source", "source")
def source(ctx: MovieContext) -> str | None:
    found = _match_source(ctx.file_name.upper())
    if found:
        return found
    for media in ctx.movie.get("Media", []):
        for part in media.get("Part", []):
            for stream in part.get("Stream", []):
                if stream.get("streamType") == 1:
                    title = stream.get("title") or stream.get("displayTitle") or ""
                    if title:
                        found = _match_source(title.upper())
                        if found:
                            return found
    return None
