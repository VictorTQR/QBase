---
title: "Versioning and Reproducibility"
source: "https://docs.lancedb.com/tables/versioning"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to implement versioning and ensure reproducibility in LanceDB. Includes version control, data snapshots, and audit trails."
tags:
  - "clippings"
---
LanceDB redefines data management for AI/ML workflows with built-in, automatic versioning powered by the [Lance columnar format](https://github.com/lancedb/lance). Every table mutation—appends, updates, deletions, or schema changes — is tracked with zero configuration, enabling:
- Time-Travel Debugging: Pinpoint production issues by querying historical table states.
- Atomic Rollbacks: Revert terabyte-scale datasets to any prior version in seconds.
- ML Reproducibility: Exactly reproduce training snapshots (vectors + metadata).
- Branching Workflows: Conduct A/B tests on embeddings/models via lightweight table clones.

## Basic Versioning Example

Let’s create a table with sample data to demonstrate LanceDB’s versioning capabilities:

### Setting Up the Table

First, let’s create a table with some sample data:

### Checking Initial Version

After creating the table, let’s check the initial version information:

## Modifying Data

When you modify data through operations like update or delete, LanceDB automatically creates new versions.

### Updating Existing Data

Let’s update some existing records to see versioning in action:

### Adding New Data

Now let’s add more records to the table:

### Checking Version Changes

Let’s see how the versions have changed after our modifications:

## Tracking Changes in Schema

LanceDB’s versioning system automatically tracks every schema modification. This is critical when handling evolving embedding models. For example, adding a new `vector_minilm` column creates a fresh version, enabling seamless A/B testing between embedding generations without recreating the table.

### Preparing Data for Embeddings

First, let’s get the data we want to embed:

### Generating Embeddings

Now let’s generate embeddings using the all-MiniLM-L6-v2 model:

### Adding Vector Column to Schema

Now let’s add the vector column to our table schema:

### Checking Version Changes After Schema Modification

Let’s see how the schema change affected our versioning:

## Rollback to Previous Versions

LanceDB supports fast rollbacks to any previous version without data duplication.

### Viewing All Versions

First, let’s see all the versions we’ve created:

### Rolling Back to a Previous Version

Now let’s roll back to before we added the vector column:

## Making Changes from Previous Versions

After restoring a table to an earlier version, you can continue making modifications. In this example, we rolled back to a version before adding embeddings. This allows us to experiment with different embedding models and compare their performance.

### Switching to a Different Embedding Model

Let’s try a different embedding model (all-mpnet-base-v2) to see how it performs:

### Adding the New Vector Column

Now let’s add the new vector column with the different model:

### Checking Version Changes

Let’s see how this new model affects our versioning:

## Delete Data From the Table

Let’s demonstrate how deletions also create new versions:

### Going Back to Latest Version

First, let’s return to the latest version:

### Deleting Data

Now let’s delete some data to see how it affects versioning:

### Version History and Operations

Throughout this guide, we’ve demonstrated various operations that create new versions in LanceDB. Here’s a summary of the version history we created:
1. **Initial Creation** (v1): Created table with quotes data and basic schema
2. **First Update** (v2): Changed “Richard” to “Richard Daniel Sanchez”
3. **Data Append** (v3): Added new quotes from both characters
4. **Schema Evolution** (v4): Added `vector_minilm` column for embeddings
5. **Embedding Merge** (v5): Populated `vector_minilm` with embeddings
6. **Version Rollback** (v6): Restored to v3 (pre-vector state)
7. **Alternative Schema** (v7): Added `vector_mpnet` column
8. **Alternative Merge** (v8): Populated `vector_mpnet` embeddings
9. **Data Cleanup** (v9): Kept only Richard Daniel Sanchez quotes
Each version represents a distinct state of your data, allowing you to:
- Track changes over time
- Compare different embedding strategies
- Revert to previous states
- Maintain data lineage for ML reproducibility

**System Operations** System operations like `optimize()`, index updates, and table compaction also increment table version numbers. In LanceDB OSS and Cloud, `optimize()` can prune older versions based on its retention setting (`cleanup_older_than`, 7 days by default), which is when old-version files are removed and disk space is reclaimed.

[Namespaces](https://docs.lancedb.com/tables/namespaces) [Consistency](https://docs.lancedb.com/tables/consistency)