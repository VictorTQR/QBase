---
title: "Create a New Collection | Zvec"
source: "https://zvec.org/en/docs/collections/create/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Collections](https://zvec.org/en/docs/collections/)

## Create a New Collection

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.create_and_open) [Node.js API Reference](https://zvec.org/api-reference/nodejs/functions/ZVecCreateAndOpen)

To create a new, empty collection in Zvec, you need to define the following:

- **Schema** — the structural blueprint of your data, specifying scalar fields and vector embeddings.
- **Collection options** (optional) — runtime settings that control how the collection behaves when opened (e.g., read-only mode).

Once defined, you call `create_and_open()` to create the collection on disk and get a ready-to-use `Collection` handle.

---

## Define a Collection Schema

A **collection schema** `CollectionSchema` defines the structure that every [document](https://zvec.org/en/docs/concepts/data-modeling/#documents) inserted into the collection must conform to.

`CollectionSchema` has three parts:

1. `name`: An identifier for the collection.
2. `fields`: A list of scalar fields.
3. `vectors`: A list of vector fields.

[Python API Reference](https://zvec.org/api-reference/python/schema/#zvec.model.schema.CollectionSchema) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollectionSchema)

### Collection Name

A human-readable identifier for your collection. This name is used internally for reference and logging.

### Scalar Fields

Scalar fields store non-vector (i.e., structured) data — such as strings, numbers, booleans, or arrays.

Each field is defined using `FieldSchema` with the following properties:

1. 🔤 `name`: A unique string identifier for the field within the collection.
2. 🧬 [`data_type`](https://zvec.org/en/docs/concepts/data-modeling/#scalar-types): The type of data stored — e.g., `STRING`, `INT64`, or array types like `ARRAY_STRING`.
3. ⭕ `nullable` (optional): Whether the field is allowed to **have no value** (defaults to `False`).
4. 🚀 `index_param` (optional): Enables fast filtering by creating an [inverted index](https://zvec.org/en/docs/concepts/inverted-index/) via `InvertIndexParam`.

[Python API Reference](https://zvec.org/api-reference/python/schema/#zvec.model.schema.FieldSchema) [Node.js API Reference](https://zvec.org/api-reference/nodejs/interfaces/ZVecFieldSchema)

### Vectors (Embeddings)

A vector is defined using `VectorSchema` with the following properties:

1. 🔤 `name`: A unique string identifier for the vector within the collection.
2. 🧬 [`data_type`](https://zvec.org/en/docs/concepts/data-modeling/#vector-types): The numeric format of the vector.
	- [Dense vectors](https://zvec.org/en/docs/concepts/vector-embedding/#dense-vectors): `VECTOR_FP32`, `VECTOR_FP16`, etc.
	- [Sparse vectors](https://zvec.org/en/docs/concepts/vector-embedding/#sparse-vectors): `SPARSE_VECTOR_FP32`, `SPARSE_VECTOR_FP16`.
3. 📐 `dimension`: Required for dense vectors — the number of dimensions.
4. 🚀 `index_param`: Configures the vector index type and similarity metric.

[Python API Reference](https://zvec.org/api-reference/python/schema/#zvec.model.schema.VectorSchema) [Node.js API Reference](https://zvec.org/api-reference/nodejs/interfaces/ZVecVectorSchema)

#### Choosing Vector Index Type

The `index_param` allows you to configure the appropriate indexing strategy:

- `metric_type`:  
	`COSINE`, `L2`, or `IP` (inner product) — *Ensure your metric matches how your embeddings were trained!*
- [`quantize_type`](https://zvec.org/en/docs/concepts/vector-index/quantization/) (optional):  
	Compress vectors to reduce index size and speed up search (with slight [recall](https://zvec.org/en/docs/concepts/vector-index/#recall-measuring-approximation-quality) trade-off)

### Full Schema Example

---

## Configure Collection Options

The `CollectionOption` lets you control runtime behavior when creating the collection:

- `read_only`: Opens the collection in read-only mode. Attempts to write will raise an error.
- `enable_mmap`: Uses memory-mapped I/O for faster access (default to `True`). This trades slightly higher memory cache usage for improved performance.

Collection option

```
import zvec

collection_option = zvec.CollectionOption(read_only=False, enable_mmap=True)
```

---

## Create and Open a Collection

With your schema and options ready, call `create_and_open()` to create the collection at the desired `path`:

Create and open a collection

```
import zvec

collection = zvec.create_and_open(  

    path="/path/to/my/collection",

    schema=collection_schema,

    option=collection_option,

)
```

The returned `collection` object is immediately ready for inserting documents, running queries, or managing data.

---

## Real-World Example: 🛒 Product Search

This schema models a **multi-modal product search system**, combining visual, textual, and structured metadata for rich retrieval:

### 🗂️ Scalar Fields: For Filtering & Display

- `category` (array of strings, indexed):  
	Enables queries like `category CONTAIN_ANY ("electronics", "headphones")` to find products that belong to either "electronics" or "headphones" (or both).
- `price` (integer, indexed with range optimization):  
	Supports fast range queries such as `price > 100`.
- `in_stock` (boolean, indexed):  
	Enables instant filtering by availability (e.g., "only show items in stock").
- `image_url` and `description` are stored but **not indexed**, since they're only used for display.

### 📐 Vector Embeddings: For Semantic Relevance

- Two dense vectors capture semantic meaning:
	- `image_vec`: 512-dimensional embeddings from product images (e.g., via a vision model).
	- `description_vec`: 768-dimensional embeddings from product descriptions (e.g., from a language model), stored with quantization.
- One sparse vector `keywords_sparse` for keyword matching, enabling hybrid sparse-dense search.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)

### On this page

[Define a Collection Schema](https://zvec.org/en/docs/collections/create/#define-a-collection-schema) [Collection Name](https://zvec.org/en/docs/collections/create/#collection-name) [Scalar Fields](https://zvec.org/en/docs/collections/create/#scalar-fields) [Vectors (Embeddings)](https://zvec.org/en/docs/collections/create/#vectors-embeddings) [Choosing Vector Index Type](https://zvec.org/en/docs/collections/create/#choosing-vector-index-type) [Full Schema Example](https://zvec.org/en/docs/collections/create/#full-schema-example) [Configure Collection Options](https://zvec.org/en/docs/collections/create/#configure-collection-options) [Create and Open a Collection](https://zvec.org/en/docs/collections/create/#create-and-open-a-collection) [Real-World Example: 🛒 Product Search](https://zvec.org/en/docs/collections/create/#real-world-example--product-search) [🗂️ Scalar Fields: For Filtering & Display](https://zvec.org/en/docs/collections/create/#%EF%B8%8F-scalar-fields-for-filtering--display) [📐 Vector Embeddings: For Semantic Relevance](https://zvec.org/en/docs/collections/create/#-vector-embeddings-for-semantic-relevance)