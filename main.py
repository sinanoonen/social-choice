from data_loader import load_cat_file
from voting_rules import plurality, anti_plurality, borda, copeland, stv
from display import print_results, print_stv
from visualize import save_all


DATASET_PATH = "00073-00000002.cat"


def main():
    print("=" * 60)
    print("  CSE3210 – Computational Social Choice")
    print("  French Presidential Elections 2017 (Voter Autrement)")
    print("=" * 60 + "\n")

    # Load and convert the dataset
    alternatives, ballots = load_cat_file(DATASET_PATH)

    # Q1 – Plurality
    winner, scores = plurality(alternatives, ballots)
    print_results("Q1 – Plurality Rule", alternatives, scores, winner)

    # Q2 – Anti-Plurality
    winner, scores = anti_plurality(alternatives, ballots)
    print_results("Q2 – Anti-Plurality (Veto) Rule", alternatives, scores, winner)

    # Q3 – Borda
    winner, scores = borda(alternatives, ballots)
    print_results("Q3 – Borda's Rule", alternatives, scores, winner)

    # Q4 – Copeland
    winner, scores = copeland(alternatives, ballots)
    print_results("Q4 – Copeland's Rule", alternatives, scores, winner)

    # Q5 – STV
    stv_winner, stv_rounds = stv(alternatives, ballots)
    print_stv(alternatives, stv_rounds, stv_winner)

    # Save all visualisations to figures/
    save_all(
        alternatives,
        plurality_result=plurality(alternatives, ballots),
        anti_plurality_result=anti_plurality(alternatives, ballots),
        borda_result=borda(alternatives, ballots),
        copeland_result=copeland(alternatives, ballots),
        stv_result=(stv_winner, stv_rounds),
    )


if __name__ == "__main__":
    main()
