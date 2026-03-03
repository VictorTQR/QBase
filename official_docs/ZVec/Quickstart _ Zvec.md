---
title: "Quickstart | Zvec"
source: "https://zvec.org/en/docs/quickstart/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
## Quickstart

## Installation

```
pip install zvec
```

## Create a Collection

A [collection](https://zvec.org/en/docs/collections/) stores your documents. Each [document](https://zvec.org/en/docs/concepts/data-modeling/#documents) contains scalar fields and [vector embeddings](https://zvec.org/en/docs/concepts/vector-embedding/).

Define a schema and create a collection:

## Add Documents

[Insert](https://zvec.org/en/docs/data-operations/insert/) documents with scalar fields and vector embeddings:

## Optimize a Collection

[Optimize](https://zvec.org/en/docs/collections/optimize/) a collection to improve performance:

Optimize a collection

```
collection.optimize()
```

## Retrieve a Document by ID

[Fetch](https://zvec.org/en/docs/data-operations/fetch/) a document directly by its `id`:

## Search with Vectors

### Basic Similarity Search

Use [`query()`](https://zvec.org/en/docs/data-operations/query/) to find documents most similar to a given vector embedding:

Results are ranked by similarity score.

### Filtered Similarity Search

Combine vector search with conditional filters:

Only matching documents are considered during search.

## Inspect a Collection

View the collection's schema:

View collection schema

```
print(collection.schema)
```

View the collection's statistics:

View collection statistics

```
print(collection.stats)
```

## Delete a Document

[Delete](https://zvec.org/en/docs/data-operations/delete/#delete-by-ids) a document by its ID:

Delete a document

```
collection.delete(ids="book_1")
```

[Delete](https://zvec.org/en/docs/data-operations/delete/#delete-by-filter-condition) documents by filter condition:

Delete documents by filter condition

```
collection.delete_by_filter(filter="publish_year < 1900")
```

---

✨ You're all set to store, retrieve, and search vector data with **Zvec**!

💙 Thank you for your interest in **Zvec**! We hope you enjoy exploring what **Zvec** can do!

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[API Reference](https://zvec.org/api-reference/)

[

Previous Page

](https://zvec.org/api-reference/)[

Configuration

Next Page

](https://zvec.org/en/docs/config/)

### On this page

[Installation](https://zvec.org/en/docs/quickstart/#installation) [Create a Collection](https://zvec.org/en/docs/quickstart/#create-a-collection) [Add Documents](https://zvec.org/en/docs/quickstart/#add-documents) [Optimize a Collection](https://zvec.org/en/docs/quickstart/#optimize-a-collection) [Retrieve a Document by ID](https://zvec.org/en/docs/quickstart/#retrieve-a-document-by-id) [Search with Vectors](https://zvec.org/en/docs/quickstart/#search-with-vectors) [Basic Similarity Search](https://zvec.org/en/docs/quickstart/#basic-similarity-search) [Filtered Similarity Search](https://zvec.org/en/docs/quickstart/#filtered-similarity-search) [Inspect a Collection](https://zvec.org/en/docs/quickstart/#inspect-a-collection) [Delete a Document](https://zvec.org/en/docs/quickstart/#delete-a-document)