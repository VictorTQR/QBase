---
title: "Ingesting Data"
source: "https://docs.lancedb.com/tables/create"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn about different methods to ingest data into tables in LanceDB, including from various data sources and empty tables."
tags:
  - "clippings"
---
In LanceDB, tables store records with a defined schema that specifies column names and types. You can create LanceDB tables from these data formats:
- Pandas DataFrames
- [Polars](https://pola.rs/) DataFrames
- Apache Arrow Tables
The Python SDK additionally supports:
- PyArrow schemas for explicit schema control
- `LanceModel` for Pydantic-based validation

## Create a LanceDB Table

Initialize a LanceDB connection and create a table LanceDB allows ingesting data from various sources - `dict`, `list[dict]`, `pd.DataFrame`, `pa.Table` or a `Iterator[pa.RecordBatch]`. Let’s take a look at some of the these.

### From list of tuples or dictionaries

### From a Pandas DataFrame

Data is converted to Arrow before being written to disk. For maximum control over how data is saved, either provide the PyArrow schema to convert to or else provide a PyArrow Table directly.

The **`vector`** column needs to be a [Vector](https://docs.lancedb.com/integrations/data/pydantic#vector-field) (defined as [pyarrow.FixedSizeList](https://arrow.apache.org/docs/python/generated/pyarrow.list_.html)) type.

#### From a custom schema

### From a Polars DataFrame

LanceDB supports [Polars](https://pola.rs/), a modern, fast DataFrame library written in Rust. Just like in Pandas, the Polars integration is enabled by PyArrow under the hood. A deeper integration between LanceDB Tables and Polars DataFrames is on the way.

### From an Arrow Table

You can also create LanceDB tables directly from Arrow tables. LanceDB supports float16 data type!

### From Pydantic Models

When you create an empty table without data, you must specify the table schema. LanceDB supports creating tables by specifying a PyArrow schema or a specialized Pydantic model called `LanceModel`.For example, the following Content model specifies a table with 5 columns:`movie_id`, `vector`, `genres`, `title`, and `imdb_id`. When you create a table, you can pass the class as the value of the `schema` parameter to `create_table`. The `vector` column is a `Vector` type, which is a specialized Pydantic type that can be configured with the vector dimensions. It is also important to note that LanceDB only understands subclasses of `lancedb.pydantic.LanceModel` (which itself derives from `pydantic.BaseModel`).

#### Nested schemas

Sometimes your data model may contain nested objects. For example, you may want to store the document string and the document source name as a nested Document object:This can be used as the type of a LanceDB table column:This creates a struct column called “document” that has two subfields called “content” and “source”:

#### Validators

Because `LanceModel` inherits from Pydantic’s `BaseModel`, you can combine them with Pydantic’s [field validators](https://docs.pydantic.dev/latest/concepts/validators). The example below shows how to add a validator to ensure that only valid timezone-aware datetime objects are used for a `created_at` field.When you run this code it, should raise the `ValidationError`.

### Using Iterators / Writing Large Datasets

It is recommended to use iterators to add large datasets in batches when creating your table in one go. This does not create multiple versions of your dataset unlike manually adding batches using `table.add()` LanceDB additionally supports PyArrow’s `RecordBatch` Iterators or other generators producing supported data types.Here’s an example using using `RecordBatch` iterator for creating tables.You can also use iterators of other types like Pandas DataFrame or Pylists directly in the above example.

## Open existing tables

If you forget the name of your table, you can always get a listing of all table names.

## Creating empty table

You can create an empty table for scenarios where you want to add data to the table later. An example would be when you want to collect data from a stream/external file and then add it to a table in batches.An empty table can be initialized via a PyArrow schema.Alternatively, you can also use Pydantic to specify the schema for the empty table. Note that we do not directly import `pydantic` but instead use `lancedb.pydantic` which is a subclass of `pydantic.BaseModel` that has been extended to support LanceDB specific types like `Vector`.Once the empty table has been created, you can append to it or modify its contents, as explained in the [updating and modifying tables](https://docs.lancedb.com/tables/update) section.

## Drop a table

Use the `drop_table()` method on the database to remove a table.This permanently removes the table and is not recoverable, unlike deleting rows. By default, if the table does not exist an exception is raised. To suppress this, you can pass in `ignore_missing=True`.

[Basic usage](https://docs.lancedb.com/tables) [Working with multimodal data](https://docs.lancedb.com/tables/multimodal)