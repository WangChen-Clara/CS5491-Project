# Classic CVRP Data Pipeline

## Goal

Build a standardized Classic-CVRP dataset package from CVRPLib sets `A/B/E/F/M/P`.

## One-command Run

From project root:

`python scripts/process_cvrplib.py`

## Inputs

- Raw `.vrp` and `.sol` files under set folders:
  - `A/`, `B/`, `E/`, `F/`, `M/`, `P/`

## Outputs

- `data/processed/base/*.base.json`
  - Standardized instance files for algorithms
- `data/processed/meta/*.meta.json`
  - Source trace and parser metadata
- `data/index.csv`
  - Summary table for all instances
- `docs/qa_report.md`
  - Validation result and coverage stats
- `docs/data_schema.md`
  - Field-level schema
- `data/raw/`
  - Copied raw source files for traceability

## Supported CVRPLib Formats

- `EDGE_WEIGHT_TYPE: EUC_2D`
- `EDGE_WEIGHT_TYPE: EXPLICIT` + `EDGE_WEIGHT_FORMAT: LOWER_ROW`

## Validation Per Instance

- Depot demand must be 0
- All customer demands must be > 0
- Customer count must equal `dimension - 1`
- Distance matrix size must be `dimension x dimension`
- Distance matrix must be symmetric
- Distance matrix diagonal must be 0
