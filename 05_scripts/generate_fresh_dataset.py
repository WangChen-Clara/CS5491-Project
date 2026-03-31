import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple


GLOBAL_SEED = 5491

FRESHNESS_TO_MAX_TRAVEL = {"high": 90, "medium": 180, "low": 300}
FRESHNESS_WEIGHT = {"high": 1.5, "medium": 1.0, "low": 0.7}
TEMP_ZONE_PROB = {
    "high": [("frozen", 0.35), ("chilled", 0.50), ("ambient", 0.15)],
    "medium": [("frozen", 0.20), ("chilled", 0.50), ("ambient", 0.30)],
    "low": [("frozen", 0.10), ("chilled", 0.25), ("ambient", 0.65)],
}

TIME_WINDOW_BASE = {
    "near": (480, 720),
    "mid": (540, 840),
    "far": (600, 960),
}


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def stable_instance_seed(instance_id: str) -> int:
    digest = hashlib.sha256(instance_id.encode("utf-8")).hexdigest()
    return GLOBAL_SEED + int(digest[:8], 16)


def quantile_thresholds(values: List[float], q1: float, q2: float) -> Tuple[float, float]:
    sorted_vals = sorted(values)
    if not sorted_vals:
        return 0.0, 0.0
    i1 = min(len(sorted_vals) - 1, max(0, int(math.floor((len(sorted_vals) - 1) * q1))))
    i2 = min(len(sorted_vals) - 1, max(0, int(math.floor((len(sorted_vals) - 1) * q2))))
    return sorted_vals[i1], sorted_vals[i2]


def classify_by_cut(value: float, low_cut: float, high_cut: float, labels: Tuple[str, str, str]) -> str:
    if value <= low_cut:
        return labels[0]
    if value <= high_cut:
        return labels[1]
    return labels[2]


def weighted_choice(rng: random.Random, weighted: List[Tuple[str, float]]) -> str:
    r = rng.random()
    acc = 0.0
    for label, w in weighted:
        acc += w
        if r <= acc:
            return label
    return weighted[-1][0]


def add_fresh_fields(base: Dict) -> Dict:
    instance_id = base["instance_id"]
    rng = random.Random(stable_instance_seed(instance_id))

    customers = base["customers"]
    depot_id = base["depot"]["id"]
    distance_matrix = base["distance_matrix"]
    depot_idx = depot_id - 1

    demands = [c["demand"] for c in customers]
    demand_low, demand_high = quantile_thresholds(demands, 0.30, 0.70)

    depot_distances = [distance_matrix[depot_idx][c["id"] - 1] for c in customers]
    dist_low, dist_high = quantile_thresholds(depot_distances, 0.33, 0.66)

    fresh_customers = []
    for c in customers:
        demand = c["demand"]
        dist_to_depot = distance_matrix[depot_idx][c["id"] - 1]

        distance_band = classify_by_cut(dist_to_depot, dist_low, dist_high, ("near", "mid", "far"))
        base_ready, base_due = TIME_WINDOW_BASE[distance_band]
        jitter = rng.randint(-20, 20)
        ready = base_ready + jitter
        due = base_due + jitter

        demand_band = classify_by_cut(demand, demand_low, demand_high, ("low", "medium", "high"))
        freshness_class = "high" if demand_band == "high" else ("medium" if demand_band == "medium" else "low")
        max_travel = FRESHNESS_TO_MAX_TRAVEL[freshness_class]
        temp_zone = weighted_choice(rng, TEMP_ZONE_PROB[freshness_class])

        service_time_min = 5 + int(math.ceil(0.2 * demand))
        late_penalty_per_min = round(0.8 * demand, 2)
        spoilage_penalty = round(2.0 * demand * FRESHNESS_WEIGHT[freshness_class], 2)

        fresh_customers.append(
            {
                **c,
                "distance_to_depot": dist_to_depot,
                "distance_band": distance_band,
                "service_time_min": service_time_min,
                "ready_time_min": ready,
                "due_time_min": due,
                "freshness_class": freshness_class,
                "max_travel_time_min": max_travel,
                "temp_zone": temp_zone,
                "late_penalty_per_min": late_penalty_per_min,
                "spoilage_penalty": spoilage_penalty,
            }
        )

    fresh = {
        **base,
        "problem_variant": "CVRP_FRESH",
        "depot_start_time_min": 480,
        "objective_weights": {
            "distance": 1.0,
            "lateness": 1.0,
            "spoilage": 1.0,
        },
        "customers": fresh_customers,
    }
    return fresh


def validate_fresh_instance(fresh: Dict) -> List[str]:
    errs: List[str] = []
    customers = fresh["customers"]
    for c in customers:
        if c["service_time_min"] <= 0:
            errs.append(f"customer {c['id']}: service_time_min <= 0")
        if c["ready_time_min"] >= c["due_time_min"]:
            errs.append(f"customer {c['id']}: invalid time window")
        cls = c["freshness_class"]
        if cls not in FRESHNESS_TO_MAX_TRAVEL:
            errs.append(f"customer {c['id']}: invalid freshness_class {cls}")
        else:
            expected = FRESHNESS_TO_MAX_TRAVEL[cls]
            if c["max_travel_time_min"] != expected:
                errs.append(f"customer {c['id']}: max_travel_time mismatch")
        if c["temp_zone"] not in {"frozen", "chilled", "ambient"}:
            errs.append(f"customer {c['id']}: invalid temp_zone")
    return errs


def summarize_distribution(fresh_instances: List[Dict]) -> Dict:
    cls_count = {"high": 0, "medium": 0, "low": 0}
    temp_count = {"frozen": 0, "chilled": 0, "ambient": 0}
    service_times: List[int] = []
    tw_widths: List[int] = []
    late_penalties: List[float] = []
    spoilage_penalties: List[float] = []

    for inst in fresh_instances:
        for c in inst["customers"]:
            cls_count[c["freshness_class"]] += 1
            temp_count[c["temp_zone"]] += 1
            service_times.append(c["service_time_min"])
            tw_widths.append(c["due_time_min"] - c["ready_time_min"])
            late_penalties.append(c["late_penalty_per_min"])
            spoilage_penalties.append(c["spoilage_penalty"])

    return {
        "freshness_count": cls_count,
        "temp_zone_count": temp_count,
        "service_time_min": {"min": min(service_times), "max": max(service_times), "mean": round(mean(service_times), 2)},
        "time_window_width_min": {"min": min(tw_widths), "max": max(tw_widths), "mean": round(mean(tw_widths), 2)},
        "late_penalty_per_min": {"min": min(late_penalties), "max": max(late_penalties), "mean": round(mean(late_penalties), 2)},
        "spoilage_penalty": {"min": min(spoilage_penalties), "max": max(spoilage_penalties), "mean": round(mean(spoilage_penalties), 2)},
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    base_dir = root / "02_processed_data" / "classic" / "base"
    fresh_dir = root / "02_processed_data" / "fresh" / "fresh"
    fresh_meta_dir = root / "02_processed_data" / "fresh" / "fresh_meta"
    docs_dir = root / "06_docs" / "pipeline_docs"
    protocol_doc = docs_dir / "fresh_generation_protocol.md"
    qa_doc = docs_dir / "fresh_qa_report.md"
    schema_doc = docs_dir / "fresh_data_schema.md"

    fresh_dir.mkdir(parents=True, exist_ok=True)
    fresh_meta_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    fresh_instances: List[Dict] = []
    qa_errors: Dict[str, List[str]] = {}

    base_files = sorted(base_dir.glob("*.base.json"))
    for base_path in base_files:
        base = load_json(base_path)
        fresh = add_fresh_fields(base)
        errs = validate_fresh_instance(fresh)
        if errs:
            qa_errors[fresh["instance_id"]] = errs

        instance_id = fresh["instance_id"]
        fresh_out = fresh_dir / f"{instance_id}.fresh.json"
        meta_out = fresh_meta_dir / f"{instance_id}.fresh.meta.json"
        write_json(fresh_out, fresh)
        write_json(
            meta_out,
            {
                "instance_id": instance_id,
                "source_base_file": str(base_path),
                "generator_version": "1.0",
                "global_seed": GLOBAL_SEED,
                "instance_seed": stable_instance_seed(instance_id),
                "service_time_rule": "5 + ceil(0.2 * demand)",
                "time_window_rule": "distance-band base windows + jitter[-20,20]",
                "freshness_rule": "demand quantile 30/70 -> low/medium/high",
                "max_travel_rule": FRESHNESS_TO_MAX_TRAVEL,
                "temp_zone_rule": TEMP_ZONE_PROB,
                "penalty_rule": {
                    "late_penalty_per_min": "0.8 * demand",
                    "spoilage_penalty": "2.0 * demand * freshness_weight",
                    "freshness_weight": FRESHNESS_WEIGHT,
                },
            },
        )
        fresh_instances.append(fresh)

    dist = summarize_distribution(fresh_instances)

    protocol_lines = [
        "# Fresh Dataset Generation Protocol",
        "",
        f"- Global seed: `{GLOBAL_SEED}`",
        "- Input: `02_processed_data/classic/base/*.base.json`",
        "- Output: `02_processed_data/fresh/fresh/*.fresh.json` and `02_processed_data/fresh/fresh_meta/*.fresh.meta.json`",
        "",
        "## Rules",
        "",
        "- service time: `service_time_min = 5 + ceil(0.2 * demand)`",
        "- depot start time: `08:00` (480 minutes)",
        "- time windows by distance band (to depot):",
        "  - near: `[480+j, 720+j]`",
        "  - mid: `[540+j, 840+j]`",
        "  - far: `[600+j, 960+j]`",
        "  - jitter `j` sampled from `[-20, 20]` with deterministic instance seed",
        "- freshness class by demand quantiles (30/70): `low`, `medium`, `high`",
        "- max travel time by freshness: low=300, medium=180, high=90",
        "- temp zone by class-conditional probability:",
        "  - high: frozen 0.35, chilled 0.50, ambient 0.15",
        "  - medium: frozen 0.20, chilled 0.50, ambient 0.30",
        "  - low: frozen 0.10, chilled 0.25, ambient 0.65",
        "- penalties:",
        "  - `late_penalty_per_min = 0.8 * demand`",
        "  - `spoilage_penalty = 2.0 * demand * freshness_weight`",
        "  - freshness_weight: high=1.5, medium=1.0, low=0.7",
        "",
        "## Objective Weights",
        "",
        "- distance: 1.0",
        "- lateness: 1.0",
        "- spoilage: 1.0",
    ]
    protocol_doc.write_text("\n".join(protocol_lines) + "\n", encoding="utf-8")

    qa_lines = [
        "# QA Report (Fresh CVRP)",
        "",
        f"- Total fresh instances generated: {len(fresh_instances)}",
        f"- Instances with validation errors: {len(qa_errors)}",
        "",
        "## Validation Checklist",
        "",
        "- service_time_min > 0",
        "- ready_time_min < due_time_min",
        "- freshness_class in {high, medium, low}",
        "- max_travel_time_min consistent with freshness_class",
        "- temp_zone in {frozen, chilled, ambient}",
        "",
        "## Distribution Summary",
        "",
        f"- freshness_count: {dist['freshness_count']}",
        f"- temp_zone_count: {dist['temp_zone_count']}",
        f"- service_time_min stats: {dist['service_time_min']}",
        f"- time_window_width_min stats: {dist['time_window_width_min']}",
        f"- late_penalty_per_min stats: {dist['late_penalty_per_min']}",
        f"- spoilage_penalty stats: {dist['spoilage_penalty']}",
        "",
        "## Error Details",
        "",
    ]
    if not qa_errors:
        qa_lines.append("- No validation errors detected.")
    else:
        for instance_id in sorted(qa_errors):
            qa_lines.append(f"- {instance_id}: {'; '.join(qa_errors[instance_id])}")
    qa_doc.write_text("\n".join(qa_lines) + "\n", encoding="utf-8")

    schema_lines = [
        "# Fresh Data Schema",
        "",
        "## File: `02_processed_data/fresh/fresh/<instance_id>.fresh.json`",
        "",
        "- Includes all fields from classic `base.json`",
        "- Additional instance-level fields:",
        "  - `problem_variant`",
        "  - `depot_start_time_min`",
        "  - `objective_weights`",
        "- Additional customer-level fields:",
        "  - `distance_to_depot`",
        "  - `distance_band`",
        "  - `service_time_min`",
        "  - `ready_time_min`, `due_time_min`",
        "  - `freshness_class`",
        "  - `max_travel_time_min`",
        "  - `temp_zone`",
        "  - `late_penalty_per_min`",
        "  - `spoilage_penalty`",
        "",
        "## File: `02_processed_data/fresh/fresh_meta/<instance_id>.fresh.meta.json`",
        "",
        "- Generation rules, seeds, and source mapping for full reproducibility.",
    ]
    schema_doc.write_text("\n".join(schema_lines) + "\n", encoding="utf-8")

    print(f"Generated fresh instances: {len(fresh_instances)}")
    print(f"Fresh data dir: {fresh_dir}")
    print(f"Fresh QA report: {qa_doc}")


if __name__ == "__main__":
    main()
