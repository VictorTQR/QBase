---
title: "Quickstart"
source: "https://docs.lancedb.com/quickstart"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Get started with LanceDB in minutes."
tags:
  - "clippings"
---
The easiest way to get started with LanceDB is the open source version, which is an embedded database that runs in-process (like SQLite). Let’s get started in just a few steps!

## 1\. Install LanceDB

Install LanceDB in your client SDK.

## 2\. Connect to a LanceDB database

LanceDB supports several URI patterns to connect to a database.
- A local filesystem path (when using it as an embedded library)
- A `db://...` URI (when using LanceDB Cloud or Enterprise)
- An object storage URI: `s3://...`, `gs://...`, or `az://...` (OSS mode)

### Connect via local path with LanceDB

The simplest way to begin is to use LanceDB OSS. Simply import LanceDB as an embedded library in your client SDK of choice and point to a local path.

### Connect via object storage URIs

You can also connect LanceDB OSS directly to object storage:For credentials, endpoints, and provider-specific options, see [Configuring storage](https://docs.lancedb.com/storage/configuration).

### Connect to LanceDB Enterprise

If you’re using a managed LanceDB service on either LanceDB Cloud or Enterprise, you can connect using a `db://` URI, along with any encessary credentials. Simply replace the local path with a remote `uri` that points to where your data is stored, and you’re ready to go.To learn more about LanceDB Enterprise, see the [Enterprise documentation](https://docs.lancedb.com/enterprise).

## 3\. Obtain data and ingest into LanceDB

Let’s look at an example. We have the following records of characters in an adventure board game. The vector column holds 3-dimensional embeddings representing each character.To ingest the data into LanceDB, obtain data of the required shape and pass in the data object to the `create_table` method as shown below. Note that LanceDB tables require a schema. If you don’t provide one, LanceDB will infer it from the data.

The `vector` arrays here are synthetic and for demonstration purposes only. In your real-world applications, you’d generate these vectors from the raw text fields using a suitable embedding model.

Now, let’s perform a vector similarity search. The query vector should have the same dimensionality as your data vectors and be generated using the same embedding model. The search returns the most similar vectors based on a chosen distance metric (default is L2, or Euclidean distance).Our query is a vector that represents a “warrior”. Let’s find the result that’s most similar to it!The example for Python above shows how to convert results to a Polars DataFrame. Depending on your language, you can collect query results as a list/array of objects or DataFrames to be used downstream in your application.

Use the `to_pandas()` method to convert query results into a Pandas DataFrame.

Python

See the full code for these examples (including helper functions) in the `quickstart` file for the appropriate client language in the [docs repo](https://github.com/lancedb/docs/tree/main/tests).

## What’s next?

You’ve learned how to install LanceDB, connect, create a table, and run a first vector search. In the real world, embeddings capture meaning and vector search allows you to find the most relevant data based on semantic similarity.Note that LanceDB is much more than “just a vector database” — it’s [a multimodal lakehouse](https://lancedb.com/blog/multimodal-lakehouse/). There’s a lot more you can do with it! Continue to the [Table management](https://docs.lancedb.com/tables) guide to build on this example with schema options, appending data, updates, and versioning.As you explore LanceDB further, you can combine vector search with other techniques like filtering based on metadata fields, full-text search, hybrid search, and more. Check out the tutorials and guides below to continue learning.## [Basic table operations](https://docs.lancedb.com/tables)

[

Build on this quickstart with table creation, updates, and schema tips.

](https://docs.lancedb.com/tables)LanceDB Cloud Quickstart

Get started with LanceDB Cloud in minutes.

[View original](https://docs.lancedb.com/cloud/get-started)Build a RAG App

Learn how to build Retrieval-Augmented Generation (RAG) applications using LanceDB.

[View original](https://docs.lancedb.com/tutorials/agents)

[LanceDB](https://docs.lancedb.com/)