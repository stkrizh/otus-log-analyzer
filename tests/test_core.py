import unittest

from context import core


class TestCore(unittest.TestCase):
    def test_most_recent_filenames(self):
        filenames = [
            "nginx-access-ui.log-20170630.gz",
            "nginx-access-ui.log-20150629.gz",
            "nginx-access-ui.log-20150630.bz",
            "image.jpg",
            "nginx-access-ui.log-20150630.gz",
            "nginx-access-ui.log-20170701.log",
            "nginx-access-ui.log-20170701.gz",
            "nginx-access-XX.log-20191212.gz",
        ]

        self.assertEqual(
            "nginx-access-ui.log-20170701.log",
            core._most_recent_filename(filenames)
        )

    def test_isupper(self):
        self.assertTrue("FOO".isupper())
        self.assertFalse("Foo".isupper())

    def test_split(self):
        s = "hello world"
        self.assertEqual(s.split(), ["hello", "world"])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)
