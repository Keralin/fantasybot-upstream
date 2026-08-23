"""Captain helper (premium leagues): a pure, deterministic pick.

The captain doubles his points this gameweek, so the helper must name the XI's
best expected scorer — recent form tilted by start probability — and only ever an
available starter (an injured filler scores 0, so captaining him wastes the double).
"""

import unittest

from fantasybot.strategy.captain import captain_value, form, pick_captain


def _cand(pid, avg=None, points=None, last=None, value=0, prob=None, disponible=True):
    pm = {"id": f"m{pid}", "marketValue": value}
    if avg is not None:
        pm["averagePoints"] = avg
    if points is not None:
        pm["points"] = points
    if last is not None:
        pm["lastSeasonPoints"] = last
    return {"playerTeamId": pid, "playerMaster": pm, "prob": prob, "disponible": disponible}


class TestForm(unittest.TestCase):
    def test_prefers_average_then_points_then_last(self):
        self.assertEqual(form({"averagePoints": 7, "points": 100, "lastSeasonPoints": 200}), 7.0)
        self.assertEqual(form({"points": 100, "lastSeasonPoints": 200}), 100.0)
        self.assertEqual(form({"lastSeasonPoints": 200}), 200.0)
        self.assertEqual(form({}), 0.0)


class TestPickCaptain(unittest.TestCase):
    def test_picks_highest_form_starter(self):
        xi = [_cand("a", avg=4), _cand("b", avg=9), _cand("c", avg=6)]
        self.assertEqual(pick_captain(xi), "b")

    def test_probability_breaks_close_form(self):
        # equal form, but one is a nailed starter (95%) vs a rotation risk (20%)
        xi = [_cand("nailed", avg=6, prob=95), _cand("rotates", avg=6, prob=20)]
        self.assertEqual(pick_captain(xi), "nailed")

    def test_ignores_unavailable_players(self):
        # the highest-form player is injured -> he must NOT be captained (scores 0)
        xi = [_cand("star", avg=12, disponible=False), _cand("fit", avg=5, disponible=True)]
        self.assertEqual(pick_captain(xi), "fit")

    def test_none_when_no_eligible(self):
        self.assertIsNone(pick_captain([]))
        self.assertIsNone(pick_captain([_cand("x", avg=5, disponible=False)]))

    def test_captain_value_is_pure_number(self):
        v = captain_value(_cand("a", avg=5, value=10_000_000, prob=80))
        self.assertIsInstance(v, float)


if __name__ == "__main__":
    unittest.main()
