# JATAYUv1.0 EDA & Priors Findings

## Dataset Summary

Annotation files found: 29413
Empty annotation files: 758
Total annotated objects: 250027

## Class Imbalance

Most frequent classes: tractor_trolley, bus, car
Least frequent classes: bicycle, motorcycle, cycle_rickshaw

## Dirichlet Priors

The prior uses alpha_k = n_k + 1.
Observed share = n_k / N.
Posterior mean = (n_k + 1) / (N + K).

## Count Distribution Analysis

The dispersion index is sample variance divided by sample mean.
A Poisson model has theoretical mean equal to variance.
An index above one suggests overdispersion but does not alone
establish that a Negative Binomial model is appropriate.

| Class | Images | Objects | Mean | Variance | Dispersion | Status |
|---|---:|---:|---:|---:|---:|---|
| auto_rickshaw | 29413 | 20072 | 0.6824 | 2.7787 | 4.0718 | Overdispersed |
| bicycle | 29413 | 6452 | 0.2194 | 0.2614 | 1.1917 | Intermediate dispersion |
| bus | 29413 | 47337 | 1.6094 | 34.7888 | 21.6162 | Overdispersed |
| car | 29413 | 26311 | 0.8945 | 6.2527 | 6.9899 | Overdispersed |
| cycle_rickshaw | 29413 | 15084 | 0.5128 | 4.7916 | 9.3434 | Overdispersed |
| e_rickshaw | 29413 | 22916 | 0.7791 | 1.6951 | 2.1757 | Overdispersed |
| motorcycle | 29413 | 7692 | 0.2615 | 0.3470 | 1.3269 | Intermediate dispersion |
| pedestrian | 29413 | 21461 | 0.7296 | 1.6480 | 2.2587 | Overdispersed |
| tractor_trolley | 29413 | 57204 | 1.9449 | 34.2783 | 17.6251 | Overdispersed |
| truck | 29413 | 25498 | 0.8669 | 19.8095 | 22.8510 | Overdispersed |

## Interpretation Limitations

- Empty annotation files are included as zero-object images.
- Files without annotations are not necessarily invalid files.
- Annotation-file inventory does not detect images missing label files.
- Bounding-box area is a normalized image-space quantity.
- Dispersion thresholds are descriptive heuristics, not model-selection tests.

## Output Artifacts

- `docs/eda/class_frequency.png`
- `docs/eda/objects_per_image.png`
- `docs/eda/box_size_dist.png`
- `r/class_prior.csv`
- `r/count_stats.csv`
