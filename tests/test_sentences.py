import unittest

from lingogeek.sentences import split


class SplitTests(unittest.TestCase):
    def test_plain_sentences(self):
        self.assertEqual(
            split("One thing happened. Then another."),
            ["One thing happened.", "Then another."],
        )

    def test_titles_do_not_split(self):
        self.assertEqual(
            split("Please return it to Dr. Smith by five."),
            ["Please return it to Dr. Smith by five."],
        )

    def test_dotted_abbreviations_do_not_split(self):
        self.assertEqual(len(split("It shows the U.S.A. office and the Ltd. subsidiary.")), 1)

    def test_initials_do_not_split(self):
        self.assertEqual(len(split("The report was signed by J. Armstrong today.")), 1)

    def test_question_and_exclamation(self):
        self.assertEqual(split("Really? Yes! Fine."), ["Really?", "Yes!", "Fine."])

    def test_single_sentence_without_punctuation(self):
        self.assertEqual(split("No full stop here"), ["No full stop here"])

    def test_empty(self):
        self.assertEqual(split("   "), [])


if __name__ == "__main__":
    unittest.main()
