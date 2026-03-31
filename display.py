"""
Pretty-printing helpers for voting rule results.

  - print_results()  : score table for Plurality, Anti-Plurality, Borda, Copeland
  - print_stv()      : round-by-round elimination log for STV
"""


def print_results(title: str, alternatives: dict, scores: dict, winner: int) -> None:
    """
    Print a formatted score table for a voting rule, sorted best to worst.
    The winning candidate is highlighted with an arrow marker.

    Parameters
    ----------
    title        : str            section heading to display
    alternatives : dict {int -> str}
    scores       : dict {int -> int or float}   score per candidate
    winner       : int            id of the winning candidate
    """
    print("\n" + "=" * 60)
    print("  " + title)
    print("=" * 60)

    for cid, score in sorted(scores.items(), key=lambda x: -x[1]):
        marker = "  <-- WINNER" if cid == winner else ""
        print("  {:<32} {:>10.1f}{}".format(alternatives[cid], score, marker))

    print("-" * 60)
    print("  Winner: {}\n".format(alternatives[winner]))


def print_stv(alternatives: dict, rounds_log: list, winner: int) -> None:
    """
    Print the STV round-by-round elimination log.

    For each round, shows vote counts and percentages for all active candidates,
    and the candidate eliminated at the end of that round.

    Parameters
    ----------
    alternatives : dict {int -> str}
    rounds_log   : list of dict   as returned by voting_rules.stv()
                   Each dict contains:
                     "counts"     : {cid -> vote count}
                     "total"      : total valid votes this round
                     "eliminated" : cid eliminated (absent in the final round)
    winner       : int            id of the winning candidate
    """
    print("\n" + "=" * 60)
    print("  Single Transferable Vote (STV) – Round Log")
    print("=" * 60)

    for r, entry in enumerate(rounds_log, start=1):
        print("\n  Round {}  (total valid votes: {})".format(r, entry["total"]))

        for cid, cnt in sorted(entry["counts"].items(), key=lambda x: -x[1]):
            pct = cnt / entry["total"] * 100 if entry["total"] else 0
            print(
                "    {:<32} {:>6} votes  ({:.1f}%)".format(alternatives[cid], cnt, pct)
            )

        if "eliminated" in entry:
            print("  --> Eliminated: {}".format(alternatives[entry["eliminated"]]))

    print("\n  Winner: {}".format(alternatives[winner]))
    print("-" * 60)
