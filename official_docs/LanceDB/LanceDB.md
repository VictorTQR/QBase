---
title: "LanceDB"
source: "https://docs.lancedb.com/"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Multimodal lakehouse for AI."
tags:
  - "clippings"
---
**LanceDB** is a [multimodal lakehouse](https://lancedb.com/blog/multimodal-lakehouse/) for AI, built on top of [Lance](https://docs.lancedb.com/lance), an open-source lakehouse format. Below, we list a few ways LanceDB can help you build and scale your AI and ML workloads.LanceDB is designed for a variety of workloads and deployment scenarios, and supports use cases that are way beyond traditional vector search. The LanceDB suite includes three products, all built on top of the same open-source Lance format and table abstractions.![](https://mintcdn.com/lancedb-bcbb4faf/E2bb7wPpAQiUkYbQ/static/assets/images/overview/lancedb-suite.png?fit=max&auto=format&n=E2bb7wPpAQiUkYbQ&q=85&s=9c5eb07d2726b501e3029d818f0be554)

## Use cases

- **Embedding pipelines**: Add new columns (features), create embeddings, and transform your data at scale. LanceDB lets you extend tables both vertically and horizontally with minimal I/O overhead.
- **Search**: Build high-performance search and retrieval applications using LanceDB’s optimized storage, including vector search, full-text search, and hybrid search with secondary indexes.
- **Training**: Efficiently access and manage large-scale multimodal datasets for training and fine-tuning AI models.
- **Exploratory Data Analysis**: Analyze and search through petabyte-scale multimodal datasets, including video and point cloud data, to gain insights and inform model development.

## Choose how you run LanceDB

Depending on your needs, you can choose one of three ways to run LanceDB.

### LanceDB OSS

The fastest way to get started is the open-source embedded library, with client SDKs in Python, TypeScript and Rust. Run it locally during development, then use the same data model and APIs as you scale up and need a managed solution. Start here:## [Quickstart](https://docs.lancedb.com/quickstart)

[

Get started with LanceDB in minutes.

](https://docs.lancedb.com/quickstart)Basic Table Operations

Create tables, search vectors, and modify data in LanceDB.

[View original](https://docs.lancedb.com/tables)

### LanceDB Enterprise

[LanceDB Enterprise](https://docs.lancedb.com/enterprise) is a distributed and managed **multimodal lakehouse** built for search, exploratory data analysis, feature engineering, and training-oriented data access workflows on top of the same core table abstraction. This eliminates the need for teams to build bespoke infrastructure to manage petabyte-scale multimodal datasets. To get started, reach out at [contact@lancedb.com](https://docs.lancedb.com/).

**Built with scale, performance, and security in mind.**LanceDB Enterprise is designed for very large-scale, high-performance, distributed workloads in private deployments, and can operate under strict security requirements.

### LanceDB Cloud

[LanceDB Cloud](https://docs.lancedb.com/cloud) is a serverless, managed service for users who are more focused on search use cases. You can easily create and manage projects in the Cloud UI, and integrate via REST API or client SDKs (Python, TypeScript, Rust).[![main-cloud-cta](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/get-started/main-cloud-cta.png?fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=27c8de8b0c345dc24ed650aeae15e5c5)](https://cloud.lancedb.com/)

[Quickstart](https://docs.lancedb.com/quickstart) [Lance format](https://docs.lancedb.com/lance)