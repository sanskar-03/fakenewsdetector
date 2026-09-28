# Model Card — Aletheia

## Components
- DeBERTa text classifier configured by `MODEL_NAME`.
- all-MiniLM-L6-v2 embeddings with ChromaDB for trusted-source retrieval.
- DuckDuckGo search for current web evidence.
- perceptual hashing for optional image reuse detection.
- Ollama/Llama 3.1 for structured reasoning when available.

## Intended use
College capstone / evidence-assistance and human review.

## Limitations
A classifier is not a truth oracle. Search results can be incomplete or wrong. Stance assignment is conservative heuristic assistance, not a formally validated natural-language-inference model. Image no-match never proves authenticity.
