from harmonics.commons.to_ern import to_ern
from harmonics.commons.to_mxl import to_mxl
from harmonics.commons.from_mxl import from_mxl
import json
from harmonics.score_models import Score
from harmonics.parser import HarmonicsParser


def test_to_ern():
    score = HarmonicsParser().parse_to_score("tests/data/base_test.ern")
    to_ern("tests/data/items.ern", score)


def test_full_to_mxl():
    HarmonicsParser().parse_to_mxl(
        "tests/data/full_test.ern", "tests/data/full_test.mxl"
    )


def test_from_mxl():
    HarmonicsParser().parse_to_mxl(
        "tests/data/base_test.ern", "tests/data/base_test.mxl"
    )
    parser = HarmonicsParser()
    parser.parse_to_ern("tests/data/base_test.mxl", "tests/data/mxl_ern.ern")

    # Check that it is parsable
    score = parser.parse_to_score("tests/data/mxl_ern.ern")
