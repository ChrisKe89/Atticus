# Evaluation Reports

CI and local evaluation runs should publish structured artifacts under this directory.
Each run should include:

* `metrics.csv` – aggregate retrieval metrics (Recall@k, MRR@k, accuracy, latency).
* `summary.json` – machine-readable summary for regression gates.
* `metrics.html` – human-friendly dashboard for reviewers (captured by CI artifacts).

The repository ships with `sample-eval.csv` and `sample-eval.html` to illustrate the
expected schema. `make eval` will populate fresh artifacts and overwrite previous snapshots.
GitHub Actions uploads
the contents of `eval/runs/ci` (`metrics.csv`, `summary.json`, `metrics.html`) as the
`evaluation-ci` artifact for every PR and push to `main`.
