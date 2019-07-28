import regex
from nefarious.parsers.base import ParserBase


# https://github.com/Sonarr/Sonarr/blob/baf8f6cca637f76db64957c1871420196630dad3/src/NzbDrone.Core/Parser/Parser.cs


class TVParser(ParserBase):

    special_episode_word_regex = regex.compile(r"\b(part|special|edition|christmas)\b\s?", regex.I)

    media_regex_list = [
        # Multi-Part episodes without a title (S01E05.S01E06)
        (
            'Multi-Part episodes without a title (S01E05.S01E06)',
            regex.compile(r"^(?:\W*S?(?<season>(?<!\d+)(?:\d{1,2}|\d{4})(?!\d+))(?:(?:[ex]){1,2}(?<episode>\d{1,3}(?!\d+)))+){2,}", regex.I),
        ),

        # Episodes without a title, Multi (S01E04E05, 1x04x05, etc)
        (
            'Episodes without a title, Multi (S01E04E05, 1x04x05, etc)',
            regex.compile(r"^(?:S?(?<season>(?<!\d+)(?:\d{1,2}|\d{4})(?!\d+))(?:(?:[-_]|[ex]){1,2}(?<episode>\d{2,3}(?!\d+))){2,})", regex.I),
        ),

        # Episodes without a title, Single (S01E05, 1x05)
        (
            'Episodes without a title, Single (S01E05, 1x05)',
            regex.compile(r"^(?:S?(?<season>(?<!\d+)(?:\d{1,2}|\d{4})(?!\d+))(?:(?:[-_ ]?[ex])(?<episode>\d{2,3}(?!\d+))))", regex.I),
        ),

        # Anime - [SubGroup] Title Episode Absolute Episode Number ([SubGroup] Series Title Episode 01)
        (
            'Anime - [SubGroup] Title Episode Absolute Episode Number ([SubGroup] Series Title Episode 01)',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\][-_. ]?)(?<title>.+?)[-_. ](?:Episode)(?:[-_. ]+(?<absoluteepisode>(?<!\d+)\d{2,3}(?!\d+)))+(?:_|-|\s|\.)*?(?<hash>\[.{8}\])?(?:$|\.)?", regex.I),
        ),

        # Anime - [SubGroup] Title Absolute Episode Number + Season+Episode
        (
            'Anime - [SubGroup] Title Absolute Episode Number + Season+Episode',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\](?:_|-|\s|\.)?)(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+(?<absoluteepisode>\d{2,3}))+(?:_|-|\s|\.)+(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:\-|[ex]|\W[ex]){1,2}(?<episode>\d{2}(?!\d+)))+).*?(?<hash>[(\[]\w{8}[)\]])?(?:$|\.)", regex.I),
        ),

        # Anime - [SubGroup] Title Season+Episode + Absolute Episode Number
        (
            'Anime - [SubGroup] Title Season+Episode + Absolute Episode Number',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\](?:_|-|\s|\.)?)(?<title>.+?)(?:[-_\W](?<![()\[!]))+(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:\-|[ex]|\W[ex]){1,2}(?<episode>\d{2}(?!\d+)))+)(?:(?:_|-|\s|\.)+(?<absoluteepisode>(?<!\d+)\d{2,3}(?!\d+)))+.*?(?<hash>\[\w{8}\])?(?:$|\.)", regex.I),
        ),

        # Anime - [SubGroup] Title Season+Episode
        (
            'Anime - [SubGroup] Title Season+Episode',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\](?:_|-|\s|\.)?)(?<title>.+?)(?:[-_\W](?<![()\[!]))+(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:[ex]|\W[ex]){1,2}(?<episode>\d{2}(?!\d+)))+)(?:\s|\.).*?(?<hash>\[\w{8}\])?(?:$|\.)", regex.I),
        ),

        # Anime - [SubGroup] Title with trailing number Absolute Episode Number
        (
            'Anime - [SubGroup] Title with trailing number Absolute Episode Number',
            regex.compile(r"^\[(?<subgroup>.+?)\][-_. ]?(?<title>[^-]+?\d+?)[-_. ]+(?:[-_. ]?(?<absoluteepisode>\d{3}(?!\d+)))+(?:[-_. ]+(?<special>special|ova|ovd))?.*?(?<hash>\[\w{8}\])?(?:$|\.mkv)", regex.I),
        ),

        # Anime - [SubGroup] Title - Absolute Episode Number
        (
            'Anime - [SubGroup] Title - Absolute Episode Number',
            regex.compile(r"^\[(?<subgroup>.+?)\][-_. ]?(?<title>.+?)(?:[. ]-[. ](?<absoluteepisode>\d{2,3}(?!\d+|[-])))+(?:[-_. ]+(?<special>special|ova|ovd))?.*?(?<hash>\[\w{8}\])?(?:$|\.mkv)", regex.I),
        ),

        # Anime - [SubGroup] Title Absolute Episode Number
        (
            'Anime - [SubGroup] Title Absolute Episode Number',
            regex.compile(r"^\[(?<subgroup>.+?)\][-_. ]?(?<title>.+?)[-_. ]+\(?(?:[-_. ]?#?(?<absoluteepisode>\d{2,3}(?!\d+)))+\)?(?:[-_. ]+(?<special>special|ova|ovd))?.*?(?<hash>\[\w{8}\])?(?:$|\.mkv)", regex.I),
        ),

        # Multi-episode Repeated (S01E05 - S01E06, 1x05 - 1x06, etc)
        (
            'Multi-episode Repeated (S01E05 - S01E06, 1x05 - 1x06, etc)',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+S?(?<season>(?<!\d+)(?:\d{1,2}|\d{4})(?!\d+))(?:(?:[ex]|[-_. ]e){1,2}(?<episode>\d{1,3}(?!\d+)))+){2,}", regex.I),
        ),

        # Single episodes with a title (S01E05, 1x05, etc) and trailing info in slashes
        (
            'Single episodes with a title (S01E05, 1x05, etc) and trailing info in slashes',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+S?(?<season>(?<!\d+)(?:\d{1,2})(?!\d+))(?:[ex]|\W[ex]|_){1,2}(?<episode>\d{2,3}(?!\d+|(?:[ex]|\W[ex]|_|-){1,2}\d+))).+?(?:\[.+?\])(?!\\)", regex.I),
        ),

        # Anime - Title Season EpisodeNumber + Absolute Episode Number [SubGroup]
        (
            'Anime - Title Season EpisodeNumber + Absolute Episode Number [SubGroup]',
            regex.compile(r"^(?<title>.+?)(?:[-_\W](?<![()\[!]))+(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:[ex]|\W[ex]){1,2}(?<episode>(?<!\d+)\d{2}(?!\d+)))).+?(?:[-_. ]?(?<absoluteepisode>(?<!\d+)\d{3}(?!\d+)))+.+?\[(?<subgroup>.+?)\](?:$|\.mkv)", regex.I),
        ),

        # Multi-Episode with a title (S01E05E06, S01E05-06, S01E05 E06, etc) and trailing info in slashes
        (
            'Multi-Episode with a title (S01E05E06, S01E05-06, S01E05 E06, etc) and trailing info in slashes',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+S?(?<season>(?<!\d+)(?:\d{1,2})(?!\d+))(?:[ex]|\W[ex]|_){1,2}(?<episode>\d{2,3}(?!\d+))(?:(?:\-|[ex]|\W[ex]|_){1,2}(?<episode>\d{2,3}(?!\d+)))+).+?(?:\[.+?\])(?!\\)", regex.I),
        ),

        # Anime - Title Absolute Episode Number [SubGroup]
        (
            'Anime - Title Absolute Episode Number [SubGroup]',
            regex.compile(r"^(?<title>.+?)(?:(?:_|-|\s|\.)+(?<absoluteepisode>\d{3}(?!\d+)))+(?:.+?)\[(?<subgroup>.+?)\].*?(?<hash>\[\w{8}\])?(?:$|\.)", regex.I),
        ),

        # Anime - Title Absolute Episode Number [Hash]
        (
            'Anime - Title Absolute Episode Number [Hash]',
            regex.compile(r"^(?<title>.+?)(?:(?:_|-|\s|\.)+(?<absoluteepisode>\d{2,3}(?!\d+)))+(?:[-_. ]+(?<special>special|ova|ovd))?[-_. ]+.*?(?<hash>\[\w{8}\])(?:$|\.)", regex.I),
        ),

        # Episodes with airdate AND season/episode number, capture season/epsiode only
        (
            'Episodes with airdate AND season/episode number, capture season/epsiode only',
            regex.compile(r"^(?<title>.+?)?\W*(?<airdate>\d{4}\W+[0-1][0-9]\W+[0-3][0-9])(?!\W+[0-3][0-9])[-_. ](?:s?(?<season>(?<!\d+)(?:\d{1,2})(?!\d+)))(?:[ex](?<episode>(?<!\d+)(?:\d{1,3})(?!\d+)))", regex.I),
        ),

        # Episodes with airdate AND season/episode number
        (
            'Episodes with airdate AND season/episode number',
            regex.compile(r"^(?<title>.+?)?\W*(?<airyear>\d{4})\W+(?<airmonth>[0-1][0-9])\W+(?<airday>[0-3][0-9])(?!\W+[0-3][0-9]).+?(?:s?(?<season>(?<!\d+)(?:\d{1,2})(?!\d+)))(?:[ex](?<episode>(?<!\d+)(?:\d{1,3})(?!\d+)))", regex.I),
        ),

        # Episodes with a title, Single episodes (S01E05, 1x05, etc) & Multi-episode (S01E05E06, S01E05-06, S01E05 E06, etc)
        (
            'Episodes with a title, Single episodes (S01E05, 1x05, etc) & Multi-episode (S01E05E06, S01E05-06, S01E05 E06, etc)',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+S?(?<season>(?<!\d+)(?:\d{1,2})(?!\d+))(?:[ex]|\W[ex]){1,2}(?<episode>\d{2,3}(?!\d+))(?:(?:\-|[ex]|\W[ex]|_){1,2}(?<episode>\d{2,3}(?!\d+)))*)\W?(?!\\)", regex.I),
        ),

        # Episodes with a title, 4 digit season number, Single episodes (S2016E05, etc) & Multi-episode (S2016E05E06, S2016E05-06, S2016E05 E06, etc)
        (
            'Episodes with a title, 4 digit season number, Single episodes (S2016E05, etc) & Multi-episode (S2016E05E06, S2016E05-06, S2016E05 E06, etc)',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+S(?<season>(?<!\d+)(?:\d{4})(?!\d+))(?:e|\We|_){1,2}(?<episode>\d{2,3}(?!\d+))(?:(?:\-|e|\We|_){1,2}(?<episode>\d{2,3}(?!\d+)))*)\W?(?!\\)", regex.I),
        ),

        # Episodes with a title, 4 digit season number, Single episodes (2016x05, etc) & Multi-episode (2016x05x06, 2016x05-06, 2016x05 x06, etc)
        (
            'Episodes with a title, 4 digit season number, Single episodes (2016x05, etc) & Multi-episode (2016x05x06, 2016x05-06, 2016x05 x06, etc)',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+(?<season>(?<!\d+)(?:\d{4})(?!\d+))(?:x|\Wx){1,2}(?<episode>\d{2,3}(?!\d+))(?:(?:\-|x|\Wx|_){1,2}(?<episode>\d{2,3}(?!\d+)))*)\W?(?!\\)", regex.I),
        ),

        #  Partial season pack
        (
            'Partial season pack',
            regex.compile(r"^(?<title>.+?)(?:\W+S(?<season>(?<!\d+)(?:\d{1,2})(?!\d+))\W+(?:(?:Part\W?|(?<!\d+\W+)e)(?<seasonpart>\d{1,2}(?!\d+)))+)", regex.I),
        ),

        # Mini-Series with year in title, treated as season 1, episodes are labelled as Part01, Part 01, Part.1
        (
            'Mini-Series with year in title, treated as season 1, episodes are labelled as Part01, Part 01, Part.1',
            regex.compile(r"^(?<title>.+?\d{4})(?:\W+(?:(?:Part\W?|e)(?<episode>\d{1,2}(?!\d+)))+)", regex.I),
        ),

        # Mini-Series, treated as season 1, multi episodes are labelled as E1-E2
        (
            'Mini-Series, treated as season 1, multi episodes are labelled as E1-E2',
            regex.compile(r"^(?<title>.+?)(?:[-._ ][e])(?<episode>\d{2,3}(?!\d+))(?:(?:\-?[e])(?<episode>\d{2,3}(?!\d+)))+", regex.I),
        ),

        # Mini-Series, treated as season 1, episodes are labelled as Part01, Part 01, Part.1
        (
            'Mini-Series, treated as season 1, episodes are labelled as Part01, Part 01, Part.1',
            regex.compile(r"^(?<title>.+?)(?:\W+(?:(?:Part\W?|(?<!\d+\W+)e)(?<episode>\d{1,2}(?!\d+)))+)", regex.I),
        ),

        # Mini-Series, treated as season 1, episodes are labelled as Part One/Two/Three/...Nine, Part.One, Part_One
        (
            'Mini-Series, treated as season 1, episodes are labelled as Part One/Two/Three/...Nine, Part.One, Part_One',
            regex.compile(r"^(?<title>.+?)(?:\W+(?:Part[-._ ](?<episode>One|Two|Three|Four|Five|Six|Seven|Eight|Nine)(?>[-._ ])))", regex.I),
        ),

        # Mini-Series, treated as season 1, episodes are labelled as XofY
        (
            'Mini-Series, treated as season 1, episodes are labelled as XofY',
            regex.compile(r"^(?<title>.+?)(?:\W+(?:(?<episode>(?<!\d+)\d{1,2}(?!\d+))of\d+)+)", regex.I),
        ),

        # Supports Season 01 Episode 03
        (
            'Supports Season 01 Episode 03',
            regex.compile(r'(?:.*(?:"|^))(?<title>.*?)(?:[-_\W](?<![()\[]))+(?:\W?Season\W?)(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:\W|_)+(?:Episode\W)(?:[-_. ]?(?<episode>(?<!\d+)\d{1,2}(?!\d+)))+', regex.I),
        ),

        #  Multi-episode with episodes in square brackets (Series Title [S01E11E12] or Series Title [S01E11-12])
        (
            'Multi-episode with episodes in square brackets (Series Title [S01E11E12] or Series Title [S01E11-12])',
            regex.compile(r"(?:.*(?:^))(?<title>.*?)[-._ ]+\[S(?<season>(?<!\d+)\d{2}(?!\d+))(?:[E-]{1,2}(?<episode>(?<!\d+)\d{2}(?!\d+)))+\]", regex.I),
        ),

        # Multi-episode release with no space between series title and season (S01E11E12)
        (
            'Multi-episode release with no space between series title and season (S01E11E12)',
            regex.compile(r"(?:.*(?:^))(?<title>.*?)S(?<season>(?<!\d+)\d{2}(?!\d+))(?:E(?<episode>(?<!\d+)\d{2}(?!\d+)))+", regex.I),
        ),

        # Multi-episode with single episode numbers (S6.E1-E2, S6.E1E2, S6E1E2, etc)
        (
            'Multi-episode with single episode numbers (S6.E1-E2, S6.E1E2, S6E1E2, etc)',
            regex.compile(r"^(?<title>.+?)[-_. ]S(?<season>(?<!\d+)(?:\d{1,2}|\d{4})(?!\d+))(?:[-_. ]?[ex]?(?<episode>(?<!\d+)\d{1,2}(?!\d+)))+", regex.I),
        ),

        # Single episode season or episode S1E1 or S1-E1 or S1.Ep1
        (
            'Single episode season or episode S1E1 or S1-E1 or S1.Ep1',
            regex.compile(r'(?:.*(?:"|^))(?<title>.*?)(?:\W?|_)S(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:\W|_)?Ep?(?<episode>(?<!\d+)\d{1,2}(?!\d+))', regex.I),

        ),

        # 3 digit season S010E05
        (
            '3 digit season S010E05',
            regex.compile(r'(?:.*(?:"|^))(?<title>.*?)(?:\W?|_)S(?<season>(?<!\d+)\d{3}(?!\d+))(?:\W|_)?E(?<episode>(?<!\d+)\d{1,2}(?!\d+))', regex.I),
        ),

        # 5 digit episode number with a title
        (
            '5 digit episode number with a title',
            regex.compile(r"^(?:(?<title>.+?)(?:_|-|\s|\.)+)(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+)))(?:(?:\-|[ex]|\W[ex]|_){1,2}(?<episode>(?<!\d+)\d{5}(?!\d+)))", regex.I),
        ),

        # 5 digit multi-episode with a title
        (
            '5 digit multi-episode with a title',
            regex.compile(r"^(?:(?<title>.+?)(?:_|-|\s|\.)+)(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+)))(?:(?:[-_. ]{1,3}ep){1,2}(?<episode>(?<!\d+)\d{5}(?!\d+)))+", regex.I),
        ),

        #  Separated season and episode numbers S01 - E01
        (
            'Separated season and episode numbers S01 - E01',
            regex.compile(r"^(?<title>.+?)(?:_|-|\s|\.)+S(?<season>\d{2}(?!\d+))(\W-\W)E(?<episode>(?<!\d+)\d{2}(?!\d+))(?!\\)", regex.I),
        ),

        #  Anime - Title with season number - Absolute Episode Number (Title S01 - EP14)
        (
            'Anime - Title with season number - Absolute Episode Number (Title S01 - EP14)',
            regex.compile(r"^(?<title>.+?S\d{1,2})[-_. ]{3,}(?:EP)?(?<absoluteepisode>\d{2,3}(?!\d+|[-]))", regex.I),
        ),

        # *DIFF*:  added "Series" pattern
        # Season only releases
        (
            'Season only releases',
            regex.compile(r"^(?<title>.+?)\W(?:S|Season|Series)\W?(?<season>\d{1,2}(?!\d+))(\W+|_|$)(?<extras>EXTRAS|SUBPACK)?(?!\\)", regex.I),
        ),

        # 4 digit season only releases
        (
            '4 digit season only releases',
            regex.compile(r"^(?<title>.+?)\W(?:S|Season)\W?(?<season>\d{4}(?!\d+))(\W+|_|$)(?<extras>EXTRAS|SUBPACK)?(?!\\)", regex.I),
        ),

        # Episodes with a title and season/episode in square brackets
        (
            'Episodes with a title and season/episode in square brackets',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+\[S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:\-|[ex]|\W[ex]|_){1,2}(?<episode>(?<!\d+)\d{2}(?!\d+|i|p)))+\])\W?(?!\\)", regex.I),
        ),

        # Supports 103/113 naming
        (
            'Supports 103/113 naming',
            regex.compile(r"^(?<title>.+?)?(?:(?:[-_\W](?<![()\[!]))+(?<season>(?<!\d+)[1-9])(?<episode>[1-9][0-9]|[0][1-9])(?![a-z]|\d+))+", regex.I),
        ),

        # 4 digit episode number - Episodes without a title, Single (S01E05, 1x05) AND Multi (S01E04E05, 1x04x05, etc)
        (
            '4 digit episode number - Episodes without a title, Single (S01E05, 1x05) AND Multi (S01E04E05, 1x04x05, etc)',
            regex.compile(r"^(?:S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:\-|[ex]|\W[ex]|_){1,2}(?<episode>\d{4}(?!\d+|i|p)))+)(\W+|_|$)(?!\\)", regex.I),
        ),

        # 4 digit episode number - Episodes with a title, Single episodes (S01E05, 1x05, etc) & Multi-episode (S01E05E06, S01E05-06, S01E05 E06, etc)
        (
            '4 digit episode number - Episodes with a title, Single episodes (S01E05, 1x05, etc) & Multi-episode (S01E05E06, S01E05-06, S01E05 E06, etc)',
            regex.compile(r"^(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:\-|[ex]|\W[ex]|_){1,2}(?<episode>\d{4}(?!\d+|i|p)))+)\W?(?!\\)", regex.I),
        ),

        # Episodes with airdate (2018.04.28)
        (
            'Episodes with airdate (2018.04.28)',
            regex.compile(r"^(?<title>.+?)?\W*(?<airyear>\d{4})[-_. ]+(?<airmonth>[0-1][0-9])[-_. ]+(?<airday>[0-3][0-9])(?![-_. ]+[0-3][0-9])", regex.I),
        ),

        # Episodes with airdate (04.28.2018)
        (
            'Episodes with airdate (04.28.2018)',
            regex.compile(r"^(?<title>.+?)?\W*(?<airmonth>[0-1][0-9])[-_. ]+(?<airday>[0-3][0-9])[-_. ]+(?<airyear>\d{4})(?!\d+)", regex.I),
        ),

        # Supports 1103/1113 naming
        (
            'Supports 1103/1113 naming',
            regex.compile(r"^(?<title>.+?)?(?:(?:[-_\W](?<![()\[!]))*(?<season>(?<!\d+|\(|\[|e|x)\d{2})(?<episode>(?<!e|x)\d{2}(?!p|i|\d+|\)|\]|\W\d+|\W(?:e|ep|x)\d+)))+(\W+|_|$)(?!\\)", regex.I),
        ),

        # Episodes with single digit episode number (S01E1, S01E5E6, etc)
        (
            'Episodes with single digit episode number (S01E1, S01E5E6, etc)',
            regex.compile(r"^(?<title>.*?)(?:(?:[-_\W](?<![()\[!]))+S?(?<season>(?<!\d+)\d{1,2}(?!\d+))(?:(?:\-|[ex]){1,2}(?<episode>\d{1}))+)+(\W+|_|$)(?!\\)", regex.I),
        ),

        # iTunes Season 1\05 Title (Quality).ext
        (
            'iTunes Season 1\05 Title (Quality).ext',
            regex.compile(r"^(?:Season(?:_|-|\s|\.)(?<season>(?<!\d+)\d{1,2}(?!\d+)))(?:_|-|\s|\.)(?<episode>(?<!\d+)\d{1,2}(?!\d+))", regex.I),
        ),

        # iTunes 1-05 Title (Quality).ext
        (
            'iTunes 1-05 Title (Quality).ext',
            regex.compile(r"^(?:(?<season>(?<!\d+)(?:\d{1,2})(?!\d+))(?:-(?<episode>\d{2,3}(?!\d+))))", regex.I),
        ),

        # Anime - Title Absolute Episode Number (e66)
        (
            'Anime - Title Absolute Episode Number (e66)',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\][-_. ]?)?(?<title>.+?)(?:(?:_|-|\s|\.)+(?:e|ep)(?<absoluteepisode>\d{2,3}))+.*?(?<hash>\[\w{8}\])?(?:$|\.)", regex.I),
        ),

        # Anime - Title Episode Absolute Episode Number (Series Title Episode 01)
        (
            'Anime - Title Episode Absolute Episode Number (Series Title Episode 01)',
            regex.compile(r"^(?<title>.+?)[-_. ](?:Episode)(?:[-_. ]+(?<absoluteepisode>(?<!\d+)\d{2,3}(?!\d+)))+(?:_|-|\s|\.)*?(?<hash>\[.{8}\])?(?:$|\.)?", regex.I),
        ),

        # Anime - Title Absolute Episode Number
        (
            'Anime - Title Absolute Episode Number',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\][-_. ]?)?(?<title>.+?)(?:[-_. ]+(?<absoluteepisode>(?<!\d+)\d{2,3}(?!\d+)))+(?:_|-|\s|\.)*?(?<hash>\[.{8}\])?(?:$|\.)?", regex.I),
        ),

        # Anime - Title {Absolute Episode Number}
        (
            'Anime - Title {Absolute Episode Number}',
            regex.compile(r"^(?:\[(?<subgroup>.+?)\][-_. ]?)?(?<title>.+?)(?:(?:[-_\W](?<![()\[!]))+(?<absoluteepisode>(?<!\d+)\d{2,3}(?!\d+)))+(?:_|-|\s|\.)*?(?<hash>\[.{8}\])?(?:$|\.)?", regex.I),
        ),

        # Extant, terrible multi-episode naming (extant.10708.hdtv-lol.mp4)
        (
            'Extant, terrible multi-episode naming (extant.10708.hdtv-lol.mp4)',
            regex.compile(r"^(?<title>.+?)[-_. ](?<season>[0]?\d?)(?:(?<episode>\d{2}){2}(?!\d+))[-_. ]", regex.I),
        ),
    ]

    def normalize_season_episode(self, value: str):
        if value.isdigit():
            return int(value)
        else:
            return self._parse_number_word(value)

    def parse(self):
        title = self.normalize_title(self.title_query)

        matches = self.matches(title)

        if not matches:
            return None

        # get the first match
        self.match = matches[0]

        # single title
        if 'title' in self.match:
            self.match['title'] = self.normalize_media_title(self.match['title'][0])
        else:
            self.match['title'] = ''

        # parse multiple seasons
        if 'season' in self.match:
            for i, season in enumerate(self.match['season']):
                self.match['season'][i] = self.normalize_season_episode(season)
        # default to the first season
        else:
            self.match['season'] = [1]

        # parse multiple episodes
        if 'episode' in self.match:
            for i, episode in enumerate(self.match['episode']):
                self.match['episode'][i] = self.normalize_season_episode(episode)

        # quality
        title_quality = self.parse_quality(self.title_query)
        self.match['quality'] = title_quality.name
        self.match['resolution'] = self.parse_resolution(self.title_query)

        # hardcoded subs
        self.match['hc'] = self.parse_hardcoded_subs()

        return self.match

    def _is_match(self, title, season_number, episode_number=None):
        if episode_number is not None:
            return self._is_episode_match(title, season_number, episode_number)
        else:
            return self._is_season_match(title, season_number)

    def _is_season_match(self, title, season_number) -> bool:
        # verify no "episode" in match
        return self.match and 'title' in self.match and all([
            season_number in self.match.get('season'),
            'episode' not in self.match,
            self.match['title'] == self.normalize_media_title(title),
        ])

    def _is_episode_match(self, title, season_number, episode_number) -> bool:
        # must match title, season and episode
        return self.match and 'title' in self.match and all([
            season_number in self.match.get('season', []),
            episode_number in self.match.get('episode', []),
            self.match['title'] == self.normalize_media_title(title),
        ])
