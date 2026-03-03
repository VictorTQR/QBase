---
title: "Full-Text Search (FTS) Index"
source: "https://docs.lancedb.com/indexing/fts-index"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Create and tune BM25-based full-text search indexes in LanceDB."
tags:
  - "clippings"
---
[Skip to main content](https://docs.lancedb.com/indexing/#content-area)

LanceDB Cloud and Enterprise provide performant full-text search based on BM25, allowing you to incorporate keyword-based search in your retrieval solutions.

The `create_fts_index` API returns immediately, but index building happens asynchronously.

## Creating FTS Indexes

### Synchronous API

Use `create_fts_index` with synchronous LanceDB connections:Check FTS index status using the API:

### Asynchronous API

When using async connections (`connect_async`), use `create_index` with the `FTS` configuration:

The `create_fts_index` method is not available on `AsyncTable`. Use `create_index` with `FTS` config instead.

## Configuration Options

### FTS Parameters

- `max_token_length` can filter out base64 blobs or long URLs.
- Disabling `with_position` reduces index size but disables phrase queries.
- `ascii_folding` helps with international text (e.g., “café” → “cafe”).

### Phrase Query Configuration

Enable phrase queries by setting:

Was this page helpful?

[Vector Index](https://docs.lancedb.com/indexing/vector-index) [Scalar Index](https://docs.lancedb.com/indexing/scalar-index)