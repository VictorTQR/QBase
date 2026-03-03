---
title: "Configuration | Zvec"
source: "https://zvec.org/en/docs/config/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
## Configuration

[Python API Reference](https://zvec.org/api-reference/python/config/) [Node.js API Reference](https://zvec.org/api-reference/nodejs/functions/ZVecInitialize)

Before performing any database operations, you can optionally configure global settings using the `init()` function.

- If omitted, Zvec automatically applies sensible defaults — typically tuned to your system's available memory, CPU, and environment.
- Use `init()` when you need to customize settings, such as
	- Adjusting log verbosity or output format
	- Controlling concurrency (e.g., query thread count)

## Configuration Example

Global configuration

```
import zvec

zvec.init(

    log_type=zvec.LogType.CONSOLE,

    log_level=zvec.LogLevel.WARN,

    query_threads=4,

)
```

- Logs messages to the **console** at `WARN` level or higher.
- Limits query execution to 4 threads.

For a complete list of configuration options and advanced tuning parameters, please refer to the [API Reference](https://zvec.org/api-reference/).

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)

### On this page

[Configuration Example](https://zvec.org/en/docs/config/#configuration-example)