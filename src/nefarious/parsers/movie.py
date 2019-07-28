import regex
from nefarious.parsers.base import ParserBase

# https://github.com/Radarr/Radarr/blob/64e8fde0e1881cd8a61e34619c85e4334da291f8/src/NzbDrone.Core/Parser/Parser.cs


class MovieParser(ParserBase):

    media_regex_list = [
        # Some german or french tracker formats
        (
            'Some german or french tracker formats',
            regex.compile(r"^(?<title>(?![(\[]).+?)((\W|_))(?:(?<!(19|20)\d{2}.)(German|French|TrueFrench))(.+?)(?=((19|20)\d{2}|$))(?<year>(19|20)\d{2}(?!p|i|\d+|\]|\W\d+))?(\W+|_|$)(?!\\)", regex.I),
        ),

        # Special, Despecialized, etc. Edition Movies, e.g: Mission.Impossible.3.Special.Edition.2011
        (
            'Special, Despecialized, etc. Edition Movies, e.g: Mission.Impossible.3.Special.Edition.2011',
            regex.compile(r"^(?<title>(?![(\[]).+?)?(?:(?:[-_\W](?<![)\[!]))*\(?(?<edition>(((Extended.|Ultimate.)?(Director.?s|Collector.?s|Theatrical|Ultimate|Final(?=(.(Cut|Edition|Version)))|Extended|Rogue|Special|Despecialized|\d{2,3}(th)?.Anniversary)(.(Cut|Edition|Version))?(.(Extended|Uncensored|Remastered|Unrated|Uncut|IMAX|Fan.?Edit))?|((Uncensored|Remastered|Unrated|Uncut|IMAX|Fan.?Edit|Edition|Restored|((2|3|4)in1))))))\)?.{1,3}(?<year>(19|20)\d{2}(?!p|i|\d+|\]|\W\d+)))+(\W+|_|$)(?!\\)", regex.I),
        ),

        # Normal movie format, e.g: Mission.Impossible.3.2011
        (
            'Normal movie format, e.g: Mission.Impossible.3.2011',
            regex.compile(r"^(?<title>(?![(\[]).+?)?(?:(?:[-_\W](?<![)\[!]))*(?<year>(19|20)\d{2}(?!p|i|(19|20)\d{2}|\]|\W(19|20)\d{2})))+(\W+|_|$)(?!\\)", regex.I),
        ),

        # PassThePopcorn Torrent names: Star.Wars[PassThePopcorn]
        (
            'PassThePopcorn Torrent names: Star.Wars[PassThePopcorn]',
            regex.compile(r"^(?<title>.+?)?(?:(?:[-_\W](?<![()\[!]))*(?<year>(\[\w *\])))+(\W+|_|$)(?!\\)", regex.I),
        ),

        # That did not work? Maybe some tool uses [] for years. Who would do that?
        (
            'That did not work? Maybe some tool uses [] for years. Who would do that?',
            regex.compile(r"^(?<title>(?![(\[]).+?)?(?:(?:[-_\W](?<![)!]))*(?<year>(19|20)\d{2}(?!p|i|\d+|\W\d+)))+(\W+|_|$)(?!\\)", regex.I),
        ),

        # As a last resort for movies that have ( or [ in their title.
        (
            'As a last resort for movies that have ( or [ in their title.',
            regex.compile(r"^(?<title>.+?)?(?:(?:[-_\W](?<![)\[!]))*(?<year>(19|20)\d{2}(?!p|i|\d+|\]|\W\d+)))+(\W+|_|$)(?!\\)", regex.I),
        ),
    ]

    def _is_match(self, title, year: str = None) -> bool:
        if not self.match:
            return False

        title_matches = self.match.get('title') == self.normalize_media_title(title)

        # match year if the media and parser included it
        if year and 'year' in self.match:
            year_matches = year in self.match['year']
            return title_matches and year_matches

        return title_matches
