---
title: "Basic Table Operations"
source: "https://docs.lancedb.com/tables"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Create tables, search vectors, and append data in LanceDB."
tags:
  - "clippings"
---
Now that you’ve completed the [LanceDB quickstart](https://docs.lancedb.com/quickstart), you’re ready to explore some more table operations you’ll typically need when working with LanceDB.
- **Ingest data into tables** from JSON data (and in Python, Pandas or Polars DataFrames)
- **Create empty tables** by defining explicit Arrow schemas
- **Vector similarity search** with filtering and projections
- **Filtered queries** that can operate on nested structs
- **Interoperate with DuckDB** and run traditional SQL queries on an Arrow table (Python)

This page uses **synchronous** Python snippets. If your Python app uses `asyncio`, the same flow works with `connect_async(...)` and `await` -based table/query calls. Use the example below as a template, and see [Quickstart](https://docs.lancedb.com/quickstart#python-sync-and-async-apis) for example snippets on both sync and async Python usage.

## Dataset

We’ll work with this small dataset based on characters from the legends of Camelot. Note that the `vector` column holds 4-dimensional embeddings, and the `stats` column is a nested struct with several integer fields, indicating each character’s attributes.

camelot.json

```
[

  {

    "id": 1,

    "name": "King Arthur",

    "role": "King of Camelot",

    "description": "The legendary ruler of Camelot, wielder of Excalibur, and leader of the Knights of the Round Table.",

    "vector": [0.72, -0.28, 0.60, 0.86],

    "stats": { "strength": 2, "courage": 5, "magic": 1, "wisdom": 4 }

  },

  {

    "id": 2,

    "name": "Merlin",

    "role": "Wizard and Advisor",

    "description": "A powerful wizard and prophet who mentors Arthur and shapes the destiny of Camelot through magic and foresight.",

    "vector": [0.05, 0.88, 0.62, 0.85],

    "stats": { "strength": 2, "courage": 4, "magic": 5, "wisdom": 5 }

  },

  {

    "id": 3,

    "name": "Queen Guinevere",

    "role": "Queen of Camelot",

    "description": "Arthur's queen, admired for her grace and diplomacy, whose romances and loyalties influence Camelot's fate.",

    "vector": [0.22, -0.22, 0.42, 0.82],

    "stats": { "strength": 1, "courage": 3, "magic": 1, "wisdom": 4 }

  },

  {

    "id": 4,

    "name": "Sir Lancelot",

    "role": "Knight of the Round Table",

    "description": "Arthur's most skilled knight, famed for unmatched combat prowess and his tragic love for Queen Guinevere.",

    "vector": [0.86, -0.35, 0.38, 0.55],

    "stats": { "strength": 5, "courage": 5, "magic": 1, "wisdom": 3 }

  },

  {

    "id": 5,

    "name": "Sir Gawain",

    "role": "Knight of the Round Table",

    "description": "A noble and honorable knight known for his courtesy and his encounter with the Green Knight.",

    "vector": [0.82, -0.32, 0.52, 0.60],

    "stats": { "strength": 4, "courage": 5, "magic": 1, "wisdom": 4 }

  },

  {

    "id": 6,

    "name": "Sir Galahad",

    "role": "Knight of the Round Table",

    "description": "The purest and most virtuous knight, chosen to achieve the Holy Grail due to his unwavering spiritual purity.",

    "vector": [0.80, -0.20, 0.70, 0.78],

    "stats": { "strength": 4, "courage": 5, "magic": 2, "wisdom": 5 }

  },

  {

    "id": 7,

    "name": "Sir Percival",

    "role": "Knight of the Round Table",

    "description": "A loyal and innocent knight whose bravery and sincerity make him one of the key seekers of the Holy Grail.",

    "vector": [0.78, -0.36, 0.48, 0.52],

    "stats": { "strength": 4, "courage": 4, "magic": 1, "wisdom": 3 }

  },

  {

    "id": 8,

    "name": "Mordred",

    "role": "Traitor Knight",

    "description": "Arthur's treacherous son or nephew who ultimately rebels against him, leading to Camelot's downfall.",

    "vector": [0.68, -0.30, -0.65, 0.20],

    "stats": { "strength": 4, "courage": 2, "magic": 1, "wisdom": 2 }

  }

]
```

The `vector` arrays here are synthetic and for demonstration purposes only. In your real-world applications, you’d generate these vectors from the raw text fields using a suitable embedding model.

## Connect to a database

### Option 1: Local database

We start by connecting to a LanceDB database path. The example below uses a local path in LanceDB OSS.

### Option 2: Remote database

You can also connect LanceDB OSS directly to object storage. For credentials, endpoints, and provider-specific options, see [Configuring storage](https://docs.lancedb.com/storage/configuration).If you’re using a managed LanceDB service on either LanceDB Cloud or Enterprise, you can connect using a `db://` URI, along with any encessary credentials. Simply replace the local path with a remote `uri` that points to where your data is stored, and you’re ready to go.To learn more about LanceDB Enterprise, see the [Enterprise documentation](https://docs.lancedb.com/enterprise).

- When you connect to a remote URI (Cloud/Enterprise), `open_table(...)` returns a *remote* table. Remote tables support core operations (ingest, search, update, delete), but some convenience methods for bulk data export are not available.
- In the Python SDK, `table.to_arrow()` and `table.to_pandas()` are not implemented for remote tables. To retrieve data, use search queries instead: `table.search(query).limit(n).to_arrow()`.

## Create a table and ingest data

### From JSON

LanceDB stores records in Lance tables. Each row is a record and each column holds a field or related metadata. The simplest way to start is to obtain the source data as a list of JSON records that includes a vector column and any metadata fields you care about.Load the data from the JSON file:You can now create a LanceDB table from the loaded data. Use the `mode="overwrite"` to replace any existing table with the same name and overwrite its data (useful during initial testing).

If you want to avoid overwriting an existing table, omit the overwrite mode.

### From Pandas DataFrames

Python Only You can create LanceDB tables directly from [Pandas](https://pandas.pydata.org/) DataFrames. Simply obtain the source data as a Pandas DataFrame, then create the table and directly ingest to it.

### From Polars DataFrames

Python Only You can also create LanceDB tables directly from [Polars](https://www.pola.rs/) DataFrames. Simply obtain the source data as a Polars DataFrame, then create the table and directly ingest to it.

### From an Arrow schema

If you want to create an *empty* table without any data — say you want to define the schema first and then incrementally add data later — you can do so by defining an Arrow schema explicitly.Once the empty table is defined, LanceDB is ready to accept new data via the `add` method, as shown in the next section.

## Display table schema

LanceDB tables are type-aware, leveraging Apache Arrow under the hood. You can display a given table’s schema using the `schema` property or method. For example, in Python, running `print(table.schema)` would show something like the following:

## Append data to a table

LanceDB tables are mutable, and you can append new records to existing tables. If you’re starting with a fresh session, connect to the database and open the existing table named `camelot`.Prepare the new records to add. Here, we add two new magical characters via the `add` method.We now have two new records in the table. Let’s begin to query our data!It’s straightforward to run vector similarity search in LanceDB. Let’s answer some questions about the data using vector search with projections (returning only the desired columns).

> Q1: *Who are the characters similar to “wizard”?*

We have Merlin, The Lady of the Lake, and Morgan le Fay in the top results, who all have magical abilities.Next, let’s try to answer a different question that involves vector search while filtering on a nested struct field. Filtering is done using the `where` method, into which you can pass SQL-like expressions.

> Q2: *Who are the characters similar to “wizard” with high magic stats?*

Only three characters have magical abilities greater than 3. Merlin is clearly the most magical of them all!You can also run traditional analytics-style search queries that do not involve vectors. For example, let’s find the strongest characters in the dataset. In the query below, we leave the `search` method empty to indicate that we don’t want to use any vector for similarity search (in TypeScript/Rust, use `query()` instead), and use the `where` method to filter on the `strength` field.

> Q3: *Who are the strongest characters?*

Clearly, the strongest characters are all Knights of the Round Table!

## SQL queries using DuckDB

Python Only You can leverage a full SQL engine like DuckDB to run more complex queries that involve sorting, aggregations, joins, etc. To do this, you convert the LanceDB tables to an Arrow table, which can be natively queried by DuckDB.

This workflow applies to local (embedded) tables only. In the Python SDK, remote tables (Cloud/Enterprise) do not support `to_arrow()` or `to_pandas()`. To retrieve data from remote tables, use search queries with `.to_arrow()` on the results.

Under the hood, Lance tables are Arrow-based, leveraging Arrow’s type system. This is why it’s trivial to query a Lance table using DuckDB, which also natively supports Arrow tables.

## Add column

We can also add new columns to an existing LanceDB table using the `add_columns` method. For this example, let’s add a new float column named `power` that shows the average of each character’s strength, courage, magic, and wisdom stats.The example above sums up the individual stats and divides by 4 to compute the average. The resulting average total stats is cast to an Arrow float type under the hood for the Lance table.We can display the results of this column in descending order of power.

> Q4: *Who are the most powerful characters?*

Note that LanceDB’s `where` only filters rows, but doesn’t sort them by applying an `ORDER BY` clause that you may be used to when working with SQL databases.You can also sort the results after converting them to a Polars DataFrame. In TypeScript/Rust, you can sort the returned array in application code.

Python

Merlin and Sir Galahad are the most powerful characters when considering the average of all their abilities! Sir Lancelot and the Lady of the Lake follow closely behind.

## Delete data

You can delete rows from a LanceDB table using the `delete` method with a filtering expression.Say we want to remove Mordred, the traitor knight, from our table.This will delete the row(s) where the `role` value matches “Traitor Knight”. You can verify that the row has been deleted by running a search query again, and confirming that Mordred no longer appears in the results.

## Drop column

If you want to remove or delete a column from an existing LanceDB table, you can use the `drop_columns` method.

```
table.drop_columns(["power"])
```

This will remove the `power` column we added earlier from the table schema.

## Drop table

If you want to delete an entire table from the database, you can use the `drop_table` method.

```
db.drop_table("camelot")
```

This will delete the `camelot` table from the connected LanceDB database.

See the full code for these examples (including helper functions) in the `basic_usage` file for the appropriate client language in the [docs repo](https://github.com/lancedb/docs/tree/main/tests).

## What about vector indexes?

LanceDB supports vector indexes to speed up similarity search on large datasets. For datasets up to a few hundred thousand vectors, LanceDB’s highly efficient kNN (brute-force) retrieval of nearest neighbors is often sufficient. As your dataset grows larger, you can create vector indexes on your vector columns to accelerate search. See the [indexing](https://docs.lancedb.com/indexing) documentation for details on how to create and use vector indexes in LanceDB.

## What’s next?

Now that you’ve learned the basics of creating tables, adding data, running vector search, and modifying table schemas, you’re ready to explore more advanced features of LanceDB. Below are some suggested next pages.## [Ingesting data](https://docs.lancedb.com/tables/create)

[

Learn the different approaches to creating and ingesting data into LanceDB tables from various sources.

](https://docs.lancedb.com/tables/create)Update and modify tables

Learn how to update and modify existing LanceDB tables and their data.

[View original](https://docs.lancedb.com/tables/update)Schema & data evolution

Understand how to evolve your table schemas and data over time with LanceDB.

[View original](https://docs.lancedb.com/tables/schema)Versioning and time travel

Explore LanceDB’s built-in table versioning and time travel capabilities.

[View original](https://docs.lancedb.com/tables/versioning)

[Get started](https://docs.lancedb.com/cloud/get-started) [Ingesting data](https://docs.lancedb.com/tables/create)