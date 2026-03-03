---
title: "Vector Search"
source: "https://docs.lancedb.com/search/vector-search"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to run vector search queries in LanceDB. Includes best practices, tips and examples."
tags:
  - "clippings"
---
Vector search is a technique used to search for similar items based on their vector representations, called embeddings. It is also known as similarity search, nearest neighbor search, or approximate nearest neighbor search.![](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/search/vector-db-basics.png?w=280&fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=2ef75e6d0d178eab1ba89eeaa7f521e8)

tbl.search(np.random.random((1536))).distance\_type("cosine").limit(10).to\_list()

Raw data (e.g. text, images, audio, etc.) is converted into embeddings via an embedding model, which are then stored in a vector database like LanceDB. To perform similarity search at scale, an index is created on the stored embeddings, which can then used to perform fast lookups.

## Supported distance metrics

Distance metrics determine how LanceDB compares vectors to find similar matches. Euclidean or `l2` is the default, and used for general-purpose similarity, `cosine` for unnormalized embeddings, `dot` for normalized embeddings (best performance), or `hamming` for binary vectors.

Ensure you always use the same distance metric that your embedding model was trained with. Most modern embedding models use cosine similarity, so `cosine` is often the best choice. However, if your vectors are normalized, you should use `dot` for best performance.

The right metric improves both search accuracy and query performance. Currently, LanceDB supports the following metrics:

| Distance metric | Mathematical form | Notes |
| --- | --- | --- |
| `l2` | $\\|x-y\\|_2=\sqrt{\sum_i (x_i-y_i)^2}$ | Measures the straight-line distance between two points in vector space. Calculated as the square root of the sum of squared differences between corresponding vector components. |
| `cosine` | $1-\frac{x\cdot y}{\\|x\\|_2\\|y\\|_2}$ | Measures directional difference between vectors. Computed as 1 minus cosine similarity (the dot product normalized by both vector magnitudes), so vector length does not affect the score. Use for unnormalized vectors. |
| `dot` | $x\cdot y=\sum_i x_i y_i$ | Calculates the sum of products of corresponding vector components. Provides raw similarity scores without normalization, sensitive to vector magnitudes. Use for normalized vectors for best performance. |
| `hamming` | $\sum_i \mathbf{1}[x_i\neq y_i]$ | Counts the number of positions where corresponding bits differ between binary vectors. Only applicable to binary vectors stored as packed uint8 arrays. |

For indexed search, supported distance metrics vary by index type:

### Configure Distance Metric

By default, `l2` will be used as metric type. You can specify the metric type as `cosine` or `dot` if required (`hamming` is supported for `IVF_FLAT` index only).**Note:** You can configure the distance metric during search only if there’s no vector index. If a vector index exists, the distance metric will always be the one you specified when creating the index.Here you can see the same search but using `cosine` similarity instead of `l2` distance. The result focuses on vector direction rather than absolute distance, which works better for normalized embeddings.Instead of performing an exhaustive search on the entire database for each and every query, approximate nearest neighbour (ANN) algorithms use an index to narrow down the search space, which significantly reduces query latency.The trade-off is that the results are not guaranteed to be the true nearest neighbors of the query, but are usually “good enough” for most use cases.Use ANN search for large-scale applications where speed matters more than perfect recall. LanceDB uses approximate nearest neighbor algorithms to deliver fast results without examining every vector in your dataset.

When a vector index is used, `_distance` is not always the true distance between full vectors. In ANN mode without refinement, LanceDB computes `_distance` using compressed vectors for speed.

### Exact vs Approximate Distances

When doing vector search, the meaning of “distance” depends on whether you are using an index and whether `refine_factor` is specified as part of your query.`nprobes` controls how many partitions are searched to find candidates, while `refine_factor` controls how many candidates are rescored on full vectors for better distance fidelity and reranking quality.The table below summarizes the behavior of `_distance` in search results based on your query configuration:For deeper tuning guidance on indexing and performance estimation, see the [vector indexes](https://docs.lancedb.com/indexing/vector-index#search-configuration) page, For tuning `nprobes`, see below.

### Tuning nprobes

- `nprobes` controls how many partitions are searched at query time.
- `nprobes` improves candidate recall, but does not by itself make `_distance` exact.
- By default, LanceDB automatically tunes `nprobes` to achieve the best performance without noticeably sacrificing accuracy.
- In most cases, leave `nprobes` unset and use the auto-tuned value.
- Only tune `nprobes` manually when recall is below your target, or when you need even higher performance for your workload.
- If recall is too low, increase `nprobes` gradually, but after a certain threshold, increasing `nprobes` yields only marginal accuracy gains.
- If you need higher performance and have recall headroom, decrease `nprobes` gradually.
This is the default vector search setting. You can use prefiltering to boost query performance by reducing the search space before vector calculations begin. The system first applies your filter criteria to the dataset, then conducts vector search operations only on the remaining relevant subset.This filters out rows where label ≤ 2 before doing vector search, then picks specific columns from the top 5 matches.The `.where("label > 2")` applies a filter before vector search, `.select(["text", "keywords", "label"])` chooses specific columns to return, and `.limit(5)` restricts results to the top `5` most similar vectors.As a result, you’ll see a pandas DataFrame with just the data you want from the most similar vectors.Use postfiltering to prioritize vector similarity by searching the full dataset first, then applying metadata filters to the top results. This approach ensures you get the most similar vectors before filtering, which can be crucial when similarity is more important than metadata constraints.Here you can see how to do vector search first to get the most similar vectors, then filter by label > 1 on those results.The `prefilter=False` parameter tells LanceDB to apply the filter after vector search instead of before, `.where("label > 1")` filters the top results by metadata, and `.select()` chooses which columns to include.In the end, you receive a pandas DataFrame with the best matches that also meet your metadata requirements.

[Post-filtering](https://docs.lancedb.com/search/filtering#post-filtering-with-vector-search) in LanceDB applies the filter condition after obtaining the nearest neighbors based on vector similarity.

Use multivector search when your documents contain multiple embeddings and you need sophisticated matching between query and document vector pairs. The late interaction approach finds the most relevant combinations across all available embeddings and provides nuanced similarity scoring.Only `cosine` similarity is supported as the distance metric for multivector search operations.Here you can see how to take 2 query vectors and find the best matching pairs between them and document vectors using late interaction. The `np.random.random(size=(2, 256))` creates a 2×256 array with two random query vectors, `.limit(5)` returns the top 5 best document-query combinations, and `.to_pandas()` provides results in a DataFrame format.**Read more:**[Multivector search](https://docs.lancedb.com/search/multivector-search)

### Search With Distance Range

Use `distance_range` search when you need vectors within particular similarity bounds rather than just the closest neighbors. The system filters results to only include vectors that fall within your specified distance thresholds from the query.This shows three ways to search within distance ranges: bounded, upper bound only, and lower bound only.The `distance_range()` method filters results by similarity thresholds - the first example finds vectors with distance between `0.1` and `0.5`, the second finds vectors closer than `0.5`, and the third finds vectors farther than `0.1`.Each approach returns Arrow tables with vectors that fall within your specified distance thresholds.

### Search With Binary Vectors

Use binary vector search for scenarios involving binary embeddings, such as those produced by hashing algorithms. The system stores these efficiently as packed uint8 arrays and uses Hamming distance calculations to determine vector similarity.

The number of dimensions of the binary vector must be a multiple of 8. A vector of dimensionality 128 will be stored as a `uint8` array of size 16.

Here you can see how to set up a table for binary vectors, pack them efficiently into bytes, and search using Hamming distance.The schema defines a 32-byte vector field (256 bits ÷ 8), `np.random.randint(0, 2, size=256)` creates binary vectors, `np.packbits()` compresses them to bytes, and `.distance_type("hamming")` specifies `hamming` distance for similarity calculation.The search produces an Arrow table with binary vectors ranked by how many bits differ from the query.Use batch search to handle multiple query vectors simultaneously. This gives you significant efficiency gains over individual queries. LanceDB processes all vectors in parallel and organizes results with a `query_index` field that maps each result set back to its originating query.This takes 5 query embeddings and finds the top 5 matches for each one in a single batch operation.The `load_dataset()` loads embeddings from a Hugging Face dataset, `query_embeds` contains `5` query vectors, and `.search(query_embeds)` processes all queries simultaneously.The final result is a pandas DataFrame with all results, including a `query_index` to tell you which query each result came from.

When processing batch queries, the results include a `query_index` field to explicitly associate each result set with its corresponding query in the input batch.

### Search With Asynchronous Indexing

To optimize for speed over completeness, enable the `fast_search` flag in your query to skip searching unindexed data.While vector indexing occurs asynchronously, newly added vectors are immediately searchable through a fallback brute-force search mechanism. This ensures zero latency between data insertion and searchability, though it may temporarily increase query response times.Here you can see how to turn on fast search mode to skip unindexed vectors and only look through indexed data for speed.The `fast_search=True` parameter tells LanceDB to only search indexed vectors, skipping any recently added data that hasn’t been indexed yet.You’ll obtain a pandas DataFrame with the top `5` matches from indexed vectors, but might miss data that was just added.

### Search With No Index

The simplest way to perform vector search is to perform a brute force search, without an index, where the distance between the query vector and all the vectors in the database are computed, with the top-k closest vectors returned.This is equivalent to a k-nearest neighbours (kNN) search in vector space.Choose brute force search when you need guaranteed 100% recall, typically with smaller datasets where query speed isn’t the primary concern. The system scans every vector in the table and calculates precise distances to find the exact nearest neighbors.

```
tbl.search(np.random.random((1536))).limit(3).to_list()
```

This carries out a brute force search through every vector in the table to find the 3 closest matches to a random 1536-dimensional query. You’ll get back a list of the most similar vectors with exact distances.![](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/search/knn_search.png?w=280&fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=49a76a69fef121201ddcf92aa1f22e39)

import lancedb import numpy as np import pyarrow as pa import pytest db = lancedb.connect("data/binary\_lancedb") schema = pa.schema( \[ pa.field("id", pa.int64()), # for dim=256, lance stores every 8 bits in a byte # so the vector field should be a list of 256 / 8 = 32 bytes pa.field("vector", pa.list\_(pa.uint8(), 32)), \] ) tbl = db.create\_table("my\_binary\_vectors", schema=schema) data = \[\] for i in range(1024): vector = np.random.randint(0, 2, size=256) # pack the binary vector into bytes to save space packed\_vector = np.packbits(vector) data.append( { "id": i, "vector": packed\_vector, } ) tbl.add(data) query = np.random.randint(0, 2, size=256) packed\_query = np.packbits(query) tbl.search(packed\_query).distance\_type("hamming").to\_arrow()

As you can imagine, the brute force approach is not scalable for datasets larger than a few hundred thousand vectors, as the latency of the search grows linearly with the size of the dataset. This is where approximate nearest neighbour (ANN) algorithms come in.

### Bypass the Vector Index

Use `bypass_vector_index` to get exact, ground-truth results by performing exhaustive searches across all vectors. Instead of relying on approximate methods, the system directly compares your query against every vector in the table, ensuring 100% recall at the cost of increased query time.

```
table.search(embedding).bypass_vector_index().limit(5).to_pandas()
```

This skips the approximate index and checks every single vector for exact, ground-truth results.The `.bypass_vector_index()` method forces LanceDB to perform an exhaustive search through all vectors instead of using the approximate nearest neighbor index, ensuring exact results but at the cost of slower performance.The outcome is a pandas DataFrame with the top 5 exact matches, guaranteeing 100% recall but taking longer to run.This approach is particularly useful when:
- Evaluating ANN index quality
- Calculating recall metrics to tune index parameters
- Ensuring exact results for critical applications

[Overview](https://docs.lancedb.com/search) [Multivector search](https://docs.lancedb.com/search/multivector-search)