### 接口：语音转文本
**功能描述**
创建语音转文本请求，将音频文件转换为文字。

---

**请求方法**
`POST /audio/transcriptions`

---

#### 认证鉴权
**Authorization**
- **类型**：请求头（Header）
- **格式**：Bearer `{your_token}`

---

#### 请求体（multipart/form-data）

| 参数名    | 类型               | 必填 | 说明                                                         |
| --------- | ------------------ | ---- | ------------------------------------------------------------ |
| **file**  | file               | 是   | 待识别的音频文件对象（非文件名）。<br>限制条件：<br>- 音频时长不超过 **1 小时**；<br>- 文件大小不超过 **50MB**。 |
| **model** | enum&lt;string&gt; | 是   | 对应的模型名称。<br>为提高服务质量，我们将定期调整该服务提供的模型，包括但不限于模型上线/下线及模型服务能力变更。如有可能，我们将通过公告或消息推送等方式通知您相关变更。<br><br>可选值：<br>- `FunAudioLLM/SenseVoiceSmall`<br>- `TeleAI/TeleSpeechASR`<br><br>示例：<br>`"FunAudioLLM/SenseVoiceSmall"` |

---

#### 响应
**状态码**
`200`

**响应格式**
`application/json`

**响应头**
包含 `x-siliconcloud-trace-id` 字段，作为请求的唯一追踪标识，便于日志查询与问题排查。

**响应体**
表示模型根据输入返回的转录结果。

| 字段名   | 类型   | 必填 | 说明                 |
| -------- | ------ | ---- | -------------------- |
| **text** | string | 是   | 转录得到的文本内容。 |



### 嵌入请求 API

**端点：**
`POST /v1/embeddings`

**功能：**
创建表示输入文本的嵌入向量。

---

**请求头（Headers）：**

| 字段            | 类型   | 必填 | 说明                               |
| --------------- | ------ | ---- | ---------------------------------- |
| `Authorization` | string | 是   | 认证凭证，格式为：`Bearer <token>` |
| `Content-Type`  | string | 是   | 固定为 `application/json`          |

---

**请求体（JSON Body）：**

| 字段              | 类型            | 必填 | 说明与示例                                                   |
| ----------------- | --------------- | ---- | ------------------------------------------------------------ |
| `model`           | string          | 是   | 模型名称。我们会定期调整提供的模型，包括但不限于模型上下线及能力调整，并通过公告等方式通知。可用模型列表请查看 Models。 <br> 示例：`"BAAI/bge-large-zh-v1.5"` |
| `input`           | string 或 array | 是   | 待嵌入的文本。可以是字符串或令牌数组。如需单次请求处理多个输入，可传入字符串数组或令牌数组的数组。输入长度不能超过模型的最大令牌限制，且不能为空字符串。<br><br>**各模型最大输入令牌数：**<br>- `BAAI/bge-large-zh-v1.5`、`BAAI/bge-large-en-v1.5`、`netease-youdao/bce-embedding-base_v1`：512<br>- `BAAI/bge-m3`、`Pro/BAAI/bge-m3`：8192<br>- `Qwen/Qwen3-Embedding-8B`、`Qwen/Qwen3-Embedding-4B`、`Qwen/Qwen3-Embedding-0.6B`：32768<br><br>示例：`"Silicon flow embedding online: fast, affordable, and high-quality embedding services. come try it out!"` |
| `encoding_format` | string          | 否   | 返回嵌入向量的格式。可选 `"float"` 或 `"base64"`，默认为 `"float"`。<br>示例：`"float"` |
| `dimensions`      | integer         | 否   | 指定输出嵌入向量的维度数。仅 `Qwen/Qwen3` 系列支持。<br>- `Qwen/Qwen3-Embedding-8B`：[64,128,256,512,768,1024,1536,2048,2560,4096]<br>- `Qwen/Qwen3-Embedding-4B`：[64,128,256,512,768,1024,1536,2048,2560]<br>- `Qwen/Qwen3-Embedding-0.6B`：[64,128,256,512,768,1024]<br>示例：`1024` |

---

**响应（200 OK）：**

**响应头：**
包含 `x-siliconcloud-trace-id`，用于请求追踪和问题排查。

**响应体（JSON）：**

```json
{
  "object": "list",
  "model": "模型名称",
  "data": [
    {
      // 嵌入向量数据
    }
  ],
  "usage": {
    // 请求用量信息
  }
}
```

| 字段     | 类型   | 必填 | 说明                   |
| -------- | ------ | ---- | ---------------------- |
| `object` | string | 是   | 固定为 `"list"`        |
| `model`  | string | 是   | 生成嵌入向量的模型名称 |
| `data`   | array  | 是   | 模型生成的嵌入向量列表 |
| `usage`  | object | 是   | 本次请求的用量信息     |

---

**cURL 示例：**

```bash
curl --request POST \
  --url https://api.siliconflow.cn/v1/embeddings \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "BAAI/bge-large-zh-v1.5",
  "input": "Silicon flow embedding online: fast, affordable, and high-quality embedding services. come try it out!"
}
'
```

**说明：**
请将 `<token>` 替换为你的有效访问令牌。