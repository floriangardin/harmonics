from harmonics.commons.to_ern import to_ern
from harmonics.commons.to_mxl import to_mxl
import json
from harmonics.score_models import Score


def test_to_ern():
    with open("tests/data/items.json", "r") as f:
        D = json.load(f)
    score = Score(**D)
    to_ern("tests/data/items.ern", score)
    to_mxl("tests/data/items.mxl", score)
