# Vanilla Pattern

## Intent

Simplifies the embedding and retrieval process by storing all relevant information about a vulnerability in a single context string.

## Motivation

Useful when dealing with datasets where all relevant information can be captured within a single context block, such as a paragraph from a book or an article.

## Applicability

Applicable in cases where the dataset consists of compact textual information that can be effectively represented in a single block.

## Advantages

Easy to implement and provides a unified context by ensuring that all relevant data is considered when generating the embedding.

## Disadvantages

Single context string can result in similar embeddings for CVEs that share the same CWE category, leading to retrieval inaccuracies.

## Implementation

- Concatenate multiple data fields into a single string.
- Embed the context string into dense vectors and sparse vectors.
- Vectorize the vulnerable code search query.
- Search the vector database using the encoded query vectors to retrieve results.

## Dataset characteristics

- Syntactical diversity.

### Vanilla Pattern Workflow

![Vanilla Pattern Workflow](./vanilla.png)
