---
title: "Upsert Documents | Zvec"
source: "https://zvec.org/en/docs/data-operations/upsert/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/)

## Upsert Documents

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.upsert) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#upsertsync)

`upsert()` works similar to `insert()` — it adds one or more new [documents](https://zvec.org/en/docs/concepts/data-modeling/#documents) (`Doc`) to a [collection](https://zvec.org/en/docs/collections/).

The key difference is that if a document with the same `id` already exists, it will be **overwritten**.

---

## Document Doc

Each `Doc` passed to `upsert()` must:

- Have an `id` (if a document with the same `id` already exists, it will be replaced)
- Provide data that matches the collection's [schema](https://zvec.org/en/docs/collections/create/#define-a-collection-schema):
	1. **Scalar fields**: provided as key–value pairs under `fields` (scalar field names as keys)
	2. **Vector embeddings**: provided as key–value pairs under `vectors` (vector names as keys)
- You can omit `nullable` scalar fields if a document doesn't have a value for them

---

## Upsert a Single Document

Assume you already have a collection with the following schema:

- A scalar field: `text` (string)
- A [dense vector embedding](https://zvec.org/en/docs/concepts/vector-embedding/#dense-vectors): `text_embedding` (4-dimensional FP32 vector)

You've also opened the collection and have a `collection` object ready.

Now, upsert a document like this:

Upsert a document

```
import zvec

# Create a document

doc = zvec.Doc(  

    id="text_1",  # ← must be unique

    vectors={

        "text_embedding": [0.1, 0.2, 0.3, 0.4],  # ← must match the vector name

                          # ↑ list of floats; list length = dimension (4)

    },

    fields={

        "text": "This is a sample text.",  # ← must match the scalar field name

    },

)

# Upsert the document

result = collection.upsert(doc)  

print(result)  # {"code": 0} means success
```

The `upsert()` method validates the document first:

- **Incorrect usage** — such as an unknown field or wrong vector dimension — **raises an exception**.
- **If validation passes**, the method proceeds with the upsertion and returns a `Status` object:
	- `{"code": 0}` indicates success.
	- Non-zero codes indicate failure (e.g., insufficient disk space).

Successfully upserted documents are immediately available for querying 🚀.

Upsert a document

```
import { ZVecCollection, ZVecDocInput, ZVecOpen } from "@zvec/zvec";

// Create a document

let doc: ZVecDocInput = { 

    id: "text_1",   // ← must be unique

    vectors: {

        "text_embedding": [0.1, 0.2, 0.3, 0.4]  // ← must match the vector name

                          // ↑ list of floats; list length = dimension (4)

    },

    fields: {

        "text": "This is a sample text."    // ← must match the scalar field name

    }

};

// Upsert the document

let result = collection.upsertSync(doc);  

console.log(result);  // { ok: true } means success
```

The `upsert()` method validates the document first:

- **Incorrect usage** — such as an unknown field or wrong vector dimension — **raises an exception**.
- **If validation passes**, the method proceeds with the upsertion and returns a `Status` object:
	- `{ ok: true }` indicates success.
	- `{ ok: false }` indicates failure (e.g., insufficient disk space).

Successfully upserted documents are immediately available for querying 🚀.

---

## Upsert a Batch of Documents

To upsert multiple documents at once, pass a list of `Doc` objects to `upsert()`.  
Each `Doc` is processed independently, and the method returns a list of `Status` objects — one per document.

Upsert a batch of documents

```
import zvec

result = collection.upsert(  

    [

        zvec.Doc(

            id="text_1",

            vectors={"text_embedding": [0.1, 0.2, 0.3, 0.4]},

            fields={"text": "This is a sample text."},

        ),

        zvec.Doc(

            id="text_2",

            vectors={"text_embedding": [0.4, 0.3, 0.2, 0.1]},

            fields={"text": "This is another sample text."},

        ),

        zvec.Doc(

            id="text_3",

            vectors={"text_embedding": [-0.1, -0.2, -0.3, -0.4]},

            fields={"text": "One more sample text."},

        ),

    ]

)

print(result)  # [{"code":0}, {"code":0}, {"code":0}]
```

If any document in the batch has incorrect usage (e.g., an unknown field or wrong vector dimension), the method raises an exception and **no documents are upserted**.

If all documents are valid, the method attempts to upsert every one. A failure in one (e.g., insufficient disk space) does **not** stop others from being upserted.

🔍 **Always check each `Status` in the result list.**

---

## Upsert Documents with Sparse Vectors

Assume your collection includes a [sparse vector](https://zvec.org/en/docs/concepts/vector-embedding/#sparse-vectors) named `sparse_embedding`.

Upsert a document with a sparse vector like this:

Upsert a document with a sparse vector

```
import zvec

result = collection.upsert(  

    zvec.Doc(

        id="text_1",

        vectors={

            "sparse_embedding": {

                42: 1.25,  # ← dimension 42 has weight 1.25

                1337: 0.8,  # ← dimension 1337 has weight 0.8

                2999: 0.63,  # ← dimension 2999 has weight 0.63

            }

        },

    )

)

print(result)  # {"code":0}
```

---

## Upsert Documents with Multiple Fields and Vectors

Real-world applications often require collections with multiple scalar fields and vector embeddings. In this example, assume your collection includes the following schema:

- **Scalar fields**:
	1. `book_title` (string)
	2. `category` (array of strings)
	3. `publish_year` (32-bit integer)
- **Vector embeddings**:
	1. `dense_embedding`: a 768-dimensional dense vector
	2. `sparse_embedding`: a sparse vector

Upsert a document with multiple fields and vectors like this:

Upsert a document with multiple fields and vectors

```
import zvec

# Create a document

doc = zvec.Doc(  

    id="book_1",

    vectors={

        "dense_embedding": [0.1 for _ in range(768)],  # ← use real embedding in practice

        "sparse_embedding": {42: 1.25, 1337: 0.8, 1999: 0.64},  # ← use real embedding in practice

    },

    fields={

        "book_title": "Gone with the Wind",  # ← string

        "category": ["Romance", "Classic Literature"],  # ← array of strings

        "publish_year": 1936,  # ← integer

    },

)

# Upsert the document

result = collection.upsert(doc)  

print(result)  # {"code": 0} means success
```

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)

### On this page

[Document `Doc`](https://zvec.org/en/docs/data-operations/upsert/#document-doc) [Upsert a Single Document](https://zvec.org/en/docs/data-operations/upsert/#upsert-a-single-document) [Upsert a Batch of Documents](https://zvec.org/en/docs/data-operations/upsert/#upsert-a-batch-of-documents) [Upsert Documents with Sparse Vectors](https://zvec.org/en/docs/data-operations/upsert/#upsert-documents-with-sparse-vectors) [Upsert Documents with Multiple Fields and Vectors](https://zvec.org/en/docs/data-operations/upsert/#upsert-documents-with-multiple-fields-and-vectors)