---
title: "PyTorch Integration"
source: "https://docs.lancedb.com/training/torch"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to use LanceDB with PyTorch for training and inference."
tags:
  - "clippings"
---
LanceDB provides a seamless integration with PyTorch for training and inference. This allows you to use LanceDB as a backend for your PyTorch models, and to use PyTorch for training and inference. You can use LanceDB to store your data, and PyTorch to train your models.

## Quickstart

The `Table` class in LanceDB implements a contract for a PyTorch [Dataset](https://docs.pytorch.org/docs/stable/data.html#torch.utils.data.Dataset). This means you can simply use a LanceDB table in a PyTorch dataloader directly.

Python

Although the `Table` class in LanceDB implements the `torch.utils.data.Dataset` interface, you may find that using a table [Permutation](https://docs.lancedb.com/training) is more flexible.

Python

## Output Formats

By default, a `Table` data loader will emit a `pyarrow.RecordBatch`. To convert to a different format (such as a `pytorch.Tensor`), you will need to provide a custom collate function.The `Permutation` class is more flexible. By default, the output will be a list of dicts. This is the default output format of standard data loaders and usually more convenient when you are getting started. However, there is a significant performance penalty converting from Arrow, Lance’s internal representation, to this default format.To address this, the `Permutation` class provides a set of builtin transform functions that can be applied to map the Arrow data in different ways. The `arrow` and `polars` formats will always avoid data copies. However, `numpy`,`pandas`, and `torch_col` formats will also avoid data copies in most cases. The `python`, `python_col`, and `torch` formats will all require at least one full copy of the data and are the slowest options.

### Using the torch\_col format with a torch data loader

The `torch_col` format is the most efficient way to convert from Arrow to a `torch.Tensor`. It will convert the entire Arrow batch to a *column-major* `torch.Tensor`. In other words, given C columns and R rows, the resulting Tensor will have shape `(C, R)`. However, this format generates an error if you are using a `torch.utils.data.DataLoader` with the default collation function:

Python

This error occurs because the default collation function does not currently expect a single two-dimensional tensor. It expects a list of tensors which it will then stack. This is what is output by the `torch` format but that format requires a data copy. To avoid this error, and avoid data copies, you will need to provide a custom collation function in addition to specifying the `torch_col` format.

Python

This will now output a single two-dimensional tensor for each batch.

## Selecting columns

By default, the `Table` class will return all columns in the table when used as input to PyTorch. If you only need a subset of columns, you can significantly reduce your I/O requirements by selecting only the columns you need. The `Permutation` class provides a `select_columns` method that provides this functionality.

Python

[Data loading and shuffles](https://docs.lancedb.com/training) [Overview](https://docs.lancedb.com/geneva)