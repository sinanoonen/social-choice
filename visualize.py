import os
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.patches as mpatches  # type: ignore
import numpy as np  # type: ignore


# Consistent colour palette — one colour per candidate, shared across all plots
CANDIDATE_COLORS = [
    "#4C72B0",
    "#DD8452",
    "#55A868",
    "#C44E52",
    "#8172B2",
    "#937860",
    "#DA8BC3",
    "#8C8C8C",
    "#CCB974",
    "#64B5CD",
    "#B47CC7",
]

OUTPUT_DIR = "figures"


def _ensure_output_dir():
    """Create the figures/ output directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _candidate_colors(alternatives: dict) -> dict:
    """Return a stable {cid -> hex colour} mapping sorted by candidate id."""
    sorted_ids = sorted(alternatives.keys())
    return {
        cid: CANDIDATE_COLORS[i % len(CANDIDATE_COLORS)]
        for i, cid in enumerate(sorted_ids)
    }


def bar_chart(
    title: str,
    alternatives: dict,
    scores: dict,
    winner: int,
    filename: str,
    xlabel: str = "Score",
) -> None:
    """
    Save a horizontal bar chart for one voting rule's results.

    Candidates are sorted best-to-worst (top to bottom).
    The winning bar is outlined in gold to make it stand out.

    Parameters
    ----------
    title        : str              chart title
    alternatives : dict {int->str}
    scores       : dict {int->numeric}
    winner       : int              winning candidate id
    filename     : str              output filename (saved inside figures/)
    xlabel       : str              x-axis label
    """
    _ensure_output_dir()
    color_map = _candidate_colors(alternatives)

    # Sort candidates best -> worst
    sorted_ids = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    names = [alternatives[cid] for cid in sorted_ids]
    values = [scores[cid] for cid in sorted_ids]
    colors = [color_map[cid] for cid in sorted_ids]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, values, color=colors, edgecolor="white", height=0.6)

    # Highlight the winner bar with a gold edge
    for bar, cid in zip(bars, sorted_ids):
        if cid == winner:
            bar.set_edgecolor("gold")
            bar.set_linewidth(2.5)

    # Annotate each bar with its score value
    for bar, val in zip(bars, values):
        x_pos = bar.get_width()
        offset = abs(max(values) - min(values)) * 0.01
        ha = "left" if x_pos >= 0 else "right"
        ax.text(
            x_pos + (offset if x_pos >= 0 else -offset),
            bar.get_y() + bar.get_height() / 2,
            "{:.0f}".format(val),
            va="center",
            ha=ha,
            fontsize=9,
        )

    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.invert_yaxis()  # best candidate at the top
    ax.axvline(0, color="black", linewidth=0.8)  # zero line for negative scores

    # Add winner annotation in top-right corner
    ax.text(
        0.98,
        0.02,
        "Winner: {}".format(alternatives[winner]),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color="darkgreen",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gold"),
    )

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: {}".format(path))


def stv_round_chart(alternatives: dict, rounds_log: list, winner: int) -> None:
    """
    Save a grouped bar chart showing how each candidate's vote share evolves
    across all STV rounds.

    Each group of bars = one round. Each bar = one candidate still active
    in that round. Eliminated candidates disappear from subsequent rounds.

    Parameters
    ----------
    alternatives : dict {int->str}
    rounds_log   : list of dict    as returned by voting_rules.stv()
    winner       : int
    """
    _ensure_output_dir()
    color_map = _candidate_colors(alternatives)

    n_rounds = len(rounds_log)
    # Collect all candidate ids that appear across any round
    all_cids = sorted({cid for entry in rounds_log for cid in entry["counts"]})
    n_candidates = len(all_cids)

    x = np.arange(n_rounds)
    bar_width = 0.8 / n_candidates

    fig, ax = plt.subplots(figsize=(max(12, n_rounds * 2), 6))

    for i, cid in enumerate(all_cids):
        vote_shares = []
        for entry in rounds_log:
            if cid in entry["counts"]:
                pct = entry["counts"][cid] / entry["total"] * 100
            else:
                pct = 0  # eliminated — bar absent (zero height)
            vote_shares.append(pct)

        offset = (i - n_candidates / 2) * bar_width + bar_width / 2
        bars = ax.bar(
            x + offset,
            vote_shares,
            width=bar_width,
            label=alternatives[cid],
            color=color_map[cid],
            edgecolor="white",
            linewidth=0.5,
        )

        # Gold outline on the winner's bars
        if cid == winner:
            for bar in bars:
                bar.set_edgecolor("gold")
                bar.set_linewidth(1.8)

    # 50% majority line
    ax.axhline(50, color="crimson", linestyle="--", linewidth=1.2, label="50% majority")

    ax.set_xticks(x)
    ax.set_xticklabels(["Round {}".format(r + 1) for r in range(n_rounds)], fontsize=10)
    ax.set_ylabel("Vote share (%)", fontsize=11)
    ax.set_title("STV – Vote Share per Round", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.9)
    ax.set_ylim(0, 70)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "stv_rounds.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: {}".format(path))


def summary_table(
    alternatives: dict,
    results: dict,
) -> None:
    """
    Save a summary table showing every candidate's rank under each voting rule,
    plus which rule each candidate won.

    Parameters
    ----------
    alternatives : dict {int->str}
    results      : dict {rule_label -> (winner_id, scores_dict)}
                   e.g. {"Plurality": (winner, scores), "Borda": (winner, scores), ...}
    """
    _ensure_output_dir()
    color_map = _candidate_colors(alternatives)

    rule_labels = list(results.keys())
    # Sort candidates by average rank across all rules
    sorted_ids = sorted(alternatives.keys())

    # Build rank matrix: rank_matrix[cid][rule] = rank (1 = best)
    rank_matrix = {}
    for cid in sorted_ids:
        rank_matrix[cid] = {}
        for label, (_, scores) in results.items():
            sorted_by_score = sorted(scores.keys(), key=lambda k: -scores[k])
            rank_matrix[cid][label] = sorted_by_score.index(cid) + 1

    # Sort candidates by their average rank
    sorted_ids.sort(key=lambda cid: sum(rank_matrix[cid].values()) / len(rule_labels))

    # --- Build table data ---
    col_labels = ["Candidate"] + rule_labels
    table_data = []
    cell_colors = []

    for cid in sorted_ids:
        row = [alternatives[cid]]
        row_colors = ["#f5f5f5"]
        for label, (winner_id, scores) in results.items():
            rank = rank_matrix[cid][label]
            row.append("#{} ({:.0f})".format(rank, scores[cid]))
            if cid == winner_id:
                row_colors.append("#d4edda")  # green  – winner of this rule
            elif rank <= 3:
                row_colors.append("#fff3cd")  # yellow – top 3
            else:
                row_colors.append("#ffffff")  # white  – other
        table_data.append(row)
        cell_colors.append(row_colors)

    fig, ax = plt.subplots(figsize=(12, max(5, len(sorted_ids) * 0.55 + 1.5)))
    ax.axis("off")

    tbl = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.6)

    # Style header row
    for col_idx in range(len(col_labels)):
        tbl[0, col_idx].set_facecolor("#2c3e50")
        tbl[0, col_idx].set_text_props(color="white", fontweight="bold")

    # Legend patches
    legend_patches = [
        mpatches.Patch(color="#d4edda", label="Winner of that rule"),
        mpatches.Patch(color="#fff3cd", label="Top 3 finish"),
        mpatches.Patch(color="#ffffff", label="Other"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=3,
        fontsize=9,
        framealpha=0.9,
    )

    ax.set_title(
        "Summary: Candidate Rankings Across All Voting Rules\n"
        "(sorted by average rank, format: #rank (score))",
        fontsize=12,
        fontweight="bold",
        pad=16,
    )

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "summary_table.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: {}".format(path))


def save_all(
    alternatives: dict,
    plurality_result: tuple,
    anti_plurality_result: tuple,
    borda_result: tuple,
    copeland_result: tuple,
    stv_result: tuple,
) -> None:
    """
    Generate and save all visualisations in one call.

    Parameters
    ----------
    alternatives          : dict {int->str}
    plurality_result      : (winner_id, scores)
    anti_plurality_result : (winner_id, scores)
    borda_result          : (winner_id, scores)
    copeland_result       : (winner_id, scores)
    stv_result            : (winner_id, rounds_log)
    """
    print("\nSaving figures to '{}/':".format(OUTPUT_DIR))

    p_winner, p_scores = plurality_result
    ap_winner, ap_scores = anti_plurality_result
    b_winner, b_scores = borda_result
    c_winner, c_scores = copeland_result
    s_winner, s_log = stv_result

    bar_chart(
        "Plurality Rule – First-Choice Votes",
        alternatives,
        p_scores,
        p_winner,
        "plurality.png",
        xlabel="First-place votes",
    )

    bar_chart(
        "Anti-Plurality (Veto) Rule – Veto Counts",
        alternatives,
        ap_scores,
        ap_winner,
        "anti_plurality.png",
        xlabel="Veto score (lower = more vetoed)",
    )

    bar_chart(
        "Borda's Rule – Total Borda Points",
        alternatives,
        b_scores,
        b_winner,
        "borda.png",
        xlabel="Borda points",
    )

    bar_chart(
        "Copeland's Rule – Pairwise Win Score",
        alternatives,
        c_scores,
        c_winner,
        "copeland.png",
        xlabel="Copeland score",
    )

    stv_round_chart(alternatives, s_log, s_winner)

    # Summary table uses the final-round STV scores for comparison
    stv_final_scores = s_log[-1]["counts"]
    # Pad any missing candidates with 0 (they were eliminated earlier)
    stv_scores_full = {cid: stv_final_scores.get(cid, 0) for cid in alternatives}

    summary_table(
        alternatives,
        {
            "Plurality": (p_winner, p_scores),
            "Anti-Plurality": (ap_winner, ap_scores),
            "Borda": (b_winner, b_scores),
            "Copeland": (c_winner, c_scores),
            "STV": (s_winner, stv_scores_full),
        },
    )

    print(
        "\nAll figures saved. Include them in your report from the '{}/' folder.".format(
            OUTPUT_DIR
        )
    )
