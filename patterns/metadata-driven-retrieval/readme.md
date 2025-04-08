# Metadata-Driven Retrieval Pattern

## Intent

Builds on the segmented context pattern and enhances retrieval accuracy by leveraging detailed metadata along with embeddings to refine and filter search results.

## Motivation

Useful for data that can be broken down into metadata key-value pairs and can leverage metadata fields to filter down retrieval results.

## Applicability

For datasets rich in metadata that can enhance retrieval accuracy by leveraging metadata fields as filters to enhance the relevance of search results.

## Advantages

Improves retrieval precision by combining metadata with embeddings, allowing for more granular filtering and yielding highly relevant results.

## Disadvantages

Requires careful selection of metadata fields for filtering to avoid overly restrictive searches.

## Implementation

- Concatenate unique metadata fields into a single string.
- Store the embeddings along with all the metadata as key-value pairs.
- Vectorize the vulnerable code search query.
- Search the vector database using the encoded query vectors and the metadata fields to retrieve results.

## Dataset characteristics

- Token overlap
- Metadata uniqueness
- Semantic similarity
- Syntactical diversity

### Metadata-Driven Retrieval Pattern Workflow

![Metadata-Driven Retrieval Pattern Workflow](./metadata-driven.png)
