import regex
from nefarious import quality
from nefarious.quality import Resolution

# https://github.com/Sonarr/Sonarr/blob/master/src/NzbDrone.Core/Parser/Parser.cs
# https://github.com/Sonarr/Sonarr/blob/master/src/NzbDrone.Core/Parser/QualityParser.cs


class ParserBase:
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
    resolution_regex = regex.compile(r"\b(?:(?<R480p>480p|640x480|848x480)|(?<R576p>576p)|(?<R720p>720p|1280x720)|(?<R1080p>1080p|1920x1080|1440p|FHD|1080i)|(?<R2160p>2160p|4k[-_. ](?:UHD|HEVC|BD)|(?:UHD|HEVC|BD)[-_. ]4k))\b", regex.I)
    source_regex = regex.compile(r"\b(?:(?<bluray>BluRay|Blu-Ray|HD-?DVD|BD)|(?<webdl>WEB[-_. ]DL|WEBDL|WebRip|AmazonHD|iTunesHD|NetflixU?HD|WebHD|[. ]WEB[. ](?:[xh]26[45]|DD5[. ]1)|\d+0p[. ]WEB[. ]|WEB-DLMux)|(?<hdtv>HDTV)|(?<bdrip>BDRip)|(?<brrip>BRRip)|(?<dvd>DVD|DVDRip|NTSC|PAL|xvidvd)|(?<dsr>WS[-_. ]DSR|DSR)|(?<pdtv>PDTV)|(?<sdtv>SDTV)|(?<tvrip>TVRip))\b", regex.I)
    high_def_pdtv_regex = regex.compile(r"hr[-_. ]ws", regex.I)

    def __init__(self, title):
        self.parse(title)

    def parse(self, name):
        title = self.normalize_title(name)
        matches = self.matches(title)
        if matches:
            # get the first match
            self.match = matches[0]
            # single title
            if 'title' in self.match and self.match['title']:
                self.match['title'] = self.normalize_media_title(self.match['title'][0])

            # quality
            title_quality = self.parse_quality(name)
            self.match['quality'] = title_quality.name
            self.match['resolution'] = self.parse_resolution(name)

    def parse_quality(self, name: str):
        name = name.strip().lower()
        resolution = self.parse_resolution(name)
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
            elif any([result['pdtv'], result['sdtv'], result['dsr'], result['tvrip']]):
                if resolution == Resolution.R1080p or '1080p' in name:
                    return quality.HDTV_1080P
                elif resolution == Resolution.R720p or '720p' in name:
                    return quality.HDTV_720P
                elif self.high_def_pdtv_regex.search(name):
                    return quality.HDTV_720P
                return quality.SDTV

            return quality.UNKNOWN

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

        return quality.quality_from_extension(self._extension(name))

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

        # TODO - this may be unnecessary (use _extension function regardless)
        # remove known extensions
        match = self.file_extension_regex.search(title)
        if match:
            match_ext = match.group().lower()
            for ext, _ in quality.EXTENSIONS.items():
                if match_ext == ext:
                    title = title.replace(match_ext, '')

        title = self.simple_title_regex.sub(' ', title)
        title = self.clean_quality_brackets_regex.sub('', title)

        title = self.duplicate_spaces_regex.sub(' ', title)

        return title.strip().lower()

    def is_match(self, *args) -> bool:
        raise NotImplementedError

    def _extension(self, name):
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
