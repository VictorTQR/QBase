---
title: "Metadata Filtering in LanceDB"
source: "https://docs.lancedb.com/search/filtering"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Filter search results in LanceDB based on metadata fields."
tags:
  - "clippings"
---
LanceDB supports filtering features of query results based on metadata fields. While joint vector and metadata search at scale presents a significant challenge, LanceDB achieves sub-100ms latency at thousands of QPS, enabling efficient vector search with filtering capabilities even on datasets containing billions of records.**Pre-filtering is applied to top-k results by default** before executing the vector search. This narrow down the search space within large datasets, thereby reducing query latency. You can also use **post-filtering** to refine results after the vector search completes.To illustrate filtering capabilities, let’s try four data points with combinations of vectors and metadata:You can always filter your data without search. This is useful when you need to query based on metadata:

If your table is large, this could potentially return a very large amount of data. Please be sure to use a `limit` clause unless you’re sure you want to return the whole result set.

When querying large tables, omitting a `limit` clause may overwhelm resources and return excessive data. It can also increase costs as query pricing scales with data scanned and data returned ([LanceDB Cloud pricing](https://lancedb.com/pricing)).

## Filtering with SQL

Because it’s built on top of DataFusion, LanceDB embraces the utilization of standard SQL expressions as predicates for filtering operations. SQL can be used during vector search, update, and deletion operations.LanceDB supports a growing list of SQL expressions:

### Simple SQL Filters

For example, the following filter string is acceptable:

### Advanced SQL Filters

If your column name contains special characters, upper-case characters, or is a [SQL Keyword](https://docs.rs/sqlparser/latest/sqlparser/keywords/index.html), you can use backtick (`` ` ``) to escape it. For nested fields, each segment of the path must be wrapped in backticks.

Field names containing periods (.) are NOT supported.

Literals for dates, timestamps, and decimals can be written by writing the string value after the type name. For example:For timestamp columns, the precision can be specified as a number in the type parameter. Microsecond precision (6) is the default.

| SQL | Time unit |
| --- | --- |
| `timestamp(0)` | Seconds |
| `timestamp(3)` | Milliseconds |
| `timestamp(6)` | Microseconds |
| `timestamp(9)` | Nanoseconds |

## Apache Arrow Mapping

LanceDB internally stores data in [Apache Arrow](https://arrow.apache.org/) format. The mapping from SQL types to Arrow types is:

## Best Practices

**Scalar Indexes**: We strongly recommend creating scalar indices on columns used for filtering, whether combined with a search operation or applied independently (e.g., for updates or deletions).For best performance with large tables or high query volumes:
- Build a scalar index on frequently filtered columns
- Use exact column names in filters (e.g., `user_id` instead of `USER_ID`)
- Avoid complex transformations in filter expressions (keep them simple)
- When running concurrent queries, use connection pooling for better throughput
For a column of type LIST(T), you can use `LABEL_LIST` to create a scalar index. Then you should leverage DataFusion’s [array functions](https://datafusion.apache.org/user-guide/sql/scalar_functions.html#array-functions) like `array_has_any` or `array_has_all` for optimized filtering.

## Limitations

Both **pre-filtering** and **post-filtering** can yield false positives. For pre-filtering, if the filter is too selective, it might eliminate relevant items that the vector search would have otherwise identified as a good match. In this case, increasing `nprobes` parameter will help reduce such false positives. It is recommended to call `bypass_vector_index()` if you know that the filter is highly selective.Similarly, a highly selective post-filter can lead to false positives. Increasing both `nprobes` and `refine_factor` can mitigate this issue. When deciding between pre-filtering and post-filtering, pre-filtering is generally the safer choice if you’re uncertain.

[Hybrid search](https://docs.lancedb.com/search/hybrid-search) [Query optimization](https://docs.lancedb.com/search/optimize-queries)