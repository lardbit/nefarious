class Resolution:
    R480P = '480p'
    R576p = '576p'
    R720p = '720p'
    R1080p = '1080p'
    R2160p = '2160p'
    Unknown = 'unknown'


class Quality:
    weight: int
    name: str
    resolution: int

    def __init__(self, weight, name, resolution):
        self.weight = weight
        self.name = name
        self.resolution = resolution


class Profile:
    name: str
    qualities: list

    def __init__(self, name, qualities):
        self.name = name
        self.qualities = qualities

    def __eq__(self, other):
        return self.name == other.name


UNKNOWN = Quality(0, "Unknown", 0)
SDTV = Quality(1, "SDTV", 480)
DVD = Quality(2, "DVD", 480)
BLURAY_720P = Quality(6, "Bluray-720p", 720)
BLURAY_1080P = Quality(7, "Bluray-1080p", 1080)
BLURAY_2160P = Quality(19, "Bluray-2160p", 2160)
WEBDL_720P = Quality(5, "WEBDL-720p", 720)
WEBDL_480P = Quality(8, "WEBDL-480p", 480)
WEBDL_1080P = Quality(3, "WEBDL-1080p", 1080)
WEBDL_2160P = Quality(18, "WEBDL-2160p", 2160)
WEBRIP_720P = Quality(14, "WEBRip-720p", 720)
WEBRIP_1080P = Quality(15, "WEBRip-1080p", 1080)
WEBRIP_2160P = Quality(17, "WEBRip-2160p", 2160)
HDTV_720P = Quality(4, "HDTV-720p", 720)
HDTV_1080P = Quality(9, "HDTV-1080p", 1080)
HDTV_2160P = Quality(16, "HDTV-2160p", 2160)
RAW_HD = Quality(10, "Raw-HD", 1080)

QUALITIES = [
    UNKNOWN,
    SDTV,
    DVD,
    BLURAY_720P,
    BLURAY_1080P,
    BLURAY_2160P,
    WEBDL_720P,
    WEBDL_480P,
    WEBDL_1080P,
    WEBDL_2160P,
    WEBRIP_720P,
    WEBRIP_1080P,
    WEBRIP_2160P,
    HDTV_720P,
    HDTV_1080P,
    HDTV_2160P,
    RAW_HD,
]

QUALITY_NAMES = [q.name for q in QUALITIES]


PROFILE_ANY = Profile('any', [
    SDTV,
    WEBDL_480P,
    DVD,
    HDTV_720P,
    HDTV_1080P,
    WEBDL_720P,
    WEBDL_1080P,
    BLURAY_720P,
    BLURAY_1080P,
])

PROFILE_SD = Profile('sd', [
    SDTV,
    WEBDL_480P,
    DVD,
])

PROFILE_HD_720P = Profile('hd-720p', [
    HDTV_720P,
    WEBDL_720P,
    BLURAY_720P,
])

PROFILE_HD_1080p = Profile('hd-1080p', [
    HDTV_1080P,
    WEBDL_1080P,
    BLURAY_1080P,
])

PROFILE_ULTRA_HD = Profile('ultra-hd', [
    HDTV_2160P,
    WEBDL_2160P,
    BLURAY_2160P,
])

PROFILE_HD_720P_1080P = Profile('hd-720p-1080p', [
    HDTV_720P,
    HDTV_1080P,
    WEBDL_720P,
    WEBDL_1080P,
    BLURAY_720P,
    BLURAY_1080P,
])

PROFILES = [
    PROFILE_ANY, PROFILE_SD, PROFILE_HD_720P, PROFILE_HD_1080p, PROFILE_ULTRA_HD, PROFILE_HD_720P_1080P,
]

PROFILE_NAMES = [p.name for p in PROFILES]

EXTENSIONS = {
    # Unknown
    ".webm": UNKNOWN,

    # SDTV
    ".m4v": SDTV,
    ".3gp": SDTV,
    ".nsv": SDTV,
    ".ty": SDTV,
    ".strm": SDTV,
    ".rm": SDTV,
    ".rmvb": SDTV,
    ".m3u": SDTV,
    ".ifo": SDTV,
    ".mov": SDTV,
    ".qt": SDTV,
    ".divx": SDTV,
    ".xvid": SDTV,
    ".bivx": SDTV,
    ".nrg": SDTV,
    ".pva": SDTV,
    ".wmv": SDTV,
    ".asf": SDTV,
    ".asx": SDTV,
    ".ogm": SDTV,
    ".ogv": SDTV,
    ".m2v": SDTV,
    ".avi": SDTV,
    ".bin": SDTV,
    ".dat": SDTV,
    ".dvr-ms": SDTV,
    ".mpg": SDTV,
    ".mpeg": SDTV,
    ".mp4": SDTV,
    ".avc": SDTV,
    ".vp3": SDTV,
    ".svq3": SDTV,
    ".nuv": SDTV,
    ".viv": SDTV,
    ".dv": SDTV,
    ".fli": SDTV,
    ".flv": SDTV,
    ".wpl": SDTV,

    # DVD
    ".img": DVD,
    ".iso": DVD,
    ".vob": DVD,

    # HD
    ".mkv": HDTV_720P,
    ".ts": HDTV_720P,
    ".wtv": HDTV_720P,

    # Bluray
    ".m2ts": BLURAY_720P,
}


def quality_from_extension(extension):
    for ext, quality in EXTENSIONS.items():
        if ext == extension:
            return quality
    return UNKNOWN
