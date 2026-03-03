---
title: "Optimize Query Performance"
source: "https://docs.lancedb.com/search/optimize-queries"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Analyze and optimize query performance in LanceDB."
tags:
  - "clippings"
---
LanceDB provides two powerful tools for query analysis and optimization: `explain_plan` and `analyze_plan`. Let’s take a better look at how they work:

## Query Analysis Tools

### explain\_plan

Reveals the logical query plan before execution, helping you identify potential issues with query structure and index usage. This tool is useful for:
- Verifying query optimization strategies
- Validating index selection
- Understanding query execution order
- Detecting missing indices

### analyze\_plan

Executes the query and provides detailed runtime metrics, including:
- Operation duration (`_elapsed_compute_`)
- Data processing statistics (`_output_rows_`, `_bytes_read_`)
- Index effectiveness (`_index_comparisons_`, `_indices_loaded_`)
- Resource utilization (`_iops_`, `_requests_`)
Together, these tools offer a comprehensive view of query performance, from planning to execution. Use `explain_plan` to verify your query structure and `analyze_plan` to measure and optimize actual performance.

## Reading the Execution Plan

To demonstrate query performance analysis, we’ll use a table containing 1.2M rows sampled from the [Wikipedia dataset](https://huggingface.co/datasets/wikimedia/wikipedia). Initially, the table has no indices, allowing us to observe the impact of optimization.Let’s examine a vector search query that:
- Filters rows where `identifier` is between 0 and 1,000,000
- Returns the top 100 matches
- Projects specific columns: `chunk_index`, `title`, and `identifier`

### Execution Plan Components

The execution plan reveals the sequence of operations performed to execute your query. Let’s examine each component:

#### 1\. Base Layer (LanceScan)

- Initial data scan loading only specified columns to minimize I/O
- Unordered scan enabling parallel processing

#### 2\. First Filter

- Apply requested filter on `identifier` column
- Reduces the number of vectors that need KNN computation
- Computes L2 (Euclidean) distances between query vector and all vectors that passed the filter

#### 4\. Results Processing

- Filters out null distance results
- Sorts by distance and takes top 100 results
- Processes in batches of 1024 for optimal memory usage

#### 5\. Data Retrieval

- `RemoteTake` is a key component of Lance’s I/O cache
- Handles efficient data retrieval from remote storage locations
- Fetches specific rows and columns needed for the final output
- Optimizes network bandwidth by only retrieving required data

#### 6\. Final Output

- Returns only requested columns and maintains column ordering
This plan demonstrates a basic search without index optimizations: it performs a full scan and filter before vector search.

## Performance Analysis

Let’s use `analyze_plan` to run the query and analyze the query performance, which will help us identify potential bottlenecks:

### Performance Metrics Analysis

- Scanned 1,200,000 rows from the LanceDB table
- Read 1.86GB of data in 78 I/O operations
- Only loaded necessary columns (`vector` and `identifier`)
- Unordered scan for parallel processing
- Applied prefilter condition (`identifier > 0 AND identifier < 1000000`)
- Reduced dataset from 1.2M to 1,099,508 rows
- KNN search used L2 (Euclidean) distance metric
- Vector comparisons processed in 1076 batches

#### 3\. Results Processing

- KNN results sorted by distance (TopK with fetch=100)
- Null distances filtered out
- Batches coalesced to target size of 1024 rows
- Additional columns fetched for final results
- Remote take operation for 100 results
- Final projection of required columns

### Key Observations

- Vector search is the primary bottleneck (1,099,508 vector comparisons)
- Significant I/O overhead (1.86GB data read)
- Full table scan due to lack of indices
- Substantial optimization potential through proper index implementation

## Optimized Query Execution

After creating vector and scalar indices, the execution plan shows:

### Optimized Plan Analysis

#### 1\. Scalar Index Query

- Range filter using scalar index
- Only 2 index files and 562 scalar index parts loaded
- 2.3M index comparisons for matches
- IVF index with 20 probes
- Only 20 index parts loaded
- 25,893 vector comparisons
- 2,000 matching vectors

#### 3\. Results Processing

- Sorts by distance
- Limits to top 100 results
- Batches into groups of 1024

#### 4\. Data Fetching

- Single output batch
- One remote take per row

#### 5\. Final Projection

- Returns specified columns: chunk\_index, title, identifier, and distance

### Performance Improvements

#### 1\. Initial Data Access

- Before: Full table scan of 1.2M rows, 1.86GB data
- After: Only 2 indices and 562 scalar index parts loaded
- Benefit: Eliminated table scans for prefilter
- Before: L2 calculations on 1,099,508 vectors
- After:
	- 99.8% reduction in vector comparisons
	- Decreased output batches from 1,076 to 20

#### 3\. Data Retrieval Optimization

- RemoteTake operation remains consistent

## Performance Optimization Guide

### 1\. Index Implementation

#### When to Create Indices

- Columns used in WHERE clauses
- Vector columns for similarity searches
- Join columns used in `merge_insert`

#### Index Type Selection

## Index Coverage Monitoring

Use `table.index_stats()` to monitor index coverage. A well-optimized table should have `num_unindexed_rows ~ 0`.

### 2\. Query Plan Optimization

#### Common Patterns and Fixes

!!! note “Regular Performance Analysis” Regularly analyze your query plans to identify and address performance bottlenecks. The `analyze_plan` output provides detailed metrics to guide optimization efforts.

### 3\. Getting Started with Optimization

For vector search performance:
- Create ANN index on your vector column(s) as described in the [index guide](https://docs.lancedb.com/indexing/vector-index)
- If you often filter by metadata, create [scalar indices](https://docs.lancedb.com/indexing/scalar-index) on those columns

[Filtering](https://docs.lancedb.com/search/filtering) [SQL](https://docs.lancedb.com/search/sql)