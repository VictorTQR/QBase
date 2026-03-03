---
title: "GPU-Powered Vector Indexing"
source: "https://docs.lancedb.com/indexing/gpu-indexing"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Accelerate IVF and HNSW index builds with GPU acceleration in LanceDB."
tags:
  - "clippings"
---
With LanceDB’s GPU-powered vector indexing you can index very large datasets in far less time than you could with the default CPU-based indexing. In our tests, LanceDB is capable of indexing billions of rows in under four hours on a 1-8 GPU cluster.

**Automatic GPU indexing** Enterprise-only Automatic GPU Indexing is currently only available in [LanceDB Enterprise](https://docs.lancedb.com/enterprise). Please [contact us](https://docs.lancedb.com/indexing/) to enable this feature for your deployment.The vector index is created when you call `create_index`. The backend will use GPU resources to build either the IVF or HNSW indexes. The system automatically selects the optimal GPU configuration based on your data size and available hardware.This process is also asynchronous by default, but you can use `wait_for_index` to convert it into a synchronous process by waiting until the index is built.

## Manual GPU indexing in LanceDB OSS

You can use the Python SDK to manually create the `IVF_PQ` index on a GPU. You’ll need [PyTorch>2.0](https://pytorch.org/). Note that GPU-based indexing is currently only supported by the synchronous SDK in LanceDB OSS.Specify the values `cuda` or `mps` (on Apple Silicon) for the `accelerator` parameter to enable GPU training on your device.

### GPU indexing on Linux

### GPU indexing on macOS (Apple Silicon)

## Performance considerations

- GPU memory usage scales with `num_partitions` and vector dimensions
- For optimal performance, ensure GPU memory exceeds dataset size
- Batch size is automatically tuned based on available GPU memory
- Indexing speed improves with larger batch sizes

## Troubleshooting

If you encounter the error `AssertionError: Torch not compiled with CUDA enabled`, you need to [install PyTorch with CUDA support](https://pytorch.org/get-started/locally/).

[Scalar Index](https://docs.lancedb.com/indexing/scalar-index) [Quantization](https://docs.lancedb.com/indexing/quantization)