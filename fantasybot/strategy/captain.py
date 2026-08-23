"""Captain (and coach form) scoring for PREMIUM leagues.

In a premium league one starter can be named CAPTAIN and scores DOUBLE this
gameweek. That makes the pick pure upside — name the XI player most likely to
rack up the most points — and it is deterministic MATH, not an LLM decision:
recent form, tilted by how surely the player starts. The lineup optimizer calls
`pick_captain` while building a premium payload; nothing here has side effects.

The same `form` signal (a player's recent scoring rate) also ranks owned coaches,
so the helper lives here and the optimizer imports it for both.
"""


def form(pm):
    """A player's recent scoring form, read from the LaLiga playerMaster.

    Prefers this season's average points per game (`averagePoints`), then total
    `points`, then last season's points as a cold-start fallback. 0 when nothing
    is known — an unscored player simply ranks last, never crashes the pick.
    """
    for key in ("averagePoints", "points", "lastSeasonPoints"):
        v = pm.get(key)
        if v:
            return float(v)
    return 0.0


def captain_value(entry):
    """Expected captain payoff for one XI entry — higher is a better captain.

    = recent `form`, tilted by start-probability (a nailed starter beats a
    rotation risk of equal form) with market value as a faint tiebreaker (the
    pricier player is the safer captain when form and probability are level).
    `prob` is 0-100 (futbolfantasy) or None; unknown -> a neutral 0.5 weight, so
    a player with no probable-lineup data still ranks on form, just without the
    boost. Pure function.
    """
    pm = entry.get("playerMaster") or {}
    prob = entry.get("prob")
    prob_w = (prob / 100.0) if isinstance(prob, (int, float)) and not isinstance(prob, bool) else 0.5
    value = pm.get("marketValue") or 0
    return form(pm) * (0.5 + 0.5 * prob_w) + value * 1e-9


def pick_captain(xi):
    """Choose the captain among the chosen XI.

    `xi` is a list of dicts, each with a `playerTeamId`, a `playerMaster`, and the
    optimizer's `prob`/`disponible`. Only AVAILABLE starters are eligible — an
    injured in-position filler scores 0, so captaining him would waste the double.
    Returns the best starter's playerTeamId, or None when the XI is empty / nobody
    is eligible (the caller then simply omits the captain).
    """
    eligible = [e for e in xi if e.get("disponible", True)]
    if not eligible:
        return None
    best = max(eligible, key=captain_value)
    return best.get("playerTeamId") or best["playerMaster"]["id"]
