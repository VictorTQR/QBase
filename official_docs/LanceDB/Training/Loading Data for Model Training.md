---
title: "Loading Data for Model Training"
source: "https://docs.lancedb.com/training/index"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Introduction to loading data, shuffling, and creating permutations for model training in LanceDB."
tags:
  - "clippings"
---
LanceDB makes an excellent data backend for training machine learning models. This section will describe the `Permutation` API in LanceDB that’s designed to facilitate the process of training a model and explain how to use LanceDB as a data backend for training.Most model training frameworks iterate through data in batches and feed this data into the model. This process is often referred to as **data loading**. The simplest way to load data into a model is to iterate a LanceDB table in a loop and feed the data into the model.In practice, this is too simplistic for effective training. We may not want to load all the data, or we may want to load the data in a different order, or we may need to apply some sort of processing to the data before training. To achieve this, we will often want to create a `Permutation` of the table.

## Selecting rows

When training a model, we might not want to load all of the data. For example, we might filter out columns that are not needed for training. We might also divide the data into training and validation sets. Or we could divide the data into multiple sets for cross-validation.Whenever we create a permutation of the table, we have to first decide which rows we want to include (and in what order). This is stored in a **permutation table** which marks out the row ids that make up our data. Other decisions, such as which columns to include, and what transformations to apply, can be defined at read time and don’t require a separate permutation table.

## Selecting all rows

To select all rows, we can use the `Permutation.identity` method. This gives us a `Permutation` without requiring us to create a separate permutation table. This allows us to refine our columns and apply transformations and can be useful when the data loader itself is responsible for handling sampling and shuffling.

## Filtering rows

If we only want to select a subset of rows, then we can use a filter. This will require us to create a permutation table which identifies which rows we want to include.

## Creating splits

LanceDB also provides several different methods for creating splits. These allow us to divide our dataset into smaller non-overlapping sets. The split can then be specified when creating the `Permutation` object to view only a subset of the data.

## Shuffling rows

By default, permutations will access the data in the order the data is stored in the table. This can cause our model to learn artifacts specific to the order of the data. This is one of many ways we can “overfit” our model to our data. To avoid this, we typically want to shuffle the data before training. Model training frameworks (like PyTorch) will often provide a way to shuffle the data. If you are not using one of these frameworks, or if you want to shuffle the data with LanceDB, you can shuffle the rows when you create a permutation table.

## Selecting columns

By default, permutations will return all columns in the table. If you only need a subset of the columns, you can significantly reduce your I/O requirements by selecting only the columns you need. This can be done on the permutation object itself, and does not require us to create a separate permutation table.

[Configuring storage](https://docs.lancedb.com/storage/configuration) [PyTorch integration](https://docs.lancedb.com/training/torch)