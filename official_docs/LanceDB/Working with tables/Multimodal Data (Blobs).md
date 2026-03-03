---
title: "Multimodal Data (Blobs)"
source: "https://docs.lancedb.com/tables/multimodal"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to store and query multimodal data (images, audio, video) directly in LanceDB using binary columns."
tags:
  - "clippings"
---
LanceDB handles multimodal data—images, audio, video, and PDF files—natively by storing the raw bytes in a binary column alongside your vectors and metadata. This approach simplifies your data infrastructure by keeping the raw assets and their embeddings in the same database, eliminating the need for separate object storage for many use cases.This guide demonstrates how to ingest, store, and retrieve image data using standard binary columns, and also introduces the **Lance Blob API** for optimized handling of larger multimodal files.

## Storing binary data

To store binary data, you need to use the `pa.binary()` data type in your Arrow schema. In Python, this corresponds to `bytes` objects if you’re using LanceDB’s Pydantic `LanceModel` to define the schema.

### 1\. Setup and imports

First, let’s import the necessary libraries. We’ll use `PIL` (Pillow) for image handling and `io` for byte conversion.

### 2\. Preparing data

For this example, we’ll create some dummy in-memory images. In a real application, you would read these from files or an API. The key is to convert your data (image, audio, etc.) into a raw `bytes` object.

### 3\. Defining the schema

When creating the table, it is **highly recommended** to define the schema explicitly. This ensures that your binary data is correctly interpreted as a `binary` type by Arrow/LanceDB and not as a generic string or list.

### 4\. Ingesting data

Now, create the table using the data and the defined schema.

## Retrieving and using blobs

When you search your LanceDB table, you can retrieve the binary column just like any other metadata.

### Converting bytes back to objects

Once you have the `bytes` data back from the search result, you can decode it back into its original format (e.g., a PIL Image, an Audio buffer, etc.).

## Large Blobs (Blob API)

For larger files like high-resolution images or videos, Lance provides a specialized **Blob API**. By using `pa.large_binary()` and specific metadata, you enable **lazy loading** and optimized encoding. This allows you to work with massive datasets without loading all binary data into memory upfront.

### 1\. Defining a blob schema

To use the Blob API, you must mark the column with `{"lance-encoding:blob": "true"}` metadata.

### 2\. Ingesting large blobs

You can then ingest data normally, and Lance will handle the optimized storage.

For more advanced usage, including random access and file-like reading of blobs, see the Lance format’s [blob API documentation](https://lance.org/guide/blob/).

The `pa.binary()` and `pa.large_binary()` types are universal. You can use this same pattern for other types of multimodal data:
- **Audio:** Read `.wav` or `.mp3` files as bytes.
- **Video:** Store video transitions or full clips using the Blob API.
- **PDFs/Documents:** Store the raw file content for document search.

[Ingesting data](https://docs.lancedb.com/tables/create) [Schema & data evolution](https://docs.lancedb.com/tables/schema)