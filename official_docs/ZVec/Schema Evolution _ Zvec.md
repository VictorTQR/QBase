---
title: "Schema Evolution | Zvec"
source: "https://zvec.org/en/docs/collections/schema-evolution/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Collections](https://zvec.org/en/docs/collections/)

## Schema Evolution

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection)

Zvec supports **dynamic schema evolution**, allowing you to modify a collection's structure after it has been created — without downtime, data re-ingestion, or reindexing.

You can:

- ✅ **Add or drop scalar fields**
- ✅ **Rename fields** or **change their data types** ((as long as the change is safe — e.g., from `INT32` to `INT64`)
- ✅ **Create or drop indexes on fields**
- ❌ Add or drop vector fields (🔜 coming soon)

---

## Data Definition Language (DDL)

In Zvec, schema changes are performed using **Data Definition Language (DDL)** methods, grouped into two categories:

- **Column DDL**: defines *what data you store*.  
	It manages the structure of your collection by [adding](https://zvec.org/en/docs/collections/schema-evolution/#add-a-column), [removing](https://zvec.org/en/docs/collections/schema-evolution/#drop-a-column), [renaming or altering](https://zvec.org/en/docs/collections/schema-evolution/#alter-a-column) fields.
- **Index DDL**: defines *how you search that data*.  
	It controls the [creation](https://zvec.org/en/docs/collections/schema-evolution/#create-an-index) and [removal](https://zvec.org/en/docs/collections/schema-evolution/#drop-an-index) of indexes on fields.

💡 **Indexing Rules in Zvec**

- **Every vector field must be indexed** using an appropriate [vector index](https://zvec.org/en/docs/concepts/vector-index/) to enable similarity search.
- **Scalar fields are optionally indexed** — but you should build [inverted indexes](https://zvec.org/en/docs/concepts/inverted-index/) on any scalar field you plan to use in filtering queries (e.g., `WHERE category = 'music'`).

---

## Prerequisites

This guide assumes you have opened a collection and have a `collection` object ready.

---

## Column DDL

### Add a Column

To add a new scalar field to an existing collection, use `add_column()`:

Add a column

```
import zvec

new_field = zvec.FieldSchema(name="rating", data_type=zvec.DataType.INT32)

collection.add_column(field_schema=new_field, expression="5")
```

- `field_schema`:  
	Defines the name and data type of the new field. See [scalar field schema](https://zvec.org/en/docs/collections/create/#scalar-fields) for details.
- `expression`:  
	Specifies the default value for existing documents. Since they don't already have a `rating` field, Zvec uses this `expression` to fill in the missing values — in this case, setting `rating = 5` for all current documents.

Currently, only **numerical scalar fields** can be added via `add_column()`. Support for `string` and `boolean` types is coming soon.  
Accordingly, the `expression` must evaluate to a number — it can be a single numerical literal (like `"5"`) or a simple arithmetic expression involving existing numerical fields (e.g., `"publish_year + 1"`).

### Drop a Column

To permanently remove a scalar field, use `drop_column()`:

Drop a column

```
collection.drop_column(field_name="publish_year")
```

### Alter a Column

To rename a column or update its schema, use `alter_column()`:

Alter a column

```
# Rename

collection.alter_column(old_name="publish_year", new_name="release_year")   

# Change type (if compatible)

updated = zvec.FieldSchema(name="rating", data_type=zvec.DataType.FLOAT)

collection.alter_column(field_schema=updated)
```

### View the Current Schema

After making changes, you can always check your collection's current structure by printing its schema:

View the current schema

```
print(collection.schema)
```

See [schema example](https://zvec.org/en/docs/collections/inspect/#collection-schema) for more details.

## Index DDL

### Create an Index

To accelerate search performance, you can create (or replace) indexes on both **vector** and **scalar** fields using `create_index()`:

Create an index

```
import zvec

# Replace the existing HNSW index with a FLAT index

collection.create_index(  

    field_name="dense_embedding",

    index_param=zvec.FlatIndexParam(metric_type=zvec.MetricType.COSINE),

)

# Create an inverted index

collection.create_index(  

    field_name="publish_year",

    index_param=zvec.InvertIndexParam(),

)
```

- **Vector fields** must use one of the following index types:
	- [`HnswIndexParam`](https://zvec.org/en/docs/concepts/vector-index/hnsw-index/#index-time-parameters)
	- [`IVFIndexParam`](https://zvec.org/en/docs/concepts/vector-index/ivf-index/#index-time-parameters)
	- `FlatIndexParam`
- **Scalar fields** use `InvertIndexParam` to enable efficient filtering.

### Drop an Index

To remove an index from a scalar field, use `drop_index()`:

Drop an index

```
collection.drop_index(field_name="publish_year")
```

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Optimize](https://zvec.org/en/docs/collections/optimize/)

[

Previous Page

](https://zvec.org/en/docs/collections/optimize/)[

Data Operations

Next Page

](https://zvec.org/en/docs/data-operations/)