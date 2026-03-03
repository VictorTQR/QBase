---
title: "Schema and Data Evolution"
source: "https://docs.lancedb.com/tables/schema"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to manage table schemas in LanceDB, including adding, altering, and dropping columns."
tags:
  - "clippings"
---
Schema evolution enables non-breaking modifications to a database table’s structure — such as adding columns, altering data types, or dropping fields — to adapt to evolving data requirements without service interruptions. LanceDB supports ACID-compliant schema evolution through granular operations (add/alter/drop columns), allowing you to:
- Iterate Safely: Modify schemas in production with versioned datasets and backward compatibility
- Scale Seamlessly: Handle ML model iterations, regulatory changes, or feature additions
- Optimize Continuously: Remove unused fields or enforce new constraints without downtime

## Schema Evolution Operations

LanceDB supports three primary schema evolution operations:
1. **Adding new columns**: Extend your table with additional attributes
2. **Altering existing columns**: Change column names, data types, or nullability
3. **Dropping columns**: Remove unnecessary columns from your schema

Schema evolution operations are applied immediately but do not typically require rewriting all data. However, data type changes may involve more substantial operations.

## Adding New Columns

You can add new columns to a table with the [`add_columns`](https://lancedb.github.io/lancedb/python/python/#lancedb.table.Table.add_columns) method in Python or [`addColumns`](https://lancedb.github.io/lancedb/js/classes/Table/#addcolumns) in TypeScript/JavaScript. New columns are populated based on SQL expressions you provide.

### Setting Up the Example Table

First, let’s create a sample table with product data to demonstrate schema evolution:

### Adding Calculated Columns

You can add new columns that are calculated from existing data using SQL expressions:

### Adding Columns with Default Values

Add boolean columns with default values for status tracking:

### Adding Nullable Columns

Add timestamp columns that can contain NULL values:

When adding columns that should contain NULL values, be sure to cast the NULL to the appropriate type, e.g., `cast(NULL as timestamp)`.

## Altering Existing Columns

You can alter columns using the [`alter_columns`](https://lancedb.github.io/lancedb/python/python/#lancedb.table.Table.alter_columns) method in Python or [`alterColumns`](https://lancedb.github.io/lancedb/js/classes/Table/#altercolumns) in TypeScript/JavaScript. This allows you to:
- Rename a column
- Change a column’s data type
- Modify nullability (whether a column can contain NULL values)

### Setting Up the Example Table

Create a table with a custom schema to demonstrate column alterations:

### Renaming Columns

Change column names to better reflect their purpose:

### Changing Data Types

Convert column data types for better performance or compatibility:

### Making Columns Nullable

Allow columns to contain NULL values:

### Multiple Changes at Once

Apply several alterations in a single operation:

Changing data types requires rewriting the column data and may be resource-intensive for large tables. Renaming columns or changing nullability is more efficient as it only updates metadata.

## Dropping Columns

You can remove columns using the [`drop_columns`](https://lancedb.github.io/lancedb/python/python/#lancedb.table.Table.drop_columns) method in Python or [`dropColumns`](https://lancedb.github.io/lancedb/js/classes/Table/#dropcolumns) in TypeScript/JavaScript.

### Setting Up the Example Table

Create a table with temporary columns that we’ll remove:

### Dropping Single Columns

Remove individual columns that are no longer needed:

### Dropping Multiple Columns

Remove several columns at once for efficiency:

Dropping columns cannot be undone. Make sure you have backups or are certain before removing columns.

## Vector Column Considerations

Vector columns (used for embeddings) have special considerations. When altering vector columns, you should ensure consistent dimensionality.

### Converting List to FixedSizeList

A common schema evolution task is converting a generic list column to a fixed-size list for performance:

[Working with multimodal data](https://docs.lancedb.com/tables/multimodal) [Update/modify data](https://docs.lancedb.com/tables/update)