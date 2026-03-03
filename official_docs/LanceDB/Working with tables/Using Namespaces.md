---
title: "Using Namespaces"
source: "https://docs.lancedb.com/tables/namespaces"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Use LanceDB's namespace-aware table and catalog APIs in Python, TypeScript, and Rust."
tags:
  - "clippings"
---
As your table organization needs grow over time and your projects become more complex, you can use namespaces to organize your tables in a way that reflects your business domains, teams, or environments.As described in the [Namespaces and Catalog Model](https://docs.lancedb.com/namespaces) section, namespaces are LanceDB’s way of generalizing catalog specs, providing developers a clean way to manage hierarchical organization of tables in the catalog. The SDKs treat `namespace` as a path and can use it for table resolution when you use LanceDB outside the root namespace.

## Table operations with namespace paths

Let’s imagine a scenario where your table management needs have evolved, and you now have the following multi-level structure to organize your tables outside the root namespace.Below, we show how you would express table operations within that namespace. Each item in the namespace list (`["prod", "search"]`) represents a level in the namespace hierarchy, and the table name is specified when you create, open, or drop it.

Using namespaces is **optional** in LanceDB, and most basic use cases do not require to work with them. An empty namespace (`[]`), which is the default, means “root namespace”, and the data will be stored in the `data/` directory under the specified root path.

## Namespace management APIs

You can open/create/drop tables inside a namespace path (like `["prod", "search"]`). The Python and Rust SDKs expose namespace lifecycle operations directly. In Python, use `lancedb.connect_namespace(...)` when calling namespace lifecycle methods such as `create_namespace`, `list_namespaces`, `describe_namespace`, and `drop_namespace`. In Rust, use `lancedb::connect_namespace(...)` and call `create_namespace`, `list_namespaces`, and `drop_namespace`.

In TypeScript, namespace lifecycle and namespace-scoped table operations are not currently exposed on `Connection`. In practice, namespaces in TypeScript are managed through a namespace-aware admin surface (for example [REST](https://docs.lancedb.com/api-reference/rest/index) /admin tooling), and the Connection APIs operate at the root namespace.

## Namespaces in LanceDB Enterprise

In LanceDB Enterprise deployments, configure namespace-backed federated databases in a TOML file under your deployment’s `config` directory. LanceDB Enterprise supports both directory-based (`ns_impl = "dir"`) and REST-based (`ns_impl = "rest"`) namespace implementations. The example below shows how to configure a directory-based namespace implementation in LanceDB Enterprise.The example above uses MinIO, but the same approach applies to other cloud object storage platforms based on your deployment.For REST-based namespace servers, you can specify the namespace implementation as `"rest"` with forwarding prefixed headers for authentication and context propagation.With `forward_header_prefixes = ["X-forward"]`, any incoming header starting with `X-forward` is forwarded to `http://<your_org>.internal.catalog.com`. This is useful for auth propagation, for example sending `X-forward-authorization: Bearer xxxx`.
- [Client SDK API references](https://docs.lancedb.com/api-reference)
- [REST API Reference](https://docs.lancedb.com/api-reference/rest)
- [Namespaces and the Catalog Model](https://docs.lancedb.com/namespaces)

[Update/modify data](https://docs.lancedb.com/tables/update) [Versioning](https://docs.lancedb.com/tables/versioning)