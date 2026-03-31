"""
FORMAT NOTES
------------
This dataset uses a CATEGORICAL format with 3 score levels:
  Category 1  (+1 / "good")
  Category 2  ( 0 / "neutral")
  Category 3  (-1 / "bad")

Each ballot line looks like:
  count: {cat1_ids}, {cat2_ids}, {cat3_ids}

where each group is a *tie* (unordered set).

CONVERSION STRATEGY (categories -> linear preference order)
-----------------------------------------------------------
To feed classical voting rules (which expect a strict linear order)
we convert each categorical ballot to a ranked list as follows:

  cat-1 members (score +1) -> ranked jointly first
  cat-2 members (score  0) -> ranked jointly second
  cat-3 members (score -1) -> ranked jointly last

Candidates absent from a ballot are appended at the very end.
Ties within a category are broken by candidate id.
"""

import re


def parse_cat_group(token: str) -> list:
    """
    Parse a single category token from a .cat ballot line.

    A token represents one category and can appear in 3 shapes:
      {6,10}  ->  [6, 10]   (multiple candidates, strip braces and split)
      {}      ->  []        (empty category, nobody placed here)
      10      ->  [10]      (single candidate, no braces)

    """
    token = token.strip()
    if token.startswith("{"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        return [int(x.strip()) for x in inner.split(",")]
    else:
        return [int(token)]


def load_cat_file(filepath: str) -> tuple:
    """

    Steps:
      1. Read alternative id->name mappings from header comment lines.
      2. For each ballot line, split the 3 category tokens by top-level commas
         (commas inside braces are ignored).
      3. Build a linear ranking: cat-1 candidates first, then cat-2, then cat-3,
         then any candidates not mentioned in the ballot.
      4. Expand each ballot entry by its voter count.

    Returns
    -------
    alternatives : dict {int -> str}
        Mapping of candidate id to candidate name.
    ballots : list of list of int
        One entry per voter (expanded by count). Each inner list is a full
        linear ranking of all candidate ids, most preferred first.
    """
    alternatives = {}
    ballots = []

    with open(filepath, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # -- Parse alternative names from header comment lines -------------------
    for line in lines:
        m = re.match(r"# ALTERNATIVE NAME (\d+): (.+)", line)
        if m:
            alternatives[int(m.group(1))] = m.group(2).strip()

    all_ids = sorted(alternatives.keys())

    # -- Parse ballot lines --------------------------------------------------
    for line in lines:
        if line.startswith("#") or ":" not in line:
            continue

        count_str, rest = line.split(":", 1)
        try:
            count = int(count_str.strip())
        except ValueError:
            continue  # not a ballot line

        # Split on top-level commas only (ignore commas inside braces)
        groups = []
        depth = 0
        current = ""
        for ch in rest:
            if ch == "{":
                depth += 1
                current += ch
            elif ch == "}":
                depth -= 1
                current += ch
            elif ch == "," and depth == 0:
                groups.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            groups.append(current.strip())

        # Build linear ranking: cat-1 -> cat-2 -> cat-3 -> unmentioned
        mentioned = set()
        linear_ranking = []
        for g in groups:
            for cid in sorted(parse_cat_group(g)):  # sort within group for determinism
                linear_ranking.append(cid)
                mentioned.add(cid)

        # Append candidates not mentioned anywhere in this ballot
        for cid in all_ids:
            if cid not in mentioned:
                linear_ranking.append(cid)

        # Expand ballot by voter count
        for _ in range(count):
            ballots.append(linear_ranking)

    print(
        "Loaded {} candidates and {} voters.\n".format(len(alternatives), len(ballots))
    )
    return alternatives, ballots
