# M16：AI 建议标签（LLM 打标，M15 增强）

2026-08-21 定稿并实施。在 M15 标签系统之上增加 LLM 建议标签能力，
修订 m15 讨论稿决策 2 中「不做 AI 建议标签」的部分——AI 只建议、
人确认，不自动写库。范围 = 独立打标配置节 [llm.tagging] + 详情页
「AI 建议标签」按钮 + 宽松清洗 + REST 端点。不做批量打标与总结后自动
建议（留待后续「批量任务」里程碑）。

---

## 0. 已定决策（讨论结论，不再开放）

1. **触发 = 仅详情页按钮**：点「AI 建议标签」同步调 LLM（秒级，
   timeout 默认 60s），按钮禁用 + 文案变「生成中…」防重复；不走
   任务系统（单次轻调用，无文件产物，任务中心没有可展示的实体）。
2. **落地 = 预填编辑器待确认**：建议合并进「编辑标签」选中值（不
   覆盖已选），新标签名补进选项，用户点「保存标签」才入库。LLM
   结果不直接写库。
3. **配置 = 独立 [llm.tagging] 节**：enabled(默认 false) / base_url /
   model / api_key_env / api_key / temperature=0.1 / max_tokens=300 /
   timeout=60 / max_input_chars=4000。可与总结用不同模型（打标输入
   短输出小，可用更快/更便宜的）。设置页新增精简卡片（只暴露
   enabled/base_url/model/api_key_env + 测试按钮，其余参数走默认值
   或 config.toml 直编）。
4. **输入 = 标题 + 内容 + 已有标签**：内容复用总结的来源选择
   （get_summary_input_text：音频/视频取转录、文档取解析/原文），
   截断 max_input_chars（默认 4000）；全库现有标签列表随 prompt
   下发，引导复用避免同义标签 proliferation。
5. **输出 = JSON 字符串数组，宽容解析**：3-8 个、单个 ≤10 字符、
   中文为主；解析剥 markdown fence、截取首个 [ 到末个 ] 后
   json.loads，失败抛 RuntimeError("AI 返回格式异常，请重试")。
6. **清洗 = 宽松丢弃而非报错**：strip、丢空/含半角逗号/>30 字符、
   去重保序、截到 MAX_TAGS_PER_ASSET；清洗后为空时 UI 提示
   「AI 未返回可用标签」。
7. **范围外（明确不做）**：批量打标、总结任务完成后自动建议、
   建议历史留存、标签置信度展示、流式输出。

---

## 1. 现状事实（代码依据）

```text
llm_service.chat_completion    通用 OpenAI 兼容调用（httpx 同步，
                               temperature/max_tokens/timeout 走 config
                               dict），可直接复用
llm_service 提示词             模块级中文常量；无 JSON 输出先例
summarization_service
  .get_summary_input_text      总结输入来源选择：音频/视频→active 转录，
                               .md/.txt→原文，其他可解析文档→parsed
                               artifact；无输入抛中文 ValueError
config_service                 [llm.summary] 读取/校验/掩码/密钥状态/
                               连通性测试（_test_llm_connection 固定读
                               summary 节）；API key 经 api_key_env 走
                               环境变量或 secrets.toml
asset_detail.py 标签区（m15）  编辑器 ui.select(add-unique) + 保存按钮
                               → tag_service.set_asset_tags（io_bound）；
                               无 spinner 先例，按钮 disable + notify 是
                               通用等待反馈
tasks 系统                      总结走后台线程 + tasks 行；打标无文件
                               产物，不适配该模型
```

## 2. 实施蓝图

### 2.1 `app/services/llm_service.py`

```text
TAGGING_SYSTEM_PROMPT            中文系统提示（决策 5 的标签规范）
_parse_tag_list(raw)             宽容解析：strip → 去 ```fence → 截取
                                 [...] → json.loads；非字符串数组/失败
                                 抛 RuntimeError("AI 返回格式异常，请重试")
suggest_tags(title, text,
             existing_tags, config)
                                 user 内容 = 标题 + 已有标签 + 内容
                                 （截断 max_input_chars）→ chat_completion
                                 → _parse_tag_list；空内容抛 ValueError
```

### 2.2 `app/services/tag_service.py`

```text
_clean_suggestions(names)        宽松清洗（决策 6）
suggest_asset_tags(asset_id)     校验资产存在 → get_tagging_llm_config
                                 （未启用抛 ValueError("AI 打标未启用，
                                 请前往设置页开启")）→ 复用
                                 get_summary_input_text 取文本（沿用其
                                 报错如「请先生成转录」）→ list_tags 取
                                 现有标签 → llm_service.suggest_tags →
                                 清洗返回；全程不写库
```

### 2.3 `app/services/config_service.py`

```text
get_tagging_llm_config()         仿 get_summary_llm_config；enabled 时
                                 校验 base_url/model/api_key（中文报错）
validate_config                  增加 llm.tagging 块（启用时 base_url/
                                 model 非空、max_tokens/timeout/
                                 max_input_chars > 0）
_mask_api_keys / get_key_status /
has_plain_api_key                覆盖 llm.tagging 节
_test_llm_connection(section,
                     label)      参数化（原固定读 summary）；test_connection
                                 增加 kind="llm_tagging"
```

### 2.4 `app/services/library_service.py`

```text
DEFAULT_LIBRARY_CONFIG           追加 [llm.tagging] 节（enabled=false +
                                 注释，默认值同决策 3；老库不迁移，
                                 未生成节时读默认值）
```

### 2.5 `app/api/library.py` + `app/api/settings.py`

```text
POST /api/assets/{id}/suggest-tags
                                 → {"suggestions": [...]}；400 未开库/
                                 ValueError（未启用、无输入文本），
                                 404 资产不存在，502 LLM 调用/解析失败
POST /api/settings/test-connection
                                 kind 白名单增加 llm_tagging
```

### 2.6 `app/ui/pages/asset_detail.py`

```text
「AI 建议标签」按钮              保存按钮旁，icon auto_awesome；点击
                                 后两按钮 disable + 文案变「生成中…」
                                 → io_bound(suggest_asset_tags) → 建议
                                 并入编辑器选中值（不覆盖已选）、新名
                                 补进 options → notify「已填入 N 个
                                 建议标签，确认后保存」→ 恢复按钮；
                                 异常 notify_error（未启用/无转录等
                                 中文提示）；不做预置 disable
```

### 2.7 `app/ui/pages/settings.py`

```text
「AI 打标配置」卡片              LLM 总结卡之后；字段 = 启用 switch /
                                 Base URL / Model / api_key_env + 密钥
                                 状态 + 「测试打标 API」按钮；说明文案
                                 注明其余参数默认值与 config.toml 直编
build_patch                      llm 下增加 tagging 子 patch（仅 UI
                                 暴露的四键，deep merge 保留其余）
handle_test_tagging              test_connection("llm_tagging", patch)
```

### 2.8 零改动确认

tag_repository、asset_repository、search_service、assets/search 列表
筛选、数据库 schema、任务系统、转录/总结/解析服务均不动；M15 全部
既有行为不变；LLM 总结链路与 [llm.summary] 行为不变。

## 3. 测试步骤（开发人员手动执行）

```text
1. 设置页 AI 打标卡：未启用时填好字段保存 → 详情页点「AI 建议标签」
   → 提示「AI 打标未启用，请前往设置页开启」
2. 设置页启用 + 填 mock/真实端点 → 「测试打标 API」通过；保存后
   config.toml 出现 [llm.tagging] enabled=true
3. 详情页点「AI 建议标签」→ 按钮变「生成中…」→ 建议合并进编辑器
   （已手选标签不被覆盖、新标签补进选项）→ notify 提示 → 点
   「保存标签」入库，徽章刷新
4. 音频无转录时点击 → 提示需先生成转录；LLM 返回非 JSON → 提示
   「AI 返回格式异常，请重试」；返回含逗号/超长标签 → 被丢弃，
   其余正常入库
5. 回车/清空编辑器后再次建议 → 不产生重复标签；手动流程与 M15 一致
6. API：POST /api/assets/{id}/suggest-tags 各错误码；GET /api/settings
   中 llm.tagging.api_key 已掩码
7. 回归：LLM 总结、打标未启用时的 M15 全部行为不变
```

## 4. M16 验收标准

对应 PRD §29.16（新增）：

```text
详情页「AI 建议标签」生成建议并预填编辑器，确认保存后才入库
独立 [llm.tagging] 配置：未启用给中文提示；设置页可编辑并测试连通
建议经宽松清洗（去空/含逗号/超长/去重），不覆盖已选标签
AI 打标不写库、不产生任务与文件；M15 手动打标行为完全不变
```

## 5. PRD 同步清单（实施完成时）

```text
§3 / §31 注记：AI 建议标签已由 m16 实现（修订 m15 决策），批量打标仍不做
§11.2 详情页增「AI 建议标签」按钮描述
§20 配置设计增 [llm.tagging] 节说明
§22.3 / §22.6 设置页增 AI 打标卡片
§23.2 增 POST /api/assets/{id}/suggest-tags；§23.5 测试连通 kind 增 llm_tagging
§28 增 M16；§29 增 29.16
README / CLAUDE.md 功能描述同步
```
