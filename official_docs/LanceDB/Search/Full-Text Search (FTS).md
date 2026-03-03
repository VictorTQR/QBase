---
title: "Full-Text Search (FTS)"
source: "https://docs.lancedb.com/search/full-text-search"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to implement full-text search in LanceDB using BM25 for keyword-based retrieval."
tags:
  - "clippings"
---
LanceDB provides support for Full-Text Search via Lance, allowing you to incorporate keyword-based search (based on BM25) in your retrieval solutions.

## Basic Usage

Consider that we have a LanceDB table named `my_table`, whose string column `text` we want to index and query via keyword search, the FTS index must be created before you can search via keywords.

### Table Setup

First, open or create the table you want to search:

### Construct FTS Index

Create a full-text search index on your text column:

In Python, this page shows the synchronous `create_fts_index(...)` form. For the asynchronous equivalent (`await table.create_index("text", config=FTS(...))`), see [FTS index](https://docs.lancedb.com/indexing/fts-index).

```
table.create_fts_index("text")
```

Perform full-text search and retrieve results:The search is conducted on all indexed columns by default, so it’s useful when there are multiple indexed columns.If you want to specify which columns to search use `fts_columns="text"`

LanceDB automatically searches on the existing FTS index if the input to the search is of type `str`. If you provide a vector as input, LanceDB will search the ANN index instead.

## Advanced Usage

### Tokenize Table Data

By default, the text is tokenized by splitting on punctuation and whitespaces, and would filter out words that are longer than 40 characters. All words are converted to lowercase.Stemming is useful for improving search results by reducing words to their root form, e.g. “running” to “run”. LanceDB supports stemming for multiple languages. You should set the `base_tokenizer` parameter rather than `tokenizer_name` because you cannot customize the tokenizer if `tokenizer_name` is specified.For example, to enable stemming for English:The tokenizer is customizable, you can specify how the tokenizer splits the text, and how it filters out words, etc.**Default index parameters:**
- `base_tokenizer`: `"simple"`
- `language`: English
- `with_position`: false
- `max_token_length`: 40
- `lower_case`: true
- `stem`: true
- `remove_stop_words`: true
- `ascii_folding`: true
For example, for language with accents, you can specify the tokenizer to use `ascii_folding` to remove accents, e.g. ‘é’ to ‘e’:

### Filtering Options

LanceDB full text search supports to filter the search results by a condition, both pre-filtering and post-filtering are supported.This can be invoked via the familiar `where` syntax.With pre-filtering:

```
table.search("puppy").limit(10).where("text='foo'", prefilter=True).to_list()
```

With post-filtering:

```
table.search("puppy").limit(10).where("text='foo'", prefilter=False).to_list()
```

### Phrase vs. Terms Queries

Lance-based FTS doesn’t support queries using boolean operators `OR`, `AND` in the search string.

For full-text search you can specify either a **phrase** query like `"the old man and the sea"`, or a **terms** search query like `old man sea`.To search for a phrase, the index must be created with `with_position=True` and `remove_stop_words=False`:This will allow you to search for phrases, but it will also significantly increase the index size and indexing time.Fuzzy search allows you to find matches even when the search terms contain typos or slight variations. LanceDB uses the classic [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance) to find similar terms within a specified edit distance.Let’s create a sample table and build full-text search indices to demonstrate fuzzy search capabilities and relevance boosting features.

### Search for Substring

LanceDB supports searching for substrings in the text column, you can set the `base_tokenizer` parameter to `"ngram"` to enable this feature, and use the parameters `ngram_min_length` and `ngram_max_length` to control the length of the substrings:

### Generate Data

First, let’s create a table with sample text data for testing fuzzy search:

```
import lancedb

import numpy as np

import pandas as pd

import random

# Connect to LanceDB

db = lancedb.connect(

    uri="db://your-project-slug",

    api_key="your-api-key",

    region="us-east-1"

)

# Generate sample data

table_name = "fts-fuzzy-boosting-test"

vectors = [np.random.randn(128) for _ in range(100)]

text_nouns = ("puppy", "car")

text2_nouns = ("rabbit", "girl", "monkey")

verbs = ("runs", "hits", "jumps", "drives", "barfs")

adv = ("crazily.", "dutifully.", "foolishly.", "merrily.", "occasionally.")

adj = ("adorable", "clueless", "dirty", "odd", "stupid")

# Generate random text combinations

text = [

    " ".join([

        text_nouns[random.randrange(0, len(text_nouns))],

        verbs[random.randrange(0, 5)],

        adv[random.randrange(0, 5)],

        adj[random.randrange(0, 5)],

    ])

    for _ in range(100)

]

text2 = [

    " ".join([

        text2_nouns[random.randrange(0, len(text2_nouns))],

        verbs[random.randrange(0, 5)],

        adv[random.randrange(0, 5)],

        adj[random.randrange(0, 5)],

    ])

    for _ in range(100)

]

count = [random.randint(1, 10000) for _ in range(100)]
```

### Create Table

### Construct FTS Index

Create a full-text search index on the first text column:Then, create an index on the second text column:Now we can perform basic, fuzzy, and prefix match searches:

#### Prefix based Match

Prefix-based match allows you to search for documents containing words that start with a specific prefix.

### Phrase Match

Phrase matching enables you to search for exact sequences of words. Unlike regular text search which matches individual terms independently, phrase matching requires words to appear in the specified order with no intervening terms.

Phrase queries are supported but only for a single column; providing multiple columns with a quoted phrase raises an error.

Phrase matching is particularly useful for:
- Searching for specific multi-word expressions
- Matching exact titles or quotes
- Finding precise word combinations in a specific order

#### Flexible Phrase Match

To provide more flexible phrase matching, LanceDB supports the `slop` parameter. This allows you to match phrases where the terms appear close to each other, even if they are not directly adjacent or in the exact order, as long as they are within the specified `slop` value.For example, the phrase query “puppy merrily” would not return any results by default. However, if you set `slop=1`, it will match phrases like “puppy jumps merrily”, “puppy runs merrily”, and similar variations where one word appears between “puppy” and “merrily”.

### Search with Boosting

Boosting allows you to control the relative importance of different search terms or fields in your queries. This feature is particularly useful when you need to:
- Prioritize matches in certain columns
- Promote specific terms while demoting others
- Fine-tune relevance scoring for better search results

```
from lancedb.query import MatchQuery, BoostQuery, MultiMatchQuery

# Boost data with 'runs' in text more than 'puppy' in text

print("\n2. Boosting data with 'runs' in text:")

boosting_results = (

  table.search(

      BoostQuery(

          MatchQuery("runs", "text"),

          MatchQuery("puppy", "text"),

          negative_boost=0.2,

      ),

  )

  .select(["id", "text"])

  .limit(100)

  .to_pandas()

)

"""Test searching across multiple fields."""

print("\n=== Multi Match Query Examples ===")

# Search across both text and text2

print("\n1. Searching 'crazily' in both text and text2:")

multi_match_results = (

    table.search(MultiMatchQuery("crazily", ["text", "text2"]))

    .select(["id", "text", "text2"])

    .limit(100)

    .to_pandas()

)

# Search with field boosting

print("\n2. Searching with boosted text2 field:")

multi_match_boosting_results = (

    table.search(

        MultiMatchQuery("crazily", ["text", "text2"], boosts=[1.0, 2.0]),

    )

    .select(["id", "text", "text2"])

    .limit(100)

    .to_pandas()

)
```

## Best practices

- Use fuzzy search when handling user input that may contain typos or variations
- Apply field boosting to prioritize matches in more important columns
- Combine fuzzy search with boosting for robust and precise search results
**Recommendations for optimal FTS performance:**
- Create full-text search indices on text columns that will be frequently searched
- For hybrid search combining text and vectors, see our [hybrid search guide](https://docs.lancedb.com/search/hybrid-search)
- For performance benchmarks, check our [benchmark results](https://docs.lancedb.com/enterprise/benchmarks)
- For complex queries, use SQL to combine FTS with other filter conditions

### Boolean Queries

LanceDB supports boolean logic in full-text search, allowing you to combine multiple queries using `and` and `or` operators. This is useful when you want to match documents that satisfy multiple conditions (intersection) or at least one of several conditions (union).

#### Combining Two Match Queries

In Python, you can combine two MatchQuery objects using either the `and` function or the `&` operator (e.g., `MatchQuery("puppy", "text") and MatchQuery("merrily", "text")`); both methods are supported and yield the same result. Similarly, you can use either the `or` function or the `|` operator to perform an or query.In TypeScript, boolean queries are constructed using the `BooleanQuery` class with a list of \[Occur, subquery\] pairs. For example, to perform an AND query:

SQL

This approach allows you to specify complex boolean logic by combining multiple subqueries with different Occur values (such as `Must`, `Should`, or `MustNot`).

**Which queries are allowed?**A boolean query must include at least one `SHOULD` or `MUST` clause. Queries that contain only a `MUST_NOT` clause are not allowed.

**How to use booleans?**
- Use `and` / `&` (Python), `Occur.Must` (Typescript) for intersection (documents must match all queries).
- Use `or` / `|` (Python), `Occur.Should` (Typescript) for union (documents must match at least one query).

LanceDB supports searching for substrings in text columns using n-gram tokenization. This is useful for finding partial matches within text content.

### Setting Up the Table

First, create a table with sample text data and configure n-gram tokenization:With the default n-gram settings (minimum length of 3), you can search for substrings of length 3 or more:

### Handling Short Substrings

By default, the minimum n-gram length is 3, so shorter substrings like “la” won’t match:

### Customizing N-gram Parameters

You can customize the n-gram behavior by adjusting the minimum length and using prefix-only matching:

### Testing Custom N-gram Settings

With the new settings, you can now search for shorter substrings and use prefix-only matching:LanceDB supports full-text search on string array columns, enabling efficient keyword-based search across multiple values within a single field (e.g., tags, keywords).

### Setting Up the Connection

Connect to your LanceDB instance:

### Defining the Schema

Create a schema that includes an array field for tags:

### Creating Sample Data

Generate sample data with array fields containing tags:

### Creating the Table and Adding Data

Create the table and populate it with the sample data:Create an FTS index on the tags column to enable efficient text search:Search for terms with typos using fuzzy matching:Search for exact phrases within the array fields:

[Multivector search](https://docs.lancedb.com/search/multivector-search) [Hybrid search](https://docs.lancedb.com/search/hybrid-search)