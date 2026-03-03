---
title: "Hybrid Search"
source: "https://docs.lancedb.com/search/hybrid-search"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to perform hybrid search in LanceDB by combining vector and full-text search techniques with reranking."
tags:
  - "clippings"
---
In certain cases, you may want to retrieve documents that are semantically similar to a given query, but also prioritize specific keywords. This is an example of **hybrid search**, a query method that combines multiple search techniques.For detailed examples, look at this [Python Notebook](https://colab.research.google.com/github/lancedb/vectordb-recipes/blob/main/examples/saas_examples/python_notebook/Hybrid_search.ipynb) or the [**TypeScript Example**](https://github.com/lancedb/vectordb-recipes/tree/main/examples/saas_examples/ts_example/hybrid-search)

### 1\. Setup

Import the necessary libraries and dependencies for working with LanceDB, OpenAI embeddings, and reranking.

### 2\. Connect to LanceDB Cloud

Establish a connection to your LanceDB instance, with different options for Cloud, Enterprise, and Open Source deployments.For Open Source:For LanceDB Enterprise, set the host override to your private cloud endpoint:

### 3\. Configure Embedding Model

Set up the any embedding model that will convert text into vector representations for semantic search.

### 4\. Create Table & Schema

Define the data structure for your documents, including both the text content and its vector representation.

### 5\. Add Data

Insert sample documents into your table, which will be used for both semantic and keyword search.

### 6\. Build Full Text Index

Create a full-text search index on the text column to enable keyword-based search capabilities.

### 7\. Set Reranker \[Optional\]

Initialize the reranker that will combine and rank results from both semantic and keyword search. By default, lancedb uses RRF reranker, but you can choose other rerankers like `Cohere`, `CrossEncoder`, or others lister in integrations section.Perform a hybrid search query that combines semantic similarity with keyword matching, using the specified reranker to merge and rank the results.You can also pass the vector and text query explicitly. This is useful if you’re not using the embedding API or if you’re using a separate embedder service.You can perform hybrid search in LanceDB by combining the results of semantic and full-text search via a reranking algorithm of your choice. LanceDB comes with [**built-in rerankers**](https://lancedb.github.io/lancedb/reranking/) and you can implement your own **custom reranker** as well.By default, LanceDB uses `RRFReranker()`, which uses reciprocal rank fusion score, to combine and rerank the results of semantic and full-text search. You can customize the hyperparameters as needed or write your own custom reranker. Here’s how you can use any of the available rerankers:

[Full-Text Search (FTS)](https://docs.lancedb.com/search/full-text-search) [Filtering](https://docs.lancedb.com/search/filtering)