from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
LITE = ROOT / "07_delivery_packages" / "cvrp_docs_lite_package"
OUT_FIG = LITE / "figures_final"
OUT_TAB = LITE / "tables"

BASELINE = ROOT / "04_experiment_outputs" / "llm_vs_mock_small" / "baseline_summary.csv"
MOCK_LLM_SEED = ROOT / "04_experiment_outputs" / "llm_vs_mock_small" / "mock_vs_llm_seed_summary.csv"
MOCK_LLM_AGG = ROOT / "04_experiment_outputs" / "llm_vs_mock_small" / "mock_vs_llm_aggregate_summary.csv"
LLM_DETAIL = ROOT / "04_experiment_outputs" / "llm_vs_mock_small" / "runs" / "llm_seed42" / "tables" / "outer_all_detail.csv"
MOCK_DETAIL = ROOT / "04_experiment_outputs" / "llm_vs_mock_small" / "runs" / "mock_seed42" / "tables" / "outer_all_detail.csv"
ABL_BEHAVIOR = OUT_TAB / "final_ablation_behavior_summary.csv"


def build_final_method_table() -> pd.DataFrame:
    base = pd.read_csv(BASELINE)
    seed = pd.read_csv(MOCK_LLM_SEED)
    agg = pd.read_csv(MOCK_LLM_AGG)

    rows = []
    for _, r in base.iterrows():
        rows.append(
            {
                "method": r["expression"],
                "family": "baseline",
                "feasible_rate": float(r["feasible_rate"]),
                "avg_cost": float(r["avg_cost"]),
                "avg_runtime_sec": float(r["avg_runtime_sec"]),
                "token_total": 0,
                "note": "classic baseline",
            }
        )
    for _, r in seed.iterrows():
        rows.append(
            {
                "method": f"search_{r['mode']}",
                "family": "search",
                "feasible_rate": float(r["best_feasible_rate"]),
                "avg_cost": float(r["best_avg_cost"]),
                "avg_runtime_sec": float(r["best_avg_runtime_sec"]),
                "token_total": int(r["llm_total_tokens"]),
                "note": f"{r['mode']} search best result",
            }
        )

    df = pd.DataFrame(rows).sort_values(["family", "avg_cost"], ascending=[True, True]).reset_index(drop=True)
    df.to_csv(OUT_TAB / "final_methods_comparison.csv", index=False, encoding="utf-8")
    agg.to_csv(OUT_TAB / "final_mock_vs_llm_aggregate.csv", index=False, encoding="utf-8")
    return df


def plot_final_method_bars(df: pd.DataFrame) -> None:
    methods = df["method"].tolist()
    costs = df["avg_cost"].values
    rt = df["avg_runtime_sec"].values

    plt.figure(figsize=(10, 5))
    plt.bar(methods, costs, color="#4C78A8")
    plt.title("Final comparison: avg_cost across baselines and search methods")
    plt.ylabel("avg_cost")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_FIG / "final_methods_avg_cost.png", dpi=170)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.bar(methods, rt, color="#F58518")
    plt.yscale("log")
    plt.title("Final comparison: avg_runtime_sec (log scale)")
    plt.ylabel("avg_runtime_sec (log)")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_FIG / "final_methods_runtime_log.png", dpi=170)
    plt.close()


def _build_instance_delta() -> pd.DataFrame:
    llm = pd.read_csv(LLM_DETAIL)
    mock = pd.read_csv(MOCK_DETAIL)

    llm_best = (
        llm[llm["feasible"] == True]
        .groupby("instance", as_index=False)
        .agg(cost_llm=("cost", "min"), gap_pct_llm=("gap_pct", "min"))
    )
    mock_best = (
        mock[mock["feasible"] == True]
        .groupby("instance", as_index=False)
        .agg(cost_mock=("cost", "min"), gap_pct_mock=("gap_pct", "min"))
    )

    delta = llm_best.merge(mock_best, on="instance", how="inner")
    delta["delta_cost"] = delta["cost_mock"] - delta["cost_llm"]
    pair_best = delta[["cost_llm", "cost_mock"]].min(axis=1)
    delta["rel_gap_pct_llm"] = (delta["cost_llm"] - pair_best) / pair_best * 100.0
    delta["rel_gap_pct_mock"] = (delta["cost_mock"] - pair_best) / pair_best * 100.0

    delta = delta.sort_values("delta_cost", ascending=False).reset_index(drop=True)
    delta.to_csv(OUT_TAB / "final_mock_vs_llm_instance_delta.csv", index=False, encoding="utf-8")
    return delta


def plot_final_delta_and_cdf() -> None:
    delta = _build_instance_delta()

    plt.figure(figsize=(12, 5.8))
    colors = ["#2ca02c" if x > 0 else ("#d62728" if x < 0 else "#7f7f7f") for x in delta["delta_cost"]]
    bars = plt.bar(delta["instance"], delta["delta_cost"], color=colors)
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Mock vs LLM by Instance: delta_cost (mock - llm)\n(positive means LLM achieves lower cost)")
    plt.ylabel("delta_cost")
    plt.xticks(rotation=60, ha="right")

    # Explicitly mark tie cases (delta = 0) so they are not visually mistaken as missing bars.
    zero_mask = delta["delta_cost"] == 0
    if zero_mask.any():
        zero_x = np.where(zero_mask.to_numpy())[0]
        zero_y = np.zeros_like(zero_x, dtype=float)
        plt.scatter(zero_x, zero_y, color="#7f7f7f", marker="o", s=40, zorder=3, label="Tie (delta=0)")

    # Add concise labels on bars for report readability.
    for rect, val in zip(bars, delta["delta_cost"]):
        if val > 0:
            plt.text(rect.get_x() + rect.get_width() / 2, val + 4, f"{int(val)}", ha="center", va="bottom", fontsize=8)
        elif val < 0:
            plt.text(rect.get_x() + rect.get_width() / 2, val - 4, f"{int(val)}", ha="center", va="top", fontsize=8)
        else:
            plt.text(rect.get_x() + rect.get_width() / 2, 4, "0", ha="center", va="bottom", fontsize=8, color="#555555")

    llm_better = int((delta["delta_cost"] > 0).sum())
    mock_better = int((delta["delta_cost"] < 0).sum())
    ties = int((delta["delta_cost"] == 0).sum())
    summary_text = f"LLM better: {llm_better}  |  Mock better: {mock_better}  |  Tie: {ties}"
    plt.text(0.01, 0.98, summary_text, transform=plt.gca().transAxes, ha="left", va="top", fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT_FIG / "final_mock_vs_llm_instance_delta.png", dpi=170)
    plt.close()

    # Prefer true gap% to known optimum; fallback to pair-relative gap%.
    llm = delta["gap_pct_llm"].dropna().sort_values().reset_index(drop=True)
    mock = delta["gap_pct_mock"].dropna().sort_values().reset_index(drop=True)
    xlabel = "gap%"
    title = "Final mock vs LLM: CDF of gap% (to known optimum)"
    if len(llm) == 0 or len(mock) == 0:
        llm = delta["rel_gap_pct_llm"].dropna().sort_values().reset_index(drop=True)
        mock = delta["rel_gap_pct_mock"].dropna().sort_values().reset_index(drop=True)
        xlabel = "relative gap% (vs per-instance best of {mock,llm})"
        title = "Final mock vs LLM: CDF of relative gap%"

    llm_y = (llm.index + 1) / len(llm)
    mock_y = (mock.index + 1) / len(mock)
    plt.figure(figsize=(7, 5))
    plt.plot(llm, llm_y, label="LLM")
    plt.plot(mock, mock_y, label="Mock")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("CDF")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_FIG / "final_mock_vs_llm_gap_cdf.png", dpi=170)
    plt.close()


def plot_final_ablation_behavior() -> None:
    ab = pd.read_csv(ABL_BEHAVIOR)
    ab = ab.sort_values("rows_mean", ascending=False)

    plt.figure(figsize=(9, 4.8))
    plt.bar(ab["config"], ab["rows_mean"], color="#54A24B")
    plt.title("Final ablation: mean evaluated summary rows")
    plt.ylabel("rows_mean")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_FIG / "final_ablation_rows_mean.png", dpi=170)
    plt.close()

    plt.figure(figsize=(9, 4.8))
    plt.bar(ab["config"], ab["rounds_mean"], color="#B279A2")
    plt.title("Final ablation: mean active rounds")
    plt.ylabel("rounds_mean")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_FIG / "final_ablation_rounds_mean.png", dpi=170)
    plt.close()

    ab.to_csv(OUT_TAB / "final_ablation_behavior_summary.csv", index=False, encoding="utf-8")


def main() -> None:
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    OUT_TAB.mkdir(parents=True, exist_ok=True)
    df = build_final_method_table()
    plot_final_method_bars(df)
    plot_final_delta_and_cdf()
    plot_final_ablation_behavior()
    print(f"Final assets generated in: {LITE}")


if __name__ == "__main__":
    main()
