---
title: "Managing Embeddings"
source: "https://docs.lancedb.com/embedding/index"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Use the embedding API in LanceDB -- registry, functions, schemas, and multi-language SDK support."
tags:
  - "clippings"
---
Modern machine learning models can be trained to convert raw data into embeddings, which are vectors of floating point numbers. The position of an embedding in vector space captures the semantics of the data, so vectors that are close to each other are considered similar.LanceDB provides an embedding function registry in OSS as well as its Cloud and Enterprise versions ([see below](https://docs.lancedb.com/embedding/#embeddings-in-lancedb-cloud-and-enterprise)) that automatically generates vector embeddings during data ingestion. Automatic query-time embedding generation is available in LanceDB OSS, with SDK-specific query ergonomics. The API abstracts embedding generation, allowing you to focus on your application logic.

## Embedding Registry

You can get a supported embedding function from the registry, and then use it in your table schema. Once configured, the embedding function will automatically generate embeddings when you insert data into the table. Query-time behavior depends on SDK: Python/TypeScript can query with text directly, while Rust examples typically compute query embeddings explicitly before vector search.

### Using an embedding function

Python SDK In the Python SDK, the `.create()` method accepts several arguments to configure embedding function behavior. `max_retries` is a special argument that applies to all providers.Other arguments are provider-specific. Common arguments include the following:Find the full list of arguments for each provider in the [integrations](https://docs.lancedb.com/integrations/embedding) section.

## Embedding model providers

LanceDB supports most popular embedding providers.

### Text embeddings

### Multimodal embedding

You can find all supported embedding models in the [integrations](https://docs.lancedb.com/integrations/embedding) section.

## Embeddings in LanceDB Cloud and Enterprise

Currently, the embedding registry on LanceDB Cloud or Enterprise supports automatic generation of embeddings during data ingestion, generated on the client side (and stored on the remote table). We don’t yet support automatic query-time embedding generation when sending queries, though this is planned for a future release.

The same manual query-embedding flow shown above in OSS applies to Cloud and Enterprise connections.

For search, you can manually generate the embeddings at query time using the same embedding function that was used during ingestion, and pass the embeddings to the search function.

## Custom Embedding Functions

You can always implement your own embedding function:
- Python/TypeScript: subclass `TextEmbeddingFunction` (text) or `EmbeddingFunction` (multimodal).
- Rust: implement the `EmbeddingFunction` trait.

[Evaluation](https://docs.lancedb.com/reranking/eval) [Quickstart](https://docs.lancedb.com/embedding/quickstart)