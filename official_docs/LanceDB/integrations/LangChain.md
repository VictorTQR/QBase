---
title: "LangChain"
source: "https://docs.lancedb.com/integrations/ai/langchain"
author:
  - "[[LanceDB]]"
published:
created: 2026-02-05
description:
tags:
  - "clippings"
---
**LangChain** is a framework designed for building applications with large language models (LLMs) by chaining together various components. It supports a range of functionalities including memory, agents, and chat models, enabling developers to create context-aware applications.![Illustration](https://raw.githubusercontent.com/lancedb/assets/refs/heads/main/docs/assets/integration/langchain_rag.png)

Illustration

LangChain streamlines these stages (in figure above) by providing pre-built components and tools for integration, memory management, and deployment, allowing developers to focus on application logic rather than underlying complexities.Integration of **Langchain** with **LanceDB** enables applications to retrieve the most relevant data by comparing query vectors against stored vectors, facilitating effective information retrieval. It results in better and context aware replies and actions by the LLMs.

## Quick Start

You can load your document data using langchain’s loaders, for this example we are using `TextLoader` and `OpenAIEmbeddings` as the embedding model.

Python

## Documentation

In the above example `LanceDB` vector store class object is created using `from_documents()` method which is a `classmethod` and returns the initialized class object.You can also use `LanceDB.from_texts(texts: List[str],embedding: Embeddings)` class method.The exhaustive list of parameters for `LanceDB` vector store are:

| Name | type | Purpose | default |
| --- | --- | --- | --- |
| `connection` | (Optional) `Any` | `lancedb.db.LanceDBConnection` connection object to use. If not provided, a new connection will be created. | `None` |
| `embedding` | (Optional) `Embeddings` | Langchain embedding model. | Provided by user. |
| `uri` | (Optional) `str` | It specifies the directory location of **LanceDB database** and establishes a connection that can be used to interact with the database. | `/tmp/lancedb` |
| `vector_key` | (Optional) `str` | Column name to use for vector’s in the table. | `'vector'` |
| `id_key` | (Optional) `str` | Column name to use for id’s in the table. | `'id'` |
| `text_key` | (Optional) `str` | Column name to use for text in the table. | `'text'` |
| `table_name` | (Optional) `str` | Name of your table in the database. | `'vectorstore'` |
| `api_key` | (Optional `str`) | API key to use for LanceDB cloud database. | `None` |
| `region` | (Optional) `str` | Region to use for LanceDB cloud database. | Only for LanceDB Cloud: `None`. |
| `mode` | (Optional) `str` | Mode to use for adding data to the table. Valid values are “append” and “overwrite”. | `'overwrite'` |
| `table` | (Optional) `Any` | You can connect to an existing table of LanceDB, created outside of langchain, and utilize it. | `None` |
| `distance` | (Optional) `str` | The choice of distance metric used to calculate the similarity between vectors. | `'l2'` |
| `reranker` | (Optional) `Any` | The reranker to use for LanceDB. | `None` |
| `relevance_score_fn` | (Optional) `Callable[[float], float]` | Langchain relevance score function to be used. | `None` |
| `limit` | `int` | Set the maximum number of results to return. | `DEFAULT_K` (it is 4) |

Python

### Methods

##### add\_texts()

This method turn texts into embedding and add it to the database.It returns list of ids of the added texts.

Python

---

##### create\_index()

This method creates a scalar(for non-vector cols) or a vector index on a table.For index creation make sure your table has enough data in it. An ANN index is ususally not needed for datasets ~100K vectors. For large-scale (>1M) or higher dimension vectors, it is beneficial to create an ANN index.

Python

---

##### similarity\_search()

This method performs similarity search based on **text query**.Return documents most similar to the query **without relevance scores**.

Python

---

##### similarity\_search\_by\_vector()

The method returns documents that are most similar to the specified **embedding (query) vector**.**It does not provide relevance scores.**

Python

---

##### similarity\_search\_with\_score()

Returns documents most similar to the **query string** along with their relevance scores.It gets called by base class’s `similarity_search_with_relevance_scores` which selects relevance score based on our `_select_relevance_score_fn`.

Python

---

##### similarity\_search\_by\_vector\_with\_relevance\_scores()

Similarity search using **query vector**.The method returns documents most similar to the specified embedding (query) vector, along with their relevance scores.

Python

---

##### max\_marginal\_relevance\_search()

This method returns docs selected using the maximal marginal relevance(MMR). Maximal marginal relevance optimizes for similarity to query AND diversity among selected documents.Similarly, `max_marginal_relevance_search_by_vector()` function returns docs most similar to the embedding passed to the function using MMR. instead of a string query you need to pass the embedding to be searched for.

Python

---

##### add\_images()

This method ddds images by automatically creating their embeddings and adds them to the vectorstore.It returns list of IDs of the added images.

Python

[Voxel51](https://docs.lancedb.com/integrations/data/voxel51) [LlamaIndex](https://docs.lancedb.com/integrations/ai/llamaIndex)