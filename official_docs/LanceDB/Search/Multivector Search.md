---
title: "Multivector Search"
source: "https://docs.lancedb.com/search/multivector-search"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to perform multivector search in LanceDB to handle multiple vector embeddings per document, ideal for late interaction models like ColBERT and ColPaLi."
tags:
  - "clippings"
---
LanceDB’s multivector support enables you to store and search multiple vector embeddings for a single item.This capability is particularly valuable when working with late interaction models like ColBERT and ColPaLi that generate multiple embeddings per document.In this tutorial, you’ll create a table with multiple vector embeddings per document and learn how to perform multivector search. [For all the code - open in Colab](https://colab.research.google.com/github/lancedb/vectordb-recipes/blob/main/examples/saas_examples/python_notebook/Multivector_on_LanceDB_Cloud.ipynb)

## Multivector Support

Each item in your dataset can have a column containing multiple vectors, which LanceDB can efficiently index and search. When performing a search, you can query using either a single vector embedding or multiple vector embeddings.

Currently, only the `cosine` metric is supported for multivector search. The vector value type can be `float16`, `float32`, or `float64`.

## Computing Similarity

MaxSim (Maximum Similarity) is a key concept in late interaction models that:
- Computes the maximum similarity between each query embedding and all document embeddings
- Sums these maximum similarities to get the final relevance score
- Effectively captures fine-grained semantic matches between query and document tokens
The MaxSim calculation can be expressed as:
$$
\text{MaxSim}(Q, D) = \sum_{i=1}^{|Q|} \max_{j=1}^{|D|} \text{sim}(q_i, d_j)
$$
 Where $sim$ is the similarity function (e.g. cosine similarity).
$$
Q = \{q_1, q_2, ..., q_{|Q|}\}
$$
 $Q$ represents the query vector, and $D = \{d_1, d_2, ..., d_{|D|}\}$ represents the document vectors.

For now, you should use only the `cosine` metric for multivector search. The vector value type can be `float16`, `float32` or `float64`.

### 1\. Setup

Connect to LanceDB and import required libraries for data management.

### 2\. Define Schema

Define a schema that specifies a multivector field. A multivector field is a nested list structure where each document contains multiple vectors. In this case, we’ll create a schema with:
1. An ID field as an integer (int64)
2. A vector field that is a list of lists of float32 values
	- The outer list represents multiple vectors per document
	- Each inner list is a 256-dimensional vector
	- Using float32 for memory efficiency while maintaining precision

### 3\. Generate Multivectors

Generate sample data where each document contains multiple vector embeddings, which could represent different aspects or views of the same document.In this example, we create **1024 documents** where each document has **2 random vectors** of **dimension 256**, simulating a real-world scenario where you might have multiple embeddings per item.

### 4\. Create a Table

Create a table with the defined schema and sample data, which will store multiple vectors per document for similarity search.

### 5\. Build an Index

Only cosine similarity is supported as the distance metric for multivector search operations. For faster search, build the standard `IVF_PQ` index over your vectors:

### 6\. Query a Single Vector

When searching with a single query vector, it will be compared against all vectors in each document, and the similarity scores will be aggregated to find the most relevant documents.

### 7\. Query Multiple Vectors

With multiple vector queries, LanceDB calculates similarity using late interaction - a technique that computes relevance by finding the best matching pairs between query and document vectors. This approach provides more nuanced matching while maintaining fast retrieval speeds.Visit the [Hugging Face embedding integration](https://docs.lancedb.com/integrations/embedding/huggingface) page for info on embedding models.

## Simple Example: ColBERT Embeddings

[ColBERT](https://arxiv.org/abs/2004.12832) is the most well-known late-interaction retrieval model that represents each document and query as multiple token embeddings and scores matches by taking the best token-to-token similarities (MaxSim) across them.Install the dependencies before running this example:

```
import numpy as np

import pyarrow as pa

import lancedb

from pylate import models

# 1) Load a late-interaction model via PyLate

# PyLate docs show ColBERT() + encode(..., is_query=...) :contentReference[oaicite:2]{index=2}

model = models.ColBERT(model_name_or_path="lightonai/GTE-ModernColBERT-v1")

# You can discover dim from one embedding (avoid guessing)

dim = model.encode(["hello"], is_query=True)[0].shape[1]

# 2) Create a LanceDB table with a multivector column

db = lancedb.connect("./pylate_lancedb")

schema = pa.schema([

    pa.field("doc_id", pa.string()),

    pa.field("text", pa.string()),

    # multivector: list<list<float32, dim>> :contentReference[oaicite:3]{index=3}

    pa.field("mv", pa.list_(pa.list_(pa.float32(), dim))),

])

docs = [

    {"doc_id": "1", "text": "The train to Tokyo leaves at 5pm."},

    {"doc_id": "2", "text": "That Pho restaurant in Hanoi is highly rated."},

    {"doc_id": "3", "text": "This is a noodle bar in Osaka, Japan."},

]

# 3) Encode documents with PyLate (token vectors per doc)

doc_texts = [d["text"] for d in docs]

doc_embs = model.encode(doc_texts, is_query=False)  # list/array of (T, dim) per doc :contentReference[oaicite:4]{index=4}

rows = []

for d, emb in zip(docs, doc_embs):

    emb = np.asarray(emb, dtype=np.float32)

    rows.append({**d, "mv": emb.tolist()})

tbl = db.create_table("docs", data=rows, schema=schema, mode="overwrite")

# 4) If your dataset is large, build an index + query using a query matrix

# For small datasets < 100k records, you can skip indexing

# tbl.create_index(vector_column_name="mv", metric="cosine")

query = "Tell me about ramen in Japan"

q_emb = np.asarray(model.encode([query], is_query=True)[0], dtype=np.float32)  # (Tq, dim) :contentReference[oaicite:5]{index=5}

out = tbl.search(q_emb).limit(5).to_pandas()  # multivector search accepts a matrix :contentReference[oaicite:6]{index=6}

print(out[["doc_id", "text"]])
```

Late interaction models implementations evolve rapidly, so it’s recommended to check the latest popular models when trying out multivector search.

## Advanced Example: XTR Embeddings

[ConteXtualized Token Retriever (XTR)](https://arxiv.org/abs/2304.01982) is a late-interaction retrieval model that represents text as token-level vectors instead of a single embedding. This lets search score token-to-token matches (MaxSim), which can improve fine-grained relevance.The notebook linked below shows how to integrate XTR (ConteXtualized Token Retriever), which prioritizes critical document tokens during the initial retrieval stage and removes the gathering stage to significantly improve performance. By focusing on the most semantically salient tokens early in the process, XTR reduces computational complexity with improved recall, ensuring rapid identification of candidate documents.[

## Multivector search with ColPali + XTR embeddings and LanceDB

](https://colab.research.google.com/github/lancedb/vectordb-recipes/blob/main/examples/multivector_xtr/main.ipynb)

[Vector search](https://docs.lancedb.com/search/vector-search) [Full-Text Search (FTS)](https://docs.lancedb.com/search/full-text-search)