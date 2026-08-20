# M10：EPUB 内容索引（内置本地解析器）

2026-08-21 定稿。对应 PRD §31 后续阶段规划第 1 项「EPUB 内容索引
（MinerU 不支持 epub，需接入其他解析器）」。复用 M9 的解析器抽象与
`{stem}.parsed.md` 全链路，新增一个零依赖的本地 provider。

---

## 0. 已定决策（讨论结论，不再开放）

1. **选型 = 手写 zipfile 解析，标准库 only，不引 ebooklib**。
   epub 本质是「zip 容器 + XML 清单 + XHTML 内容」（见 §1），文本提取只需
   container.xml → OPF spine 顺序读 XHTML，标准库（zipfile / ElementTree /
   html.parser）完全够用；ebooklib 会引入 lxml 依赖，违背项目零新增依赖
   原则（M9 同款理由：HTTP 用已有 httpx，解压用标准库）。
2. **路由 = 按扩展名固定路由**。`.epub` → 内置本地解析器 `epub`
   （不看 `[parse].provider`，无需 token）；其余白名单（pdf/office）→
   `[parse].provider`（现 mineru）。理由：现实只有一个远端 provider（mineru，
   不支持 epub）和一个本地 provider，做通用 provider 映射表是过度设计。
   `epub` 同时注册进 PARSERS，预留 `[parse].provider = "epub"` / `[parse.epub]`
   配置位。
3. **产物完全对齐 M9**：`{stem}.parsed.md` 平铺 sidecar，扫描/全文索引/向量
   索引/AI 总结输入切换全部自动复用，扫描层与索引层零改动。
4. **接口适配 = 对三阶段抽象的最小扩展**：
   - `submit` = 结构校验（zip 可开、有 container.xml、OPF、spine 可解析），
     `files` 携带源文件绝对路径（随 submission 持久化进 params_json，
     重启恢复凭据）；
   - `poll` = 源文件存在即 `done`，`full_zip_url = "local://<绝对路径>"`
     （parse_service 轮询循环零改动，local:// 只是取回指针不是 HTTP）；
   - `fetch` = 从源文件**现算** Markdown（本地解析秒级、幂等、无状态，
     重启后无需远端状态即可重算，天然恢复安全）；
   - `base.py` 新增抽象方法 `to_markdown(raw: bytes) -> str`（产物字节 →
     markdown 文本）：MinerU 实现即原 parse_service._extract_full_md（挪入
     mineru_parser），epub 实现为 utf-8 解码（fetch 产物本身就是 markdown）；
   - 产物留档：新增类属性 `PRODUCT_BACKUP_SUFFIX`，mineru = `".zip"` 继续
     留档 backups/，epub = None（产物即 md 文本，覆盖重解析已有 `.bak.md`
     留档，不重复备份）；
   - `MAX_FILE_BYTES` 从 mineru_parser 模块常量改为 `MineruParser` 类属性
     `max_file_bytes`（200MB 是 MinerU 的限制；本地解析不设上限）。
5. **XHTML→Markdown 映射（够用就好，不做高保真）**：
   - 标题 h1-h6 → `#`~`######`；p/div 等块级 → 段落；br → 换行
   - li → `- `（嵌套列表按层级缩进两空格）；pre → 围栏代码块
   - blockquote → `> ` 前缀；hr → `---` 分隔线
   - 行内：b/strong → `**`、em/i → `*`、code → 反引号；a → 只留链接文字
     （epub 相对 href 在 QBase 中是断链，保留文字即可）
   - table 简化：一行文本，单元格 ` | ` 连接（epub 表格通常简单，够搜索/总结用）
   - 忽略 head/script/style/svg/img（图片不落盘，与 M9 决策一致）
   - 章节按 OPF spine 顺序拼接（spine 才是标准阅读顺序，不用 TOC nav/ncx）；
     spine 为空的畸形书回退：全部 xhtml/html 按 zip 内路径排序
6. **编码与路径**：XHTML 解码按 BOM / XML 声明探测，回退 utf-8(errors=replace)；
   OPF href 做百分号解码（`%20` 空格）后按 zip 路径匹配。
7. **DRM 明确拒绝**：检测到 `META-INF/encryption.xml` 即报错
   「加密（DRM）epub 不支持解析」，不做解密。
8. **UI**：`.epub` 并入 `PARSEABLE_EXTENSIONS`（详情页解析卡片 / AI 总结卡片
   / 总结输入切换自动覆盖）；详情页 `parse_ready` 校验改为「按扩展名实例化
   解析器」（epub 免 token，mineru 缺 token 时 ValueError 文案直接展示）；
   解析卡片文案区分本地（秒级）/远端（1-5 分钟）；设置页补一行说明。
9. **范围外（明确不做）**：图片/封面提取落盘、字体/样式还原、数学公式与
   复杂表格高保真、DRM 解密、MOBI/AZW3 等其他电子书格式。

---

## 1. EPUB 格式要点（事实备查）

EPUB（OPF 规范，http://www.idpf.org/epub/301/）：

```text
epub 文件 = zip 容器
├── mimetype                 固定内容 "application/epub+zip"（必须首文件且不压缩，
│                            校验它过严，实现不检查）
├── META-INF/container.xml   指向 OPF 包文件：
│                             <rootfile full-path="OEBPS/content.opf"
│                                       media-type="application/oebps-package+xml"/>
├── OEBPS/content.opf        清单 + 书架（命名空间 http://www.idpf.org/2007/opf）
│   ├── <manifest><item id=... href=... media-type="application/xhtml+xml"/></manifest>
│   └── <spine><itemref idref=.../></spine>     阅读顺序 = itemref 出现顺序
└── OEBPS/chapter1.xhtml ... spine 引用的内容文件
```

注意：

```text
href 相对 OPF 所在目录，可能含百分号编码（空格 %20），需 unquote
XHTML 编码绝大多数 utf-8，少数老书 latin-1 / utf-16（XML 声明可探）
加密书（DRM）带 META-INF/encryption.xml，含 <EncryptedData> 条目
EPUB3 与 EPUB2 差异（nav.xhtml vs toc.ncx）只影响目录，不影响 spine 顺序
```

零新增依赖：zipfile / xml.etree.ElementTree / html.parser / re / posixpath
全为标准库。

---

## 2. 实施蓝图

### 2.1 `app/services/parsers/base.py`（最小扩展）

```python
class DocumentParser(ABC):
    name: str = ""
    # 产物留档后缀：None = 产物不单独留档（epub 产物即 md 文本）
    PRODUCT_BACKUP_SUFFIX: str | None = None
    # 单文件大小上限：None = 不限制（200MB 是 MinerU 的限制，不是解析层的）
    max_file_bytes: int | None = None

    @abstractmethod
    def submit(self, paths) -> ParseSubmission: ...
    @abstractmethod
    def poll(self, submission) -> list[ParseFileState]: ...
    @abstractmethod
    def fetch(self, state) -> bytes: ...
    @abstractmethod
    def to_markdown(self, raw: bytes) -> str:
        """产物原始字节 → markdown 文本（MinerU 从 zip 提 full.md，本地解析器直接解码）。"""
```

### 2.2 `app/services/parsers/epub_parser.py`（新增）

```python
class EpubParser(DocumentParser):
    name = "epub"
    # submit：_validate_epub(path) 结构校验；files=[{name, path(绝对)}]
    # poll：源文件在 → done + full_zip_url=f"local://{path}"；不在 → failed
    # fetch：strip local:// 前缀 → _epub_to_markdown(path) → utf-8 字节
    # to_markdown：raw.decode("utf-8", errors="replace")
```

核心函数 `_epub_to_markdown(path) -> str`：

```text
zipfile 打开
  ├─ 检测 META-INF/encryption.xml → 拒绝（DRM）
  ├─ container.xml → OPF 路径（media-type=application/oebps-package+xml）
  ├─ OPF → manifest(id → href) + spine(idref 顺序)；href unquote + normpath
  ├─ spine 为空 → 回退全部 .xhtml/.html/.htm 按路径排序
  └─ 逐文件 _xhtml_to_markdown，非空章节 "\n\n" 拼接
```

`_xhtml_to_markdown(data: bytes) -> str`：`html.parser.HTMLParser` 子类
流式提取（`convert_charrefs=True` 处理实体），映射见 §0 决策 5；收尾
`\xa0`→空格、3+ 连续空行折叠为 2。

### 2.3 `app/services/parsers/mineru_parser.py`

- `to_markdown` = 原 `parse_service._extract_full_md`（zip 内找 full.md）原样挪入；
- `PRODUCT_BACKUP_SUFFIX = ".zip"`；`max_file_bytes = MAX_FILE_BYTES`（模块常量保留作定义处）。

### 2.4 `app/services/parsers/__init__.py`

- 注册 `EpubParser`；新增路由函数：

```python
def get_parser_for_extension(config: dict, ext: str) -> DocumentParser:
    """.epub 固定走内置本地解析器；其余走 [parse].provider。"""
```

### 2.5 `app/services/parse_service.py`

```text
PARSEABLE_EXTENSIONS += ".epub"
start_parsing：enabled 校验后按扩展名实例化解析器（epub 免 token）；
              大小上限按 parser.max_file_bytes（None 跳过），报错文案不写死 MinerU
run_parse_task：parser 改按扩展名路由；md_text = parser.to_markdown(raw)；
              产物留档按 PRODUCT_BACKUP_SUFFIX（None 跳过）
```

### 2.6 UI

```text
asset_detail.py：parse_ready 改为 get_parser_for_extension(config, ext)
                实例化探测（ValueError 文案直接展示）；
                文案：epub「本地解析为 Markdown（内置解析器，无需远端服务，
                通常数秒完成）」，其余维持 MinerU 文案
settings.py：解析配置卡片补一行「.epub 由内置本地解析器处理，
            无需 MinerU token」
```

### 2.7 配置模板（library_service.DEFAULT_LIBRARY_CONFIG）

`[parse]` 注释补一句 epub 本地路由说明（无新配置键）。

---

## 3. 测试步骤（开发人员手动执行）

```text
1. 准备一本真实 .epub 放入库目录，扫描后进入资产详情页
2. 「文档解析」卡片可见且可点（未配置 MinerU token 也可点），
   文案为本地解析；点「生成解析」→ 任务中心出现 parse 任务，数秒内 success
3. 源文件旁生成 {stem}.parsed.md；详情页派生文件出现「解析结果」tab，
   内容为按章节顺序的 Markdown（标题/列表/引用结构保留）
4. 重新解析 → 旧 parsed.md 备份为 .knowledge/backups/{stem}.{ts}.bak.md，
   且不产生 .zip 留档
5. 全文搜索命中 epub 内容；向量索引统计 sources/chunks 增加
6. AI 总结卡片：未解析时提示需先解析；解析后可总结，输入为 parsed.md
7. 异常路径：把 .epub 改成假 zip（如 txt 改后缀）→ 任务失败，
   错误信息指明「不是合法 epub」；删除源文件后重试 → 「源文件不存在」
8. 重启恢复：解析进行中重启应用（本地秒级，可用大书或断点模拟）→
   任务恢复并成功（epub 路径 fetch 现算，无远端状态依赖）
```

## 4. M10 验收标准

对应 PRD §29.10 增补：

```text
.epub 资产可在详情页发起解析（无需远端 token），生成 {stem}.parsed.md
解析产物进入全文/向量索引，AI 总结输入为解析结果
DRM / 损坏 epub 给出明确失败原因，任务可重试
覆盖重解析时旧结果自动备份
```

## 5. PRD 同步清单（实施完成时）

```text
§13.2 总结输入：白名单文档（含 epub）
§15.2 解析策略：.epub 移入可解析（本地解析器）
§15.3 解析器抽象：to_markdown / PRODUCT_BACKUP_SUFFIX / 按扩展名路由 / epub provider
§20 配置示例：[parse] 注释
§21.2 模块树：parsers/epub_parser.py
§28 里程碑：增 M10；§29.10 验收增补；§31 移除「EPUB 内容索引」；§35 顺序
```

---

## 附录 A：合成 epub + 端到端验证脚本

无 UI 环境验证全链路（解析 → parsed.md → FTS 索引）。在仓库根目录以
`uv run python <脚本>` 运行，验证后删除（2026-08-21 实际执行，全部通过）：

```python
"""M10 验证：合成 epub（EPUB3/EPUB2/latin-1/坏 zip/DRM）+ parse_service 全链路。"""
import shutil
import sys
import time
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from app.services.parsers.epub_parser import EpubParser

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

OPF = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>合成测试书</dc:title>
  </metadata>
  <manifest>
    <item id="c1" href="chapter%201.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="c2"/>
    <itemref idref="c1"/>
  </spine>
</package>"""

CH1 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>第一章</title></head>
<body><h1>第一章&nbsp;起点</h1><p>第一个<em>章节</em>段落。</p>
<ul><li>要点一</li><li>要点二</li></ul>
<pre><code>x = 1</code></pre>
<blockquote><p>引用内容。</p></blockquote>
<table><tr><td>甲</td><td>乙</td></tr></table>
</body></html>"""

CH2 = (
    '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
    "<h1>第二章</h1><p>第二章正文。</p></body></html>"
)

# EPUB2 风格：OPF 2.0 + toc.ncx + 内容在子目录 + latin-1 编码声明
OPF2 = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="c1" href="text/ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx"><itemref idref="c1"/></spine>
</package>"""

CH1_LATIN1 = (
    '<?xml version="1.0" encoding="iso-8859-1"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
    "<h1>Café</h1><p>café au lait</p></body></html>"
).encode("latin-1")


def build_epub(path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", CONTAINER)
        zf.writestr("OEBPS/content.opf", OPF)
        zf.writestr("OEBPS/chapter 1.xhtml", CH1)  # href 带空格（OPF 侧百分号编码）
        zf.writestr("OEBPS/chapter2.xhtml", CH2)


def build_epub2(path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", CONTAINER)
        zf.writestr("OEBPS/content.opf", OPF2)
        zf.writestr("OEBPS/toc.ncx", "<ncx/>")
        zf.writestr("OEBPS/text/ch1.xhtml", CH1_LATIN1)


def main():
    tmp = Path("_m10_tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    epub = tmp / "测试书.epub"
    build_epub(epub)

    # 三阶段直测
    parser = EpubParser({})
    submission = parser.submit([epub])
    states = parser.poll(submission)
    assert states[0].state == "done"
    md = parser.to_markdown(parser.fetch(states[0]))

    assert md.index("第二章") < md.index("第一章"), "spine 顺序错误"
    assert "# 第一章 起点" in md          # 标题 + &nbsp; 实体
    assert "- 要点一" in md and "- 要点二" in md
    assert "*章节*" in md                  # 斜体
    assert "```" in md and "x = 1" in md   # pre 内不套行内记号
    assert "> 引用内容。" in md
    assert "甲 | 乙" in md

    # EPUB2 + latin-1 + 子目录
    epub2 = tmp / "old.epub"
    build_epub2(epub2)
    parser2 = EpubParser({})
    sub2 = parser2.submit([epub2])
    md2 = parser2.to_markdown(parser2.fetch(parser2.poll(sub2)[0]))
    assert "# Café" in md2 and "café au lait" in md2

    # 异常路径
    (tmp / "fake.epub").write_text("not a zip", encoding="utf-8")
    try:
        EpubParser({}).submit([tmp / "fake.epub"])
        raise AssertionError
    except ValueError:
        pass
    with zipfile.ZipFile(tmp / "drm.epub", "w") as zf:
        zf.writestr("META-INF/encryption.xml", "<encryption/>")
    try:
        EpubParser({}).submit([tmp / "drm.epub"])
        raise AssertionError
    except ValueError:
        pass

    # 全链路：parse_service（MinerU 未配 token，epub 必须仍可解析）
    from app import state as app_state
    from app.database import get_conn, init_db
    from app.repositories import asset_repository, task_repository
    from app.services.library_service import DEFAULT_LIBRARY_CONFIG
    from app.services.parse_service import start_parsing

    kb = tmp / "kb"
    kb.mkdir()
    (kb / ".knowledge").mkdir()
    config = DEFAULT_LIBRARY_CONFIG.replace(
        'enabled = false\nprovider = "mineru"',
        'enabled = true\nprovider = "mineru"',
    )
    (kb / ".knowledge" / "config.toml").write_text(config, encoding="utf-8")
    app_state.state.library_root = kb
    init_db(kb / ".knowledge" / "db.sqlite")

    shutil.copy(epub, kb / "测试书.epub")
    conn = get_conn(kb / ".knowledge" / "db.sqlite")
    asset_id = asset_repository.upsert_asset(
        conn,
        {
            "title": "测试书",
            "relative_path": "测试书.epub",
            "absolute_path": str(kb / "测试书.epub"),
            "type": "document",
            "size": epub.stat().st_size,
            "mtime": 1,
            "parse_status": "pending",
        },
    )
    conn.commit()

    def wait_task(task_id):
        for _ in range(100):
            task = task_repository.get_task(conn, task_id)
            if task["status"] in {"success", "failed"}:
                return task
            time.sleep(0.2)
        raise AssertionError("任务超时未结束")

    task = wait_task(start_parsing(asset_id))
    assert task["status"] == "success", task["error"]

    parsed = kb / "测试书.parsed.md"
    assert parsed.exists()
    rows = conn.execute(
        "SELECT count(*) FROM chunks WHERE relative_path LIKE '%parsed%'"
    ).fetchone()
    assert rows[0] > 0, "解析结果未进索引"

    backups = kb / ".knowledge" / "backups"
    assert not list(backups.glob("*.zip")), "epub 不应产生 zip 留档"

    task2 = wait_task(start_parsing(asset_id))  # 覆盖重解析
    assert task2["status"] == "success"
    assert list(backups.glob("*.bak.md")), "覆盖备份未生成"

    conn.close()
    print("全部通过 ✔")


if __name__ == "__main__":
    main()
```

实际输出要点（2026-08-21）：

```text
EPUB3 产物片段（spine 顺序 第二章 在前；实体/列表/斜体/代码块/引用/表格均正确）：
  # 第二章 / 第二章正文。 / # 第一章 起点 / 第一个*章节*段落。 /
  - 要点一 / ```x = 1``` / > 引用内容。 / 甲 | 乙
EPUB2/latin-1 产物：'# Café\n\ncafé au lait'
坏 zip：「不是合法 epub（无法作为 zip 打开）」
DRM：「加密（DRM）epub 不支持解析」
全链路：任务 success；parsed.md 166 bytes；FTS chunks 1；
       backups/ 无 .zip；覆盖重解析生成 测试书.parsed.2026xxxx.bak.md
```
