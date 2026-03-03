---
title: "Update Documents | Zvec"
source: "https://zvec.org/en/docs/data-operations/update/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/)

## Update Documents

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.update) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#updatesync)

Use `update()` to modify **existing** [documents](https://zvec.org/en/docs/concepts/data-modeling/#documents) (`Doc`).

Only the scalar fields and vector embeddings you **include will be updated**; all other content remains unchanged.

The method accepts either a single `Doc` object or a list of `Doc` objects.

---

## Document Doc

Each `Doc` passed to `update()` must:

- Specify an `id` that **already exists** in the collection (the operation will fail if the document is not found)
- Include only the fields and vectors you **intend to update**, formatted according to the collection's [schema](https://zvec.org/en/docs/collections/create/#define-a-collection-schema):
	1. **Scalar fields**: provided as key–value pairs under `fields` (scalar field names as keys)
	2. **Vector embeddings**: provided as key–value pairs under `vectors` (vector names as keys)
- Omit any scalar fields or vectors you do not want to change — they will be left untouched.

---

## Update a Single Document

Assume you already have a collection with the following schema:

- **Scalar fields**:
	1. `book_title` (string)
	2. `category` (array of strings)
	3. `publish_year` (32-bit integer)
- **Vector embeddings**:
	1. `dense_embedding`: a 768-dimensional dense vector
	2. `sparse_embedding`: a sparse vector

To update an existing document, provide its `id` and only the fields or vectors you want to change:

Update a document

```
import zvec

doc = zvec.Doc(  

    id="book_1",  # ← must already exist in the collection

    vectors={

        "sparse_embedding": {  # ← replaces entire sparse vector

            35: 0.25,

            237: 0.1,

            369: 0.44,

        },

    },

    fields={

        "category": [  # ← replaces current category list

            "Romance",

            "Classic Literature",

            "American Civil War",

        ],

    },

    # Note: \`book_title\`, \`publish_year\`, and \`dense_embedding\` are omitted → they stay as-is

)

# Update the document

result = collection.update(doc)   

print(result)  # {"code": 0} means success
```

The `update()` method validates the document first:

- **Incorrect usage** — such as an unknown field or wrong vector dimension — **raises an exception**.
- **If validation passes**, the method proceeds with the update and returns a `Status` object:
	- `{"code": 0}` indicates success.
	- Non-zero codes indicate failure (e.g., non-existing `ID`).

Successfully updated documents are immediately available for querying 🚀.

Update a document

```
let doc: ZVecDocInput = {   

    id: "book_1", // ← must already exist in the collection

    vectors: {

        "sparse_embedding": { // ← replaces entire sparse vector

            35: 0.25,

            237: 0.1,

            369: 0.44

        }

    },

    fields: {

        "category": [ // ← replaces current category list

            "Romance",

            "Classic Literature",

            "American Civil War"

        ]

    }

    // Note: \`book_title\`, \`publish_year\`, and \`dense_embedding\` are omitted → they stay as-is

};

// Update the document

let result = collection.updateSync(doc);  

console.log(result);  // { ok: true } means success
```

The `update()` method validates the document first:

- **Incorrect usage** — such as an unknown field or wrong vector dimension — **raises an exception**.
- **If validation passes**, the method proceeds with the update and returns a `Status` object:
	- `{ ok: true }` indicates success.
	- `{ ok: false }` indicates failure (e.g., non-existing `ID`).

Successfully updated documents are immediately available for querying 🚀.

---

## Update a Batch of Documents

To update multiple documents at once, pass a list of `Doc` objects to `update()`.  
Each `Doc` is processed independently, and the method returns a list of `Status` objects — one per document.

Update a batch of documents

```
import zvec

results = collection.update(  

    [

        zvec.Doc(

            id="book_1",

            vectors={

                "sparse_embedding": {35: 0.25, 237: 0.1, 369: 0.44},

            },

            fields={

                "category": ["Romance", "Classic Literature", "American Civil War"],

            },

        ),

        zvec.Doc(

            id="book_2",

            fields={

                "book_title": "The Great Gatsby",

            },

        ),

        zvec.Doc(

            id="book_3",

            fields={

                "book_title": "A Tale of Two Cities",

                "publish_year": 1859,

            },

        ),

    ]

)

print(results)  # [{"code":0}, {"code":0}, {"code":0}]
```

If any document in the batch has incorrect usage (e.g., an unknown field or wrong vector dimension), the method raises an exception and **no documents are updated**.

If all documents are valid, the method attempts to update every one. A failure in one (e.g., the `id` doesn't exist) does **not** stop others from being updated.

🔍 **Always check each `Status` in the result list.**

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)

### On this page

[Document `Doc`](https://zvec.org/en/docs/data-operations/update/#document-doc) [Update a Single Document](https://zvec.org/en/docs/data-operations/update/#update-a-single-document) [Update a Batch of Documents](https://zvec.org/en/docs/data-operations/update/#update-a-batch-of-documents)