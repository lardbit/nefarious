import regex
from nefarious.quality import media_extensions, Resolution

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

            # resolution
            resolution = self._parse_resolution(name)
            self.match['resolution'] = resolution

    @staticmethod
    def _parse_number_word(number: str):
        numbers = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
        if number.isalpha():
            number = number.lower()
            return numbers.index(number) if number in numbers else None

    def _parse_quality(self, name):
        # TODO
        pass

    def _parse_resolution(self, name):
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
        match = self.file_extension_regex.search(title)
        if match:
            match_ext = match.group().lower()
            for ext, _ in media_extensions:
                if match_ext == ext:
                    title = title.replace(match_ext, '')

        title = self.simple_title_regex.sub(' ', title)
        title = self.clean_quality_brackets_regex.sub('', title)

        title = self.duplicate_spaces_regex.sub(' ', title)

        return title.strip().lower()

    def is_match(self, *args) -> bool:
        raise NotImplementedError
