---
title: "Updating and Modifying Table Data"
source: "https://docs.lancedb.com/tables/update"
author:
  - "[[LanceDB]]"
published:
created: 2026-02-04
description: "Learn how to update and modify data in LanceDB. Includes incremental updates, batch modifications, and best practices for data maintenance."
tags:
  - "clippings"
---
Once you have created a table, there are several ways to modify its data. You can:
- Ingest and add new records to your table;
- Update existing records that match specific conditions;
- Use the powerful Merge Insert function for more complex operations like upserting or replacing ranges of data.
These operations allow you to keep your table data current and maintain it exactly as needed for your use case. Let’s look at each of these operations in detail.

## Connecting to LanceDB

Before performing any operations, you’ll need to connect to LanceDB. The connection method depends on whether you’re using LanceDB Cloud or the open source version.You can also connect locally using LanceDB OSS:

## Data Insertion

### Adding data to a table

Say you created a LanceDB table by passing in a `schema`. This is an *empty* table, with no data in it. To add or append data to a table, you can use the `table.add(data)`, as shown below.

The vector column needs to be a `pyarrow.FixedSizeList` type.

### Using Pydantic Models

Pydantic models provide a more structured way to define your table schema:

### Using Nested Models

You can use nested Pydantic models to represent complex data structures. For example, you may want to store the document string and the document source name as a nested Document object:This can be used as the type of a LanceDB table column:This creates a struct column called `document` that has two subfields called `content` and `source`:

### Batch Data Insertion

It is recommended to use iterators to add large datasets in batches when creating your table in one go. Data will be automatically compacted for the best query performance.

#### Python Batch Insertion

LanceDB Cloud is a multi-tenant environment with a 100MB payload limit. Adjust your batch size accordingly.

## Data Modification

### Update Operations

This can be used to update zero to all rows depending on how many rows match the where clause. The update queries follow the form of a SQL UPDATE statement. The `where` parameter is a SQL filter that matches on the metadata columns. The `values` or `values_sql` parameters are used to provide the new values for the columns.

Updating nested columns is not yet supported.

See the [SQL queries](https://docs.lancedb.com/search/sql) page for more information on the supported SQL syntax.

Output:

### Updating Using SQL

The `values` parameter is used to provide the new values for the columns as literal values. You can also use the `values_sql` / `valuesSql` parameter to provide SQL expressions for the new values. For example, you can use `values_sql="x + 1"` to increment the value of the `x` column by 1.Output:

When rows are updated, they are moved out of the index. The row will still show up in ANN queries, but the query will not be as fast as it would be if the row was in the index. If you update a large proportion of rows, consider rebuilding the index afterwards.

### Delete Operations

Remove rows that match a condition.

Delete operations soft delete rows. Rows are hard deleted later by compaction and cleanup operations that happen in the background on LanceDB Cloud and Enterprise. The default retention on Cloud is 30 days. During this time, these rows are still accessible to query or restore by accessing old table versions (see [Versioning & Reproducibility in LanceDB](https://docs.lancedb.com/tables/versioning)).

If a table is emptied, its existing indexes are removed. Recreate indexes after ingesting new data.

## Merge Operations

The merge insert command is a flexible API that can be used to perform `upsert`,`insert_if_not_exists`, and `replace_range_ operations`.

The merge insert command performs a join between the input data and the target table `on` the key you provide. This requires scanning that entire column, which can be expensive for large tables. To speed up this operation, create a scalar index on the join column, which will allow LanceDB to find matches without scanning the whole table.Read more about scalar indices in the [Scalar Index](https://docs.lancedb.com/indexing/scalar-index) guide.

You may receive an HTTP 400 error from merge insert: `Bad request: Merge insert cannot be performed because the number of unindexed rows exceeds the maximum of 10000`. Verify that the scalar index on the join column is up to date before retrying.

Like the create table and add APIs, the merge insert API will automatically compute embeddings if the table has an embedding definition in its schema. If the input data doesn’t contain the source column, or the vector column is already filled, the embeddings won’t be computed.

### Upsert

`upsert` updates rows if they exist and inserts them if they don’t. To do this with merge insert, enable both `when_matched_update_all()` and `when_not_matched_insert_all()`.

#### Setting Up the Example Table and Performing Upsert

### Insert-if-not-exists

This will only insert rows that do not have a match in the target table, thus preventing duplicate rows. To do this with merge insert, enable just `when_not_matched_insert_all()`.

#### Setting Up the Example Table and Performing Insert-if-not-exists

### Replace Range

You can also replace a range of rows in the target table with the input data. For example, if you have a table of document chunks, where each chunk has both a `doc_id` and a `chunk_id`, you can replace all chunks for a given `doc_id` with updated chunks.This can be tricky otherwise because if you try to use `upsert` when the new data has fewer chunks you will end up with extra chunks. To avoid this, add another clause to delete any chunks for the document that are not in the new data, with `when_not_matched_by_source_delete`.

#### Setting Up the Example Table and Performing Replace Range

```
# Create example table with document chunks

table = db.create_table(

    "chunks",

    [

        {"doc_id": 0, "chunk_id": 0, "text": "Hello"},

        {"doc_id": 0, "chunk_id": 1, "text": "World"},

        {"doc_id": 1, "chunk_id": 0, "text": "Foo"},

        {"doc_id": 1, "chunk_id": 1, "text": "Bar"},

        {"doc_id": 2, "chunk_id": 0, "text": "Baz"},

    ],

    mode="overwrite",

)

# New data - replacing all chunks for doc_id 1 with just one chunk

new_chunks = [

    {"doc_id": 1, "chunk_id": 0, "text": "Zoo"},

]

# Replace all chunks for doc_id 1

(

    table.merge_insert(["doc_id"])

    .when_matched_update_all()

    .when_not_matched_insert_all()

    .when_not_matched_by_source_delete("doc_id = 1")

    .execute(new_chunks)

)

# Verify count for doc_id = 1 - should be 1

print(f"Chunks for doc_id = 1: {table.count_rows('doc_id = 1')}")  # 1
```

We suggest the best batch size to be 500k for optimal performance.

[Schema & data evolution](https://docs.lancedb.com/tables/schema) [Versioning](https://docs.lancedb.com/tables/versioning)