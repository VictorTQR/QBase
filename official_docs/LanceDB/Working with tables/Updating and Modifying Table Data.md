---
title: "Updating and Modifying Table Data"
source: "https://docs.lancedb.com/tables/update"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to update, merge, and delete rows in a LanceDB table."
tags:
  - "clippings"
---
Updating or modifying data involves changing rows in an existing table. LanceDB provides two families of write operations that can modify data in a table:
- `update(...)`: mutate existing rows that match a SQL filter.
- `merge_insert(...)`: compare incoming rows to existing rows by key, then choose what to do for each case.
The `update` method is simpler to use when you already know which rows you want to modify and you do not need to compare against an incoming dataset. The `merge_insert` method is more powerful when you have a new dataset that you want to merge into an existing table, and you want LanceDB to handle the logic of comparing against existing rows by key.Let’s look at an example that demonstrates these operations in practice.

## Connect to LanceDB

Connect to your local LanceDB instance:Expected output:Or, connect to your LanceDB remote cluster:Expected output:

## Create the example table

We’ll start by creating a simple table of a table with `id`, `name`, and `login_count` columns. All examples below use the same table.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bob | 20 |

The example above shows a PyArrow schema. You can just as well create the table using other table creation patterns (Pandas, Polars, Pydantic, iterators, etc.) — see the [ingestion](https://docs.lancedb.com/tables/create) guide for more details.

## Choose a write method

## Update rows

Use `update` when you already know which target rows to modify and you do not need to compare against an incoming dataset.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bobby | 20 |

Updating nested columns is not yet supported.

## Update rows with SQL expressions

Use `values_sql` when you want to use SQL-like expressions to update rows. This is useful for operations like incrementing a counter, or setting a column value based on another column.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bob | 21 |

See the [SQL queries](https://docs.lancedb.com/search/sql) page for more information on the supported SQL syntax.

When rows are updated, they are moved out of any existing index. The row will still show up in search queries, but the query will not be as fast as it would be if the row was in the index. If you update a large proportion of rows, consider triggering an index rebuild afterwards.

## Merge incoming rows by key

Merging is different from updating because it involves comparing incoming rows to existing rows by key, and then choosing what to do based on whether the key exists in the target table or not. The `merge_insert(""..."")` method lets you do this.In merge operations, rows are split into three groups:
- **Matched**: key exists in both source and target.
- **Not matched**: key exists only in source.
- **Not matched by source**: key exists only in target.

**Use scalar indexes to speed up merge insert** The merge insert command performs a join between the input data and the target table `on` the key you provide. This requires scanning that entire column, which can be expensive for large tables. To speed up this operation, create a scalar index on the join column, which will allow LanceDB to find matches without scanning the whole table.Read more about scalar indices in the [Scalar Index](https://docs.lancedb.com/indexing/scalar-index) guide.

If you see this HTTP 400 error from `merge_insert`: `Bad request: Merge insert cannot be performed because the number of unindexed rows exceeds the maximum of 10000`. Verify that the scalar index on the join column is up to date before retrying.

Like the create table and add APIs, the merge insert API will automatically compute embeddings based on the [embedding registry](https://docs.lancedb.com/embedding/index#embedding-registry) if the table has an embedding definition in its schema.During `merge_insert`, if the input data doesn’t contain the source column (i.e., the original field used to generate embeddings, such as text for a text embedding model or `image_uri` for an image model), or if a vector value is already provided, LanceDB skips embedding generation for that row. Embeddings are only auto-generated when that source field is present in the incoming data, **and** the vector field is empty.

### Update matched rows only

This updates keys that already exist in the target table. Source rows with new keys are ignored.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bobby | 21 |

### Insert unmatched rows only

This inserts only brand-new keys from the source. Existing keys are left unchanged.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bob | 20 |
| 3 | Charlie | 5 |

### Update matched rows and insert unmatched rows

Use both `when_matched_update_all()` and `when_not_matched_insert_all()` when you want to update existing keys and insert missing keys in one operation.

This is a conventional **upsert**.

Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bobby | 21 |
| 3 | Charlie | 5 |

### Delete target rows that are missing from source

Use `when_not_matched_by_source_delete()` when you want to remove any target row that does not appear in the incoming source data.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 2 | Bobby | 21 |
| 3 | Charlie | 5 |

In the example above, LanceDB matches rows by `id`. Rows with `id=2` and `id=3` exist in both the table and incoming data, so they are updated. Row `id=1` exists only in the target, so it is deleted.

### Use partial columns in merge updates

Merge updates do not require you to provide values for all columns. You can provide only a subset of columns in source rows. For matched rows, only the provided columns are updated.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bobby | 20 |
| 3 | Charlie | null |

Note that in the example above, when `merge_insert` creates a new row, any missing columns are written as `null`. If a missing column is non-nullable in your schema, the insert will fail.

## Delete rows

Delete operations **soft delete** rows that match a given condition. The underlying data is not immediately removed, but is marked for deletion (in the [deletion files](https://lance.org/format/table/#deletion-files) at the Lance format level) and excluded from query results.Expected table contents:

| id | name | login\_count |
| --- | --- | --- |
| 1 | Alice | 10 |
| 2 | Bob | 20 |

**Deleting rows removes them from the index** When rows are deleted, those rows are also excluded from the index segments, so indexed queries will not return them either. If ALL the rows are deleted (i.e., the table is emptied), ensure that you recreate the index after ingesting new data.

To permanently remove deleted rows, you can optimize the table, which will run compaction and cleans up the soft-deleted rows, which frees up storage space.
- In LanceDB OSS, compaction and cleanup are manual. Run `table.optimize()` regularly to free up disk space.
- In LanceDB Cloud, compaction and cleanup runs automatically in the background.
- In LanceDB Enterprise, files aren’t cleaned up by default. You can configure the compaction and cleanup behavior at cluster setup time to suit your organization’s retention policy.
By default, table cleanup removes data up to 7 days ago. If you need to reclaim space from deleted rows more aggressively, manually call `table.optimize()` use a shorter retention window as follows:

[Schema & data evolution](https://docs.lancedb.com/tables/schema) [Namespaces](https://docs.lancedb.com/tables/namespaces)