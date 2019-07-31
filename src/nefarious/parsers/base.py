import regex
from nefarious import quality
from nefarious.quality import Resolution, Profile


# https://github.com/Sonarr/Sonarr/blob/537e4d7c39e839e75e7a7ad84e95cd582ec1d20e/src/NzbDrone.Core/Parser/QualityParser.cs
# https://github.com/Radarr/Radarr/blob/e01900628f86696469875dcb79f60071278100ba/src/NzbDrone.Core/Parser/QualityParser.cs


class ParserBase:
    title_query: str = None
    media_regex_list = list()
    match: dict = None

    word_delimiter_regex = regex.compile(r"(\s|\.|,|_|-|=|\|)+")
    punctuation_regex = regex.compile(r"[^\w\s]")
    common_word_regex = regex.compile(r"\b(a|an|the|and|or|of)\b\s?", regex.I)
    duplicate_spaces_regex = regex.compile(r"\s{2,}")
    file_extension_regex = regex.compile(r"\.[a-z0-9]{2,4}$", regex.I)
    simple_title_regex = regex.compile(r"(?:(480|720|1080|2160)[ip]|[xh][\W_]?26[45]|DD\W?5\W1|[<>?*:|]|848x480|1280x720|1920x1080|3840x2160|4096x2160|(8|10)b(it)?)\s*", regex.I)
    website_prefix_regex = regex.compile(r"^\[\s*[a-z]+(\.[a-z]+)+\s*\][- ]*|^www\.[a-z]+\.(?:com|net)[ -]*", regex.I)
    clean_torrent_suffix_regex = regex.compile(r"\[(?:ettv|rartv|rarbg|cttv)\]$", regex.I)
    clean_quality_brackets_regex = regex.compile(r"\[[a-z0-9 ._-]+\]$")
    resolution_regex = regex.compile(
        r"\b(?:"
        r"(?<R480p>480p|640x480|848x480)|"
        r"(?<R576p>576p)|"
        r"(?<R720p>720p|1280x720)|"
        r"(?<R1080p>1080p|1920x1080|1440p|FHD|1080i)|"
        r"(?<R2160p>2160p|4k[-_. ](?:UHD|HEVC|BD)|"
        r"(?:UHD|HEVC|BD)[-_. ]4k))\b",
        regex.I)
    source_regex = regex.compile(
        r"\b(?:"
        r"(?<bluray>BluRay|Blu-Ray|HD-?DVD|BD)|"
        r"(?<webdl>WEB[-_. ]DL|WEBDL|WebRip|AmazonHD|iTunesHD|NetflixU?HD|WebHD|[. ]WEB[. ](?:[xh]26[45]|DDP?5[. ]1)|\d+0p[. ]WEB[. ]|WEB-DLMux)|"
        r"(?<hdtv>HDTV)|"
        r"(?<bdrip>BDRip)|"
        r"(?<brrip>BRRip)|"
        r"(?<dvd>DVD|DVDRip|NTSC|PAL|xvidvd)|"
        r"(?<dsr>WS[-_. ]DSR|DSR)|"
        r"(?<regional>R[0-9]{1}|REGIONAL)|"
        r"(?<scr>SCR|SCREENER|DVDSCR|DVDSCREENER)|"
        r"(?<ts>TS|TELESYNC|HD-TS|HDTS|PDVD|TSRip|HDTSRip|HQ-TS)|"
        r"(?<tc>TC|TELECINE|HD-TC|HDTC)|"
        r"(?<cam>CAMRIP|CAM|HDCAM|HCAM|HDCAMRip|HD-CAM)|"
        r"(?<wp>WORKPRINT|WP)|"
        r"(?<pdtv>PDTV)|"
        r"(?<sdtv>SDTV)|"
        r"(?<tvrip>TVRip))\b",
        regex.I)
    anime_bluray_regex = regex.compile(r"bd(?:720|1080)|(?<=[-_. (\[])bd(?=[-_. )\]])", regex.I)
    high_def_pdtv_regex = regex.compile(r"hr[-_. ]ws", regex.I)
    raw_hd_regex = regex.compile(r"\b(?<rawhd>RawHD|1080i[-_. ]HDTV|Raw[-_. ]HD|MPEG[-_. ]?2)\b", regex.I)
    hardcoded_subs_regex = regex.compile(r"\b(?<hc>hc|korsub)\b", regex.I)

    def __init__(self, title):
        self.title_query = title
        self.parse()

    def parse(self):
        title = self.normalize_title(self.title_query)
        matches = self.matches(title)
        if matches:

            # get the first match
            self.match = matches[0]

            # title
            if 'title' in self.match and self.match['title']:
                self.match['title'] = self.normalize_media_title(self.match['title'][0])

            # quality
            title_quality = self.parse_quality(self.title_query)
            self.match['quality'] = title_quality.name
            self.match['resolution'] = self.parse_resolution(self.title_query)

            # hardcoded subs
            self.match['hc'] = self.parse_hardcoded_subs()

    def parse_hardcoded_subs(self):
        match = self.hardcoded_subs_regex.search(self.title_query)
        return True if match else False

    def parse_quality(self, name: str):
        name = name.strip().lower()
        resolution = self.parse_resolution(name)

        # raw hd match
        if self.raw_hd_regex.search(name):
            return quality.RAW_HD

        # source match
        match = self.source_regex.search(name)
        if match:
            result = match.capturesdict()

            if result['bluray']:
                if 'xvid' in name:
                    return quality.DVD
                if resolution == Resolution.R2160p:
                    return quality.BLURAY_2160P
                elif resolution == Resolution.R1080p:
                    return quality.BLURAY_1080P
                elif resolution in [Resolution.R480P, Resolution.R576p]:
                    return quality.DVD
                return quality.BLURAY_720P
            elif result['webdl']:
                if resolution == Resolution.R2160p:
                    return quality.WEBDL_2160P
                elif resolution == Resolution.R1080p:
                    return quality.WEBDL_1080P
                elif resolution == Resolution.R720p:
                    return quality.WEBDL_720P
                elif '[webdl]' in name:
                    return quality.WEBDL_720P
                return quality.WEBDL_480P
            elif result['hdtv']:
                if resolution == Resolution.R2160p:
                    return quality.HDTV_2160P
                elif resolution == Resolution.R1080p:
                    return quality.HDTV_1080P
                elif resolution == Resolution.R720p:
                    return quality.HDTV_720P
                elif '[hdtv]' in name:
                    return quality.HDTV_720P
                return quality.SDTV
            elif result['brrip'] or result['bdrip']:
                if resolution == Resolution.R2160p:
                    return quality.BLURAY_2160P
                elif resolution == Resolution.R1080p:
                    return quality.BLURAY_1080P
                elif resolution == Resolution.R720p:
                    return quality.BLURAY_720P
                return quality.DVD
            elif result['dvd']:
                return quality.DVD
            elif result['cam']:
                return quality.CAM
            elif result['scr']:
                return quality.DVDSCR
            elif result['regional']:
                return quality.REGIONAL
            elif result['ts']:
                return quality.TELESYNC
            elif result['tc']:
                return quality.TELECINE
            elif any([result['pdtv'], result['sdtv'], result['dsr'], result['tvrip']]):
                if resolution == Resolution.R1080p or '1080p' in name:
                    return quality.HDTV_1080P
                elif resolution == Resolution.R720p or '720p' in name:
                    return quality.HDTV_720P
                elif self.high_def_pdtv_regex.search(name):
                    return quality.HDTV_720P
                return quality.SDTV

            return quality.UNKNOWN

        elif self.anime_bluray_regex.search(name):
            if resolution in [Resolution.R480P, Resolution.R576p] or '480p' in name:
                return quality.DVD
            elif resolution == Resolution.R1080p or '1080p' in name:
                return quality.BLURAY_1080P
            return quality.BLURAY_720P

        elif resolution == Resolution.R2160p:
            return quality.HDTV_2160P
        elif resolution == Resolution.R1080p:
            return quality.HDTV_1080P
        elif resolution == Resolution.R720p:
            return quality.HDTV_720P
        elif resolution == Resolution.R480P:
            return quality.SDTV

        elif 'x264' in name:
            return quality.SDTV

        elif '848x480' in name:
            if 'dvd' in name:
                return quality.DVD
            return quality.SDTV

        elif '1280x720' in name:
            if 'bluray' in name:
                return quality.BLURAY_720P
            return quality.HDTV_720P

        elif '1920x1080' in name:
            if 'bluray' in name:
                return quality.BLURAY_1080P
            return quality.HDTV_1080P

        elif 'bluray720p' in name:
            return quality.BLURAY_720P

        elif 'bluray1080p' in name:
            return quality.BLURAY_1080P

        return quality.quality_from_extension(self._get_extension(name))

    def parse_resolution(self, name):
        match = self.resolution_regex.search(name)

        if not match:
            return Resolution.Unknown

        result = match.capturesdict()

        if result['R480p']:
            return Resolution.R480P
        if result['R576p']:
            return Resolution.R576p
        if result['R720p']:
            return Resolution.R720p
        if result['R1080p']:
            return Resolution.R1080p
        if result['R2160p']:
            return Resolution.R2160p

        return Resolution.Unknown

    def matches(self, name):
        results = []
        for match_name, match_re in self.media_regex_list:
            match = match_re.search(name)
            if match:
                result = match.capturesdict()
                result['match_name'] = match_name
                results.append(result)
        return results

    def normalize_media_title(self, title: str):
        title = self.word_delimiter_regex.sub(' ', title)
        title = self.punctuation_regex.sub('', title)
        title = self.common_word_regex.sub('', title)
        title = self.duplicate_spaces_regex.sub(' ', title)
        return title.strip().lower()

    def normalize_title(self, title: str):
        title = self.website_prefix_regex.sub('', title)
        title = self.clean_torrent_suffix_regex.sub('', title)

        # remove known extensions
        extension = self._get_extension(title)
        if extension:
            for ext, _ in quality.EXTENSIONS.items():
                if extension == ext:
                    title = title.replace(extension, '')
                    break

        title = self.simple_title_regex.sub(' ', title)
        title = self.clean_quality_brackets_regex.sub('', title)

        title = self.duplicate_spaces_regex.sub(' ', title)

        return title.strip().lower()

    def is_match(self, title, *args, **kwargs) -> bool:
        return self._is_match(title, *args, **kwargs)

    def is_quality_match(self, profile: Profile) -> bool:
        return self.match['quality'] in profile.qualities

    def is_hardcoded_subs_match(self, allows: bool) -> bool:
        if not allows and self.match['hc']:
            return False
        return True

    def is_keyword_search_filter_match(self, exclusions: list) -> bool:
        # break up the title into individual words to compare against
        words = regex.findall(r'\w+', self.title_query.lower())
        return not set([e.lower() for e in exclusions]).intersection(words)

    def _is_match(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def _get_extension(self, name):
        result = None
        match = self.file_extension_regex.search(name)
        if match:
            result = match.group().lower()
        return result

    @staticmethod
    def _parse_number_word(number: str):
        numbers = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
        if number.isalpha():
            number = number.lower()
            return numbers.index(number) if number in numbers else None
