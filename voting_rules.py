"""
Implements five voting rules for aggregating ranked ballots:

  - Plurality
  - Anti-Plurality (Veto)
  - Borda
  - Copeland
  - Single Transferable Vote (STV)

Each function accepts:
  alternatives : dict {int -> str}   candidate id -> name
  ballots      : list of list[int]   one linear ranking per voter

Each function returns:
  winner : int                       id of the winning candidate
  scores : dict or list              supporting data (scores or round log)
"""


def plurality(alternatives: dict, ballots: list) -> tuple:
    """
    Plurality rule
    --------------
    Each voter awards 1 point to their top-ranked candidate only.
    The candidate with the most first-place votes wins.
    """
    scores = {cid: 0 for cid in alternatives}

    for ballot in ballots:
        if ballot:
            scores[ballot[0]] += 1  # only the first choice earns a point

    winner = max(scores, key=lambda k: scores[k])
    return winner, scores


def anti_plurality(alternatives: dict, ballots: list) -> tuple:
    """
    Anti-Plurality (Veto) rule
    --------------------------
    Each voter gives -1 to their last-ranked candidate; all others receive 0.
    The candidate with the highest (least negative) total score wins.
    """
    scores = {cid: 0 for cid in alternatives}

    for ballot in ballots:
        if ballot:
            scores[ballot[-1]] -= 1  # last-place candidate is vetoed

    winner = max(scores, key=lambda k: scores[k])
    return winner, scores


def borda(alternatives: dict, ballots: list) -> tuple:
    """
    Borda's rule
    ------------
    With m candidates, the candidate ranked 1st gets m-1 points,
    2nd gets m-2 points, ..., last gets 0 points.
    The candidate with the highest cumulative score wins.

    """
    m = len(alternatives)
    scores = {cid: 0 for cid in alternatives}

    for ballot in ballots:
        for rank_index, cid in enumerate(ballot):
            # rank_index 0 = first place -> earns m-1 points
            scores[cid] += (m - 1) - rank_index

    winner = max(scores, key=lambda k: scores[k])
    return winner, scores


def copeland(alternatives: dict, ballots: list) -> tuple:
    """
    Copeland's rule
    ---------------
    Conduct all pairwise majority comparisons between candidates.
    For each pair (a, b):
      - a wins the majority -> a gets +1 point
      - b wins the majority -> b gets +1 point
      - tie in votes        -> both get +0.5 points
    The candidate with the highest total Copeland score wins.
    """
    alt_ids = list(alternatives.keys())
    m = len(alt_ids)

    # pref[a][b] = number of voters who rank a strictly above b
    pref = {a: {b: 0 for b in alt_ids if b != a} for a in alt_ids}

    for ballot in ballots:
        position = {cid: idx for idx, cid in enumerate(ballot)}
        for i in range(m):
            for j in range(i + 1, m):
                a, b = alt_ids[i], alt_ids[j]
                pos_a = position.get(a, m)  # unranked candidates go to the end
                pos_b = position.get(b, m)
                if pos_a < pos_b:
                    pref[a][b] += 1
                elif pos_b < pos_a:
                    pref[b][a] += 1

    # Assign Copeland points based on pairwise outcomes
    scores = {cid: 0.0 for cid in alt_ids}
    for i in range(m):
        for j in range(i + 1, m):
            a, b = alt_ids[i], alt_ids[j]
            if pref[a][b] > pref[b][a]:
                scores[a] += 1.0
            elif pref[b][a] > pref[a][b]:
                scores[b] += 1.0
            else:
                scores[a] += 0.5
                scores[b] += 0.5

    winner = max(scores, key=lambda k: scores[k])
    return winner, scores


def stv(alternatives: dict, ballots: list) -> tuple:
    """
    Single Transferable Vote
    -------------------------------------------------------------------
    Algorithm:
      1. Count first-choice votes among still-active candidates.
      2. If any candidate has strictly more than 50% of votes -> winner.
      3. Otherwise eliminate the candidate with the fewest first-choice votes.
         Tie-break: eliminate the candidate with the lowest id (deterministic).
      4. Remove the eliminated candidate from all ballots and repeat.

    """
    active = set(alternatives.keys())
    current_ballots = [list(b) for b in ballots]  # work on copies
    rounds_log = []

    while True:
        # Count first-choice votes for each still-active candidate
        counts = {cid: 0 for cid in active}
        for ballot in current_ballots:
            for cid in ballot:
                if cid in active:
                    counts[cid] += 1
                    break  # only the top active candidate on each ballot counts

        total = sum(counts.values())
        entry = {"counts": dict(counts), "total": total}

        # Check for a majority winner
        for cid, cnt in counts.items():
            if cnt > total / 2:
                rounds_log.append(entry)
                return cid, rounds_log

        # If only one candidate remains, they win by default
        if len(active) == 1:
            rounds_log.append(entry)
            return list(active)[0], rounds_log

        # Eliminate the weakest candidate (tie-break: lowest id)
        min_votes = min(counts.values())
        to_eliminate = min(cid for cid, v in counts.items() if v == min_votes)
        entry["eliminated"] = to_eliminate
        rounds_log.append(entry)

        active.remove(to_eliminate)
        current_ballots = [
            [cid for cid in ballot if cid != to_eliminate] for ballot in current_ballots
        ]
