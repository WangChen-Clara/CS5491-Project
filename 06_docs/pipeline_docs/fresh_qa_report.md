# QA Report (Fresh CVRP)

- Total fresh instances generated: 95
- Instances with validation errors: 0

## Validation Checklist

- service_time_min > 0
- ready_time_min < due_time_min
- freshness_class in {high, medium, low}
- max_travel_time_min consistent with freshness_class
- temp_zone in {frozen, chilled, ambient}

## Distribution Summary

- freshness_count: {'high': 1498, 'medium': 2046, 'low': 1761}
- temp_zone_count: {'frozen': 1067, 'chilled': 2245, 'ambient': 1993}
- service_time_min stats: {'min': 6, 'max': 4328, 'mean': 17.72}
- time_window_width_min stats: {'min': 240, 'max': 360, 'mean': 298.8}
- late_penalty_per_min stats: {'min': 0.8, 'max': 17288.8, 'mean': 49.28}
- spoilage_penalty stats: {'min': 1.4, 'max': 64833.0, 'mean': 157.65}

## Error Details

- No validation errors detected.
