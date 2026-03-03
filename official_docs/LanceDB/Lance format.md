---
title: "Lance format"
source: "https://docs.lancedb.com/lance"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Open-source lakehouse format for multimodal AI."
tags:
  - "clippings"
---
[Lance](https://lance.org/) is an open-source lakehouse format, which provides the foundation for LanceDB’s capabilities. Lance combines the performance of Apache Arrow with advanced features designed specifically for AI workloads.Lance format documentation

Learn more about the Lance format by reading the docs.

[View original](https://lance.org/quickstart)

## How Lance Enables the Multimodal Lakehouse

Lance is a file format, table format, and catalog spec for multimodal AI, allowing developers to build a complete open lakehouse on top of object storage to power AI workflows. The format brings high-performance vector search, full-text search, random access, and feature engineering capabilities to a single unified system, eliminating the need for multiple specialized databases.Unlike traditional vector databases that only store embeddings alongside the metadata, LanceDB’s multimodal lakehouse stores both the original data (including image, video or audio bytes) and its vector representations alongside traditional tabular data in the same efficient format.

## Advantages of the Lance format

## Key concepts

The following concepts are core to the Lance format:

### Data versioning

Data in Lance tables are versioned — this helps keep LanceDB scalable and consistent. We do not immediately blow away old versions when creating new ones because other clients might be in the middle of querying the old version. It’s important to retain older versions for as long as they might be queried.Each version contains metadata and just the new/updated data in your transaction. So if you have 100 versions, they aren’t 100 duplicates of the same data. However, they do have 100x the metadata overhead of a single version, which can result in slower queries.

### Data compaction

As you insert more data, your dataset will grow and you’ll need to perform compaction to maintain query throughput (i.e., keep latencies down to a minimum). Compaction is the process of merging fragments together to reduce the amount of metadata that needs to be managed, and to reduce the number of files that need to be opened while scanning the dataset.Running compaction on a Lance dataset will do the following:
- Remove deleted rows from fragments
- Remove dropped columns from fragments
- Merge small fragments into larger ones
Compaction focuses on read performance, not immediate disk reclamation. During compaction, Lance writes new compacted files while older files are still referenced by previous table versions. This means disk usage can increase temporarily until old versions are cleaned up.

### Data deletion and recovery

Although Lance allows you to delete rows from a dataset, it does not actually delete the data immediately. It simply marks the row as deleted in the `DataFile` that represents a fragment.For a given version of the dataset, each fragment can have up to one deletion file (if no rows were ever deleted from that fragment, it will not have a deletion file). This is important to keep in mind because it means that the data is still there, and can be recovered if needed, as long as that version still exists based on your backup policy.Learn more about Lance

Lance is a separate open source project. Check out its documentation to learn more.

[View original](https://lance.org/quickstart)

[LanceDB](https://docs.lancedb.com/) [Namespaces](https://docs.lancedb.com/namespaces)