---
title: "Quantization | Zvec"
source: "https://zvec.org/en/docs/concepts/vector-index/quantization/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Concepts](https://zvec.org/en/docs/concepts/) [Vector Index](https://zvec.org/en/docs/concepts/vector-index/)

## Quantization

Quantization is a compression technique that ***transforms vectors from their original (specifically FP32) format into a more compact representation***, reducing the size of vector indexes used for search.

This transformation approximates vectors using fewer bits per dimension — enabling:

- ✨ Lower **memory footprint** — especially when the index is memory-resident,
- ✨ Faster I/O and lower query latency — due to reduced data movement and efficient integer/fp16 arithmetic,
- ✨ Better scalability on resource-constrained hardware.

![Quantization](https://zvec.org/_next/static/media/quantization-example.bc2638c2.svg)

Quantization

**Important**:

- Quantization is a ***lossy and irreversible*** compression method. It improves runtime efficiency **at the cost of potentially reduced recall accuracy**. Always validate its effect on your retrieval quality.
- Quantization only provides benefits when applied to vectors in a **FP32** format.

## Storage Behavior

To ensure data integrity and flexibility, **Zvec stores both the original vectors and their quantized versions**. This means:

- The **overall on-disk storage usage may increase** (due to storing two copies).
- However, **only the quantized vectors are loaded into memory for indexing and search**, significantly reducing the active index size.
- Users can always **retrieve the original, unaltered vectors** when needed.

## Enabling Quantization

[Python API Reference](https://zvec.org/api-reference/python/schema/#zvec.model.schema.VectorSchema) [Node.js API Reference](https://zvec.org/api-reference/nodejs/interfaces/ZVecVectorSchema)

You can enable quantization at the time of vector index creation by selecting your preferred quantization type — e.g., `FP16`, `INT8`, or `INT4` — **using the `quantize_type` parameter in your `VectorSchema`**.

Once set, Zvec automatically generates and manages the quantized representation alongside your original vectors.

---

## Quantization Types

### FP16 (Half-Precision Floating Point)

Uses 16-bit floating-point numbers to reduce memory footprint and accelerate computation while maintaining high numerical precision. Ideal for applications requiring near-FP32 accuracy with improved efficiency. Requires conversion from FP32 source.

### INT8 (8-Bit Integer Quantization)

Represents vectors using 8-bit integers, significantly reducing storage and memory bandwidth requirements. Offers a good trade-off between speed, size, and retrieval accuracy for many similarity search tasks. Requires conversion from FP32 source.

### INT4 (4-Bit Integer Quantization)

Ultra-compact representation using only 4 bits per dimension. Maximizes storage density and inference speed, suitable for latency-sensitive or resource-constrained environments where noticeable accuracy loss is acceptable. Requires conversion from FP32 source.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[IVF Index](https://zvec.org/en/docs/concepts/vector-index/ivf-index/)

[

Inverted File Index

](https://zvec.org/en/docs/concepts/vector-index/ivf-index/)[

Inverted Index

Next Page

](https://zvec.org/en/docs/concepts/inverted-index/)

### On this page

[Storage Behavior](https://zvec.org/en/docs/concepts/vector-index/quantization/#storage-behavior) [Enabling Quantization](https://zvec.org/en/docs/concepts/vector-index/quantization/#enabling-quantization) [Quantization Types](https://zvec.org/en/docs/concepts/vector-index/quantization/#quantization-types) [FP16 (Half-Precision Floating Point)](https://zvec.org/en/docs/concepts/vector-index/quantization/#fp16-half-precision-floating-point) [INT8 (8-Bit Integer Quantization)](https://zvec.org/en/docs/concepts/vector-index/quantization/#int8-8-bit-integer-quantization) [INT4 (4-Bit Integer Quantization)](https://zvec.org/en/docs/concepts/vector-index/quantization/#int4-4-bit-integer-quantization)