import regex
from nefarious.profiles import media_extensions


class ParserBase:
    media_matches = list()

    word_delimiter_regex = regex.compile(r"(\s|\.|,|_|-|=|\|)+")
    punctuation_regex = regex.compile(r"[^\w\s]")
    common_word_regex = regex.compile(r"\b(a|an|the|and|or|of)\b\s?", regex.I)
    duplicate_spaces_regex = regex.compile(r"\s{2,}")
    file_extension_regex = regex.compile(r"\.[a-z0-9]{2,4}$", regex.I)
    simple_title_regex = regex.compile(r"(?:(480|720|1080|2160)[ip]|[xh][\W_]?26[45]|DD\W?5\W1|[<>?*:|]|848x480|1280x720|1920x1080|3840x2160|4096x2160|(8|10)b(it)?)\s*", regex.I)
    website_prefix_regex = regex.compile(r"^\[\s*[a-z]+(\.[a-z]+)+\s*\][- ]*|^www\.[a-z]+\.(?:com|net)[ -]*", regex.I)
    clean_torrent_suffix_regex = regex.compile(r"\[(?:ettv|rartv|rarbg|cttv)\]$", regex.I)
    clean_quality_brackets_regex = regex.compile(r"\[[a-z0-9 ._-]+\]$")

    @staticmethod
    def _parse_number_word(number: str):
        numbers = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
        if number.isalpha():
            number = number.lower()
            return numbers.index(number) if number in numbers else None

    def matches(self, name):
        results = []
        for match_name, match_re in self.media_matches:
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
