# Evaluation Plan

Aletheia intentionally does not publish fabricated accuracy or latency figures. Production evaluation should be performed against a labeled dataset and a controlled deployment.

## Metrics
- Accuracy, precision, recall and macro-F1 for REAL/FAKE classification.
- Evidence retrieval precision@k and recall@k.
- Stance accuracy for SUPPORTS/CONTRADICTS/NEUTRAL.
- p50/p95 end-to-end latency with and without Ollama.
- Cache hit rate and failure rate for provider outages.

## Required scenarios
1. Short and long claims.
2. Multilingual claims supported by the configured tokenizer/model.
3. Strong supporting evidence.
4. Strong contradictory evidence.
5. Conflicting evidence.
6. Empty trusted-source database.
7. Web-search failure.
8. Ollama timeout/unavailability.
9. Invalid image URL and image-download failure.
10. Duplicate verification requests.

Run `pytest -q` for the included deterministic unit/API tests. For benchmark results, supply a labeled dataset and record the deployment hardware and model revisions.
