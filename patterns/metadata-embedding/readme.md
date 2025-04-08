# Metadata Embedding Pattern

## Intent

Generate embeddings based on key-value pair fields without combining them into a single context or string.

## Motivation

Useful when dealing with datasets where each piece of key-value pair carries significant weight and should be represented independently.

## Applicability

Ideal when the dataset contains structured data with distinct fields that require individual representation.

## Advantages

Attempts to capture detailed and distinct information for each key-value pair, ensuring that each piece of data retains its unique representation.

## Disadvantages

Complex to implement and similar embeddings may arise if multiple entries share similar key-value pairs, potentially leading to token overlap.

## Implementation

- Individually encoding each data field into dense and sparse vectors.
- Sparse and dense vectors are created based on individual key-value pairs and combined.
- Vectorize the vulnerable code search query.
- Search the vector database using the encoded query vectors to retrieve results.

## Dataset characteristics

- Metadata uniqueness
- Syntactical diversity

### Metadata Embedding Pattern Workflow

![Metadata Embedding Pattern Workflow](./metadata-embedding.png)
