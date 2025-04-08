# Segmented Context Pattern

## Intent

Enhances retrieval accuracy by embedding only the most essential and unique information while relegating repetitive data to the metadata.

## Motivation

Useful when data can be broken down into metadata key-value pairs, and only the unique aspects of the information are embedded for more precise retrieval.

## Applicability

For datasets where verbose information can be divided into distinct segments to reduce noise in embeddings.

## Advantages

Enables more accurate embeddings by isolating distinct parts of the context, which helps to reduce noise from verbose or irrelevant fields.

## Disadvantages

Requires careful consideration to effectively segment the data to avoid including fields that might cause overlap in the context.

## Implementation

- Selected data fields are concatenated into a string, which is then encoded into both dense and sparse vectors.
- Store the embeddings along with all the metadata as key-value pairs.
- Vectorize the vulnerable code search query.
- Search the vector database using the encoded query vectors to retrieve results.

## Dataset characteristics

- Token overlap
- Semantic similarity
- Syntactical diversity

### Segmented Context Pattern Workflow

![Segmented Context Pattern Workflow](./segmented-context.png)
