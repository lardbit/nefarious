from nefarious.parsers.tv import TVParser
from django.test import TestCase


class TVImport(TestCase):
    tv_tests = []

    def setUp(self):
        self.tv_tests = [
        ]

    def test_tv(self):
        pass
        #for name, title, season in self.tv_tests:
            #parser = TVParser(name)
            #self.assertTrue(parser.is_match(title, season), '{} ({})'.format(name, parser.match))
