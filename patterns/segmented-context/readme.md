# Segmented Context Pattern

## Intent

The Segmented Context Pattern aims to enhance retrieval accuracy by embedding only the most essential and unique information while relegating repetitive data to the metadata. This helps to ensure that the retriever can focus on distinct and relevant contexts during the retrieval process, leading to better performance when dealing with verbose and complex data.

## Motivation

In datasets containing verbose information, combining all fields into a single context can lead to excessive noise, making it harder to retrieve accurate results. By breaking the data down into segments and embedding only the unique aspects of the information, this pattern reduces noise and ensures that the retrieval system can better differentiate between various entries. This is especially useful in datasets like CVEFixes and BigVul, where similar tokens across CVEs can lead to retrieval inaccuracies.

## Applicability

The Segmented Context Pattern is suitable for datasets where verbose information can be divided into distinct segments. The primary objective is to reduce noise in the embeddings and improve retrieval accuracy by treating each segment independently. This pattern works well when the data exhibits high variability, and each segment carries a significant weight that should be represented individually.

## Advantages

The Segmented Context Pattern enables more accurate embeddings by isolating distinct parts of the context, which helps to reduce noise from verbose or irrelevant fields, resulting in clearer and more precise retrieval.

## Disadvantages

This pattern requires careful consideration to effectively segment the data, and it may introduce additional complexity in both data preparation and storage.

## Implementation

In this approach, selected metadata fields such as CVE-ID, CWE-ID, and CWE name are concatenated into a context string, which is then encoded into both dense and sparse vectors. We then store the embeddings along with all the metadata as key-value pairs.  
When a query is made, the same encoding process is applied to the query string, generating dense and sparse vectors. These vectors are used to query the vector database to retrieve relevant results.

This pattern helps address the issue of token overlap, especially when multiple CVEs belong to the same CWE, by minimizing the redundancy in the context and improving the distinctiveness of each entry.

### Segmented Context Pattern Workflow

![Segmented Context Pattern Workflow](./segmented-context.png)
