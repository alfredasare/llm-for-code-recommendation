# Metadata-Driven Retrieval Pattern

## Intent

The Metadata-Driven Retrieval Pattern aims to enhance retrieval accuracy by leveraging detailed metadata along with embeddings to refine and filter search results. This approach uses metadata to add context and constraints to the retrieval process, ensuring more relevant and precise results.

## Motivation

When dealing with datasets where the embeddings alone may not capture the distinct details of each entry, using metadata as an additional layer of refinement can help avoid retrieval inaccuracies. This is particularly useful for our use case since multiple CVEs share the same CWE and, therefore, have overlapping tokens that might otherwise confound the embedding retrieval.

## Applicability

The Metadata-Driven Retrieval Pattern is suited for datasets rich in metadata that can enhance retrieval accuracy. This pattern is particularly beneficial when specific metadata fields can be used as filters to greatly enhance the relevance of search results. It is also ideal when embeddings alone may lead to inaccuracies due to shared tokens creating noisy embeddings, requiring metadata to refine the retrieval process.

## Advantages

This approach improves retrieval precision by combining metadata with embeddings, allowing for more granular filtering and yielding highly relevant search results. Metadata filtering ensures that only the most relevant entries are retrieved, avoiding irrelevant or overly similar entries that might otherwise be included through embeddings alone.

## Disadvantages

This pattern requires careful selection of metadata fields to avoid overly restrictive searches. Additionally, not all vector databases support metadata filtering, which limits its applicability unless such features are available.

## Implementation

Metadata fields (CWE-ID, CWE description, and name) are identified, and the contextual data (vulnerable code and fixes) are organized for embedding. These metadata fields are stored as separate attributes alongside the context. For the selected context, both dense and sparse embeddings are generated. The metadata fields are not embedded but are used for filtering during retrieval. The context, dense embeddings, sparse embeddings, and metadata fields are stored in a vector database. This ensures that the vectors and the metadata are available for future retrieval queries.

The system uses dense and sparse embeddings to retrieve initial results when querying the vector database. However, these results are further refined using metadata filtering (e.g., CWE-ID or CWE description). Combining embeddings and metadata ensures that the most relevant results are retrieved, even when multiple vulnerabilities share similar tokens.

### Metadata-Driven Retrieval Pattern Workflow

![Metadata-Driven Retrieval Pattern Workflow](./metadata-driven.png)
