---
title: "Conditional Filtering | Zvec"
source: "https://zvec.org/en/docs/data-operations/query/filter/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/) [Query](https://zvec.org/en/docs/data-operations/query/)

## Conditional Filtering

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.query) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#querysync)

Conditional filtering lets you retrieve documents that match specific criteria based on their scalar fields — similar to a `WHERE` clause in SQL.

---

## Performance Considerations

- **Indexed scalar fields**: Can be efficiently searched.
- **Unindexed scalar fields**: Can still be searched, but with significantly lower performance.

---

## Prerequisites

This guide assumes you have opened a collection containing scalar fields.

---

## Performing Conditional Filtering

Apply conditional filtering by passing a `filter` expression to the `query()` method.

The expression uses **SQL-like syntax** to define search conditions.

The `topk` parameter specifies the maximum number of matching documents to return.

The `query()` method with a `filter` returns a list of matching `Doc` objects.

Each `Doc` object includes:

1. `id`: The document identifier.
2. `vectors`: A dictionary of vector embeddings.  
	This is **only populated** if `include_vector=True` is passed in the query.
3. `fields`: A dictionary of scalar field values.  
	By default, **all scalar fields** are returned; this can be restricted using the `output_fields` parameter.

---

## Supported Filter Syntax

### Comparison Operators

| Operator | Description | Supported Data Types | Example Expression |
| --- | --- | --- | --- |
| `<` | Less than | Integers, Floats, Strings | `publish_year < 2000` |
| `<=` | Less than or equal to | Integers, Floats, Strings | • `price <= 29.99`   • `author_name <= 'M'` |
| `=` | Equal to | Integers, Floats, Strings, Booleans | • `in_stock = true`   • `name = 'Michael'` |
| `!=` | Not equal to | Integers, Floats, Strings, Booleans | • `rating != 5`   • `status != 'active'` |
| `>=` | Greater than or equal to | Integers, Floats, Strings | `score >= 85.5` |
| `>` | Greater than | Integers, Floats, Strings | `age > 12` |
| `is null` | Checks if a field has no value | All data types | `email is null` |
| `is not null` | Checks if a field has a value | All data types | `email is not null` |

### Membership Operators

| Operator | Description | Supported Data Types | Example Expression | Explanation |
| --- | --- | --- | --- | --- |
| `in` | Is one of | Integers, Floats, Strings | • `error_code in (400, 403, 404)`   • `user_name in ('admin', 'root')` | Evaluates to `true` if the field value **matches any** of the listed values.      • `error_code` is `400`, `403`, or `404` → `true`   • `user_name` is `'admin'` or ' `root'` → `true` |
| `not in` | Is not one of | Integers, Floats, Strings | `status not in ('deleted', 'archived')` | Evaluates to `true` if the field value **does not match any** of the listed values.      • `status` is anything other than `'deleted'` or `'archived'` → `true` |
| `contain_all` | Array includes **all** listed values | Array Types | `tags contain_all ('urgent', 'bug')` | Evaluates to `true` only if the array contains **every** value in the list.      • `tags = ['bug', 'urgent', 'ui']` → `true`   • `tags = ['bug', 'ui']` → `false` (missing 'urgent') |
| `contain_any` | Array includes **at least one** of the listed value | Array Types | `permissions contain_any ('execute', 'write')` | Evaluates to `true` if the array contains **at least one** of the listed values.      • `permissions = ['admin', 'execute']` → `true`   • `permissions = ['read', 'forbidden']` → `false` (neither 'execute' nor 'write') |
| `array_length` | Array length | Array Types | `array_length(tags) > 2` | Evaluates to `true` if the array's length satisfies the condition.      • `tags = ['bug']` → `false` (length is 1)   • `tags = ['bug', 'urgent', 'fix']` → `true` (length is 3) |

### String Operators

| Operator | Description | Supported Data Types | Example Expression | Explanation |
| --- | --- | --- | --- | --- |
| `like` | Pattern match with wildcards | Strings | • `product_name like 'Smart%'`   • `file_name like '%.log'` | • `'Smart%'`: matches values starting with 'Smart' (e.g., 'SmartPhone', 'SmartWatch')   • `'%.log'`: matches values ending with '.log' (e.g., 'app.log', 'debug\_2025.log') |

**Performance Considerations**:  
For optimal `LIKE` query performance, fields should be [indexed](https://zvec.org/en/docs/concepts/inverted-index/).

- **Unindexed fields** still support filtering, but queries may be **significantly slower**.
- For **efficient infix/suffix patterns** (`'abc%def'`, `'%abc'`), configure an inverted index with `enable_extended_wildcard = true` option.
- Patterns with **multiple wildcards** (e.g., `'%abc%def%'`) are inherently expensive and should be used sparingly.

### Logical Operators

| Operator | Description | Example Expression | Explanation |
| --- | --- | --- | --- |
| `and` | Logical AND | `status = 'active' and score > 90` | Evaluates to `true` only if **all** conditions are `true`. |
| `or` | Logical OR | `role = 'admin' or permission = 'write'` | Evaluates to `true` if **at least one** condition is `true`. |

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Multiple Vectors](https://zvec.org/en/docs/data-operations/query/multi-vector/)

[

Previous Page

](https://zvec.org/en/docs/data-operations/query/multi-vector/)[

Vector + Filter

Next Page

](https://zvec.org/en/docs/data-operations/query/hybrid/)