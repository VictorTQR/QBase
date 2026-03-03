---
title: "Configuring Cloud Storage in LanceDB"
source: "https://docs.lancedb.com/storage/configuration"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Configure LanceDB to use S3, GCS, Azure Blob, and S3-compatible object stores with environment variables or storage options."
tags:
  - "clippings"
---
When using LanceDB OSS, you can choose where to store your data. The tradeoffs between storage options are covered in the [storage architecture guide](https://docs.lancedb.com/storage). This page shows how to configure each backend.

## Object stores

LanceDB supports AWS S3 (and compatible stores), Azure Blob Storage, and Google Cloud Storage. The URI scheme in your `connect` call selects the backend.

### Configuration options

When running inside the target cloud with correct IAM bindings, LanceDB often needs no extra configuration. When running elsewhere, provide credentials via environment variables or `storage_options`.

Keys are case-insensitive. Use lowercase in `storage_options` and uppercase in environment variables.

If you need the option to apply only to a specific table:

### Dynamic credentials with StorageOptionsProvider Python-only

Use a storage options provider when credentials expire (for example, short-lived STS credentials). Pass any provider object that implements `fetch_storage_options()` with `storage_options_provider` on table operations such as `create_table` and `open_table`. In SDK versions that expose `StorageOptionsProvider`, you can subclass it directly.If `fetch_storage_options()` returns `expires_at_millis`, LanceDB refreshes credentials before that timestamp. You can optionally set `refresh_offset_millis` (in milliseconds) to refresh earlier.

#### General object store options

These are commonly used options. Cloud-specific keys (for example `region`, `endpoint`, `service_account`, and Azure credential keys) are backend-dependent and can be provided in `storage_options` as needed.

## AWS S3

![](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/storage/aws.jpg?fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=e5ca36574c5c78fb379e1ffb0a6836bc) Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_SESSION_TOKEN` as environment variables or pass them in `storage_options`. Region is optional for AWS but required for most S3-compatible stores.Minimum permissions usually include `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`, and `s3:GetBucketLocation` scoped to the relevant bucket/prefix.

### S3-compatible stores

If the endpoint is `http://` (common in local development), also set `ALLOW_HTTP=true` or pass `allow_http=True` in `storage_options`.

### S3 Express

Consult AWS networking requirements for S3 Express before enabling.

### DynamoDB commit store for concurrent writes

S3 lacks atomic writes. To enable safe concurrent writers, use DynamoDB as a commit store by switching to the `s3+ddb` scheme and specifying the table name.Create the DynamoDB table with hash key `base_uri` (string) and range key `version` (number). Small provisioned throughput (for example `ReadCapacityUnits=1`, `WriteCapacityUnits=1`) is sufficient for coordination.

LanceDB aborts multipart uploads on graceful shutdown, but crashes can leave incomplete uploads. Add an S3 lifecycle rule to delete in-progress uploads after a few days.

## Google Cloud Storage

![](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/storage/gcp.jpg?fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=c6e235e8dc41623579d507a8dd7d60ef) Provide credentials via `GOOGLE_SERVICE_ACCOUNT` (path to JSON) or include the path in `storage_options`. GCS defaults to HTTP/1; set `HTTP1_ONLY=false` if you need HTTP/2.

## Azure Blob Storage

![](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/storage/azure.jpg?fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=2ab2a9af6d996eb0cd0ca1273738f360) Set `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCOUNT_KEY` as environment variables, or pass them via `storage_options`.Other supported keys include service principal credentials (`azure_client_id`, `azure_client_secret`, `azure_tenant_id`), SAS tokens, managed identities, and custom endpoints.

## Tigris Object Storage

![](https://mintcdn.com/lancedb-bcbb4faf/0sS6vrpmM3KSVyss/static/assets/images/storage/tigris.jpg?fit=max&auto=format&n=0sS6vrpmM3KSVyss&q=85&s=572dbfe7dd0a3e125b36f73b33df5fda) Tigris exposes an S3-compatible API. Configure the endpoint and region:Environment variables `AWS_ENDPOINT=https://t3.storage.dev` and `AWS_DEFAULT_REGION=auto` achieve the same configuration.

[Storage options](https://docs.lancedb.com/storage) [Data loading and shuffles](https://docs.lancedb.com/training)