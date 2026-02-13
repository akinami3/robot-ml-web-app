# ADR-005: Local LLM

## Status
**Accepted**

## Context
RAG feature needs:
- Text generation for Q&A
- Text embedding for vector search
- Must run locally (no cloud API dependency)
- Reasonable hardware requirements

## Decision
**Ollama + Llama 3 (chat) + nomic-embed-text (embeddings)**

## Alternatives Considered

| Criteria | Ollama + Llama 3 | vLLM + Mistral | llama.cpp + GGUF | LocalAI |
|----------|:---:|:---:|:---:|:---:|
| Setup simplicity | ★★★★★ | ★★★ | ★★★ | ★★★★ |
| Chat quality | ★★★★★ | ★★★★★ | ★★★★ | ★★★★ |
| Embedding support | ★★★★ | ★★★ | ★★ | ★★★★ |
| Docker integration | ★★★★★ | ★★★★ | ★★★ | ★★★★★ |
| GPU optional | ★★★★★ | ★★ | ★★★★ | ★★★★ |

## Rationale
- **Ollama**: Simple HTTP API, Docker image, auto-downloads models, CPU/GPU agnostic
- **Llama 3 8B**: Best open-source chat model in its size class
- **nomic-embed-text**: 768-dim embeddings, good quality, fast
- Simple HTTP integration (no gRPC/custom protocol needed)
- `ollama pull llama3 && ollama pull nomic-embed-text` — ready in minutes
