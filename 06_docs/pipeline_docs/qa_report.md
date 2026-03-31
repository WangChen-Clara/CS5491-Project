# QA Report (Classic CVRP)

- Total instances processed: 95
- Total index rows: 95
- Instances with parser/validation errors: 0

## Coverage by Set

- A: count=27, dimension_range=[32, 80]
- B: count=23, dimension_range=[31, 78]
- E: count=13, dimension_range=[13, 101]
- F: count=3, dimension_range=[45, 135]
- M: count=5, dimension_range=[101, 200]
- P: count=24, dimension_range=[16, 101]

## Validation Checklist

- depot demand equals 0
- all customer demands > 0
- customer count equals dimension - 1
- distance matrix shape equals dimension x dimension
- distance matrix is symmetric
- distance matrix diagonal is zero

## Error Details

- No validation errors detected.
