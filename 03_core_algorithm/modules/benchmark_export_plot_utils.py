import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_project_path(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return _project_root() / p


def _safe_run_name(run_name: Optional[str]) -> str:
    if run_name:
        return run_name.replace(" ", "_")
    return datetime.now().strftime("run_%Y%m%d_%H%M%S")


def _ensure_dirs(output_root: str, run_name: Optional[str]) -> Dict[str, Path]:
    root = _resolve_project_path(output_root)
    run = _safe_run_name(run_name)
    run_dir = root / run
    tables_dir = run_dir / "tables"
    plots_dir = run_dir / "plots"
    tables_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return {"run_dir": run_dir, "tables_dir": tables_dir, "plots_dir": plots_dir}


def _load_known_opt_table(base_dir: str = "02_processed_data/classic/base") -> pd.DataFrame:
    rows = []
    for p in sorted(_resolve_project_path(base_dir).glob("*.base.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        rows.append(
            {
                "instance": data["instance_id"],
                "known_opt_cost": data.get("known_opt_cost"),
                "set_id": data.get("set_id"),
                "dimension": data.get("dimension"),
            }
        )
    return pd.DataFrame(rows)


def attach_optimal_gap(detail_df: pd.DataFrame, base_dir: str = "02_processed_data/classic/base") -> pd.DataFrame:
    if detail_df is None or detail_df.empty:
        return detail_df
    if "instance" not in detail_df.columns or "cost" not in detail_df.columns:
        return detail_df

    opt_df = _load_known_opt_table(base_dir=base_dir)
    if opt_df.empty or "instance" not in opt_df.columns:
        out = detail_df.copy()
        out["known_opt_cost"] = np.nan
        out["set_id"] = np.nan
        out["dimension"] = np.nan
        out["gap"] = np.nan
        out["gap_pct"] = np.nan
        return out
    merged = detail_df.merge(opt_df, on="instance", how="left")
    merged["gap"] = merged["cost"] - merged["known_opt_cost"]
    merged["gap_pct"] = np.where(
        merged["known_opt_cost"].notna() & (merged["known_opt_cost"] > 0),
        merged["gap"] / merged["known_opt_cost"] * 100.0,
        np.nan,
    )
    return merged


def _save_df(df: Optional[pd.DataFrame], path: Path) -> int:
    if df is None:
        return 0
    df.to_csv(path, index=False, encoding="utf-8")
    return len(df)


def _plot_bar(df: pd.DataFrame, x: str, y: str, title: str, out_path: Path, rotate_xtick: bool = True) -> None:
    if df.empty or x not in df.columns or y not in df.columns:
        return
    plt.figure(figsize=(10, 5))
    plt.bar(df[x].astype(str), df[y], color="#4C78A8")
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    if rotate_xtick:
        plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_round_trends(all_summary_outer: pd.DataFrame, plots_dir: Path) -> None:
    if all_summary_outer is None or all_summary_outer.empty or "round_idx" not in all_summary_outer.columns:
        return
    # 每轮最佳与平均表现（按 avg_cost）
    round_best = all_summary_outer.groupby("round_idx", as_index=False)["avg_cost"].min()
    round_mean = all_summary_outer.groupby("round_idx", as_index=False)["avg_cost"].mean()

    plt.figure(figsize=(9, 5))
    plt.plot(round_best["round_idx"], round_best["avg_cost"], marker="o", label="best_avg_cost")
    plt.plot(round_mean["round_idx"], round_mean["avg_cost"], marker="o", label="mean_avg_cost")
    plt.title("Outer Loop Trend: avg_cost by round")
    plt.xlabel("round_idx")
    plt.ylabel("avg_cost")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "outer_round_cost_trend.png", dpi=160)
    plt.close()

    if "feasible_rate" in all_summary_outer.columns:
        round_feas = all_summary_outer.groupby("round_idx", as_index=False)["feasible_rate"].mean()
        plt.figure(figsize=(9, 5))
        plt.plot(round_feas["round_idx"], round_feas["feasible_rate"], marker="o")
        plt.title("Outer Loop Trend: feasible_rate by round")
        plt.xlabel("round_idx")
        plt.ylabel("feasible_rate")
        plt.ylim(0, 1.05)
        plt.tight_layout()
        plt.savefig(plots_dir / "outer_round_feasible_trend.png", dpi=160)
        plt.close()


def export_and_plot(
    summary_full: Optional[pd.DataFrame] = None,
    all_detail_outer: Optional[pd.DataFrame] = None,
    all_summary_outer: Optional[pd.DataFrame] = None,
    all_top_outer: Optional[pd.DataFrame] = None,
    output_root: str = "04_experiment_outputs/formal_benchmark/formal_benchmark_runs",
    run_name: Optional[str] = None,
    base_dir: str = "02_processed_data/classic/base",
) -> Dict[str, str]:
    dirs = _ensure_dirs(output_root=output_root, run_name=run_name)
    tables_dir = dirs["tables_dir"]
    plots_dir = dirs["plots_dir"]

    detail_with_gap = attach_optimal_gap(all_detail_outer, base_dir=base_dir)
    summary_with_gap = attach_optimal_gap(summary_full, base_dir=base_dir) if summary_full is not None else summary_full

    row_info = {
        "summary_full_rows": _save_df(summary_with_gap, tables_dir / "baseline_summary_full.csv"),
        "all_detail_outer_rows": _save_df(detail_with_gap, tables_dir / "outer_all_detail.csv"),
        "all_summary_outer_rows": _save_df(all_summary_outer, tables_dir / "outer_all_summary.csv"),
        "all_top_outer_rows": _save_df(all_top_outer, tables_dir / "outer_all_top.csv"),
    }

    # baseline 对比图
    if summary_full is not None and not summary_full.empty:
        _plot_bar(summary_full, "expression", "avg_cost", "Baseline Comparison: avg_cost", plots_dir / "baseline_avg_cost.png")
        if "feasible_rate" in summary_full.columns:
            _plot_bar(
                summary_full,
                "expression",
                "feasible_rate",
                "Baseline Comparison: feasible_rate",
                plots_dir / "baseline_feasible_rate.png",
            )
        if "avg_runtime_sec" in summary_full.columns:
            _plot_bar(
                summary_full,
                "expression",
                "avg_runtime_sec",
                "Baseline Comparison: avg_runtime_sec",
                plots_dir / "baseline_runtime.png",
            )

    # outer loop 趋势图
    if all_summary_outer is not None and not all_summary_outer.empty:
        _plot_round_trends(all_summary_outer, plots_dir=plots_dir)

    # top 表达式图
    if all_top_outer is not None and not all_top_outer.empty:
        top_for_plot = all_top_outer.sort_values(["round_idx", "avg_cost"], ascending=[True, True]).copy()
        top_for_plot["expr_short"] = top_for_plot["expression"].astype(str).str.slice(0, 52)
        _plot_bar(
            top_for_plot.head(12),
            "expr_short",
            "avg_cost",
            "Top Expressions (first 12 rows): avg_cost",
            plots_dir / "top_expressions_avg_cost.png",
        )

    meta = {
        "created_at": datetime.now().isoformat(),
        "output_root": str(dirs["run_dir"]),
        "files": row_info,
    }
    (dirs["run_dir"] / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "run_dir": str(dirs["run_dir"]),
        "tables_dir": str(tables_dir),
        "plots_dir": str(plots_dir),
    }
