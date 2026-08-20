"""EPUB 本地解析器（m10，MinerU 不支持 epub）。

epub = zip 容器：container.xml → OPF（manifest + spine）→ 按阅读顺序的
XHTML 内容。解析完全本地、幂等、秒级，无远端状态：

- submit：结构校验（zip 可开 / container.xml / OPF / spine），files 携带
  源文件绝对路径（随 submission 持久化进任务 params_json，重启恢复凭据）
- poll：源文件存在即 done，full_zip_url 用 local:// 伪协议指向源文件
  （只是取回指针，不是 HTTP；parse_service 轮询循环零改动）
- fetch：从源文件现算 Markdown（utf-8 字节），无状态可丢，重启后重算即可
- to_markdown：直接解码（fetch 的产物本身就是 markdown）

标准库 only（zipfile / ElementTree / html.parser），不引 ebooklib。
"""

from __future__ import annotations

import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

from app.services.parsers.base import (
    DocumentParser,
    ParseFileState,
    ParseSubmission,
)

CONTAINER_ENTRY = "META-INF/container.xml"
ENCRYPTION_ENTRY = "META-INF/encryption.xml"
NS_CONTAINER = "{urn:oasis:names:tc:opendocument:xmlns:container}"
NS_OPF = "{http://www.idpf.org/2007/opf}"
CONTENT_MEDIA_TYPE = "application/oebps-package+xml"
LOCAL_URL_PREFIX = "local://"


class EpubParser(DocumentParser):
    name = "epub"

    def __init__(self, config: dict):
        # 本地解析无必配项，config 预留 [parse.epub] 位置
        self.config = config if isinstance(config, dict) else {}

    def submit(self, paths: list[Path]) -> ParseSubmission:
        if len(paths) != 1:
            raise ValueError("本地解析一次只处理一个文件（一资产一任务）")

        path = paths[0].resolve()

        # 结构问题在提交时即暴露（而不是任务跑起来才失败）
        _spine_paths(path)

        return ParseSubmission(
            batch_id=f"local:{path}",
            files=[{"name": path.name, "path": str(path)}],
        )

    def poll(self, submission: ParseSubmission) -> list[ParseFileState]:
        info = submission.files[0] if submission.files else {}
        path = Path(str(info.get("path") or ""))

        if not path.is_file():
            return [
                ParseFileState(
                    name=str(info.get("name", "")),
                    state="failed",
                    err_msg=f"源文件不存在：{path}",
                )
            ]

        return [
            ParseFileState(
                name=str(info.get("name", "")),
                state="done",
                full_zip_url=f"{LOCAL_URL_PREFIX}{path}",
            )
        ]

    def fetch(self, state: ParseFileState) -> bytes:
        if not state.full_zip_url or not state.full_zip_url.startswith(
            LOCAL_URL_PREFIX
        ):
            raise ValueError("该文件没有可解析的本地路径")

        path = Path(state.full_zip_url[len(LOCAL_URL_PREFIX) :])
        md = _epub_to_markdown(path)

        return md.encode("utf-8")

    def to_markdown(self, raw: bytes) -> str:
        return raw.decode("utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────────────────
# epub 结构解析
# ──────────────────────────────────────────────────────────────────────────


def _spine_paths(epub_path: Path) -> list[str]:
    """打开 epub，返回按 spine 阅读顺序的内容文件 zip 路径。

    结构问题（缺 container.xml / OPF、DRM 加密、坏 zip）在此抛 ValueError。
    """
    try:
        zf = zipfile.ZipFile(epub_path)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"不是合法 epub（无法作为 zip 打开）：{exc}") from exc

    with zf:
        names = set(zf.namelist())

        if ENCRYPTION_ENTRY in names:
            raise ValueError("加密（DRM）epub 不支持解析")

        try:
            container = ET.fromstring(zf.read(CONTAINER_ENTRY))
        except KeyError:
            raise ValueError(
                f"不是合法 epub（缺少 {CONTAINER_ENTRY}）"
            ) from None

        opf_path = next(
            (
                (node.get("full-path") or "").strip()
                for node in container.iter(f"{NS_CONTAINER}rootfile")
                if node.get("media-type") == CONTENT_MEDIA_TYPE
                and (node.get("full-path") or "").strip()
            ),
            None,
        )

        if not opf_path:
            raise ValueError("container.xml 未声明 OPF 路径")

        try:
            opf = ET.fromstring(zf.read(opf_path))
        except KeyError:
            raise ValueError(f"OPF 文件不存在：{opf_path}") from None

        base_dir = posixpath.dirname(opf_path)
        manifest: dict[str, str] = {}

        for item in opf.iter(f"{NS_OPF}item"):
            item_id = item.get("id")
            href = unquote((item.get("href") or "").strip())

            if item_id and href:
                joined = posixpath.join(base_dir, href) if base_dir else href
                manifest[item_id] = posixpath.normpath(joined)

        spine = [
            manifest[itemref.get("idref")]
            for itemref in opf.iter(f"{NS_OPF}itemref")
            if itemref.get("idref") in manifest
        ]

        if not spine:
            # 畸形书回退：全部内容文件按 zip 内路径排序
            spine = sorted(
                name
                for name in names
                if name.lower().endswith((".xhtml", ".html", ".htm"))
            )

        if not spine:
            raise ValueError("epub 中没有任何 XHTML 内容文件")

        return [href for href in spine if href in names]


def _epub_to_markdown(epub_path: Path) -> str:
    """epub → markdown：spine 顺序逐章转换，非空章节以空行拼接。"""
    with zipfile.ZipFile(epub_path) as zf:
        chapters = []

        for href in _spine_paths(epub_path):
            try:
                data = zf.read(href)
            except KeyError:
                continue  # spine 引用了清单里不存在的条目，跳过

            text = _xhtml_to_markdown(data).strip()

            if text:
                chapters.append(text)

    if not chapters:
        raise ValueError("epub 没有可提取的文本内容")

    return "\n\n".join(chapters)


# ──────────────────────────────────────────────────────────────────────────
# XHTML → Markdown
# ──────────────────────────────────────────────────────────────────────────

_ENCODING_DECL = re.compile(
    rb"""encoding\s*=\s*["']([A-Za-z0-9_.:-]+)["']"""
)


def _decode_xhtml(data: bytes) -> str:
    """BOM / XML 声明探测编码，回退 utf-8(errors=replace)。"""
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")

    match = _ENCODING_DECL.search(data[:256])

    if match:
        try:
            return data.decode(match.group(1).decode("ascii"), errors="replace")
        except (LookupError, UnicodeDecodeError):
            pass

    return data.decode("utf-8", errors="replace")


class _MarkdownExtractor(HTMLParser):
    """流式提取 XHTML 文本并映射为 markdown（映射表见 m10 讨论稿 §0 决策 5）。

    行内成对标签（b/strong/em/i/code、h1-h6）用哨兵占位，闭合时回取区间
    文本包上 markdown 记号；head/script/style/svg 整体跳过。
    """

    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    INLINE_MARKS = {"b": "**", "strong": "**", "em": "*", "i": "*", "code": "`"}
    SKIP_TAGS = {"head", "script", "style", "svg", "title"}
    # 结束时补空行的块级标签
    BLOCK_TAGS = {
        "p", "div", "section", "article", "header", "footer", "main",
        "aside", "figure", "figcaption", "ul", "ol", "dl", "dt", "dd",
        "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "table",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts: list = []  # str 或哨兵
        self._skip_depth = 0
        self._pre_depth = 0
        self._quote_depth = 0
        self._list_depth = 0

    # ── 输出工具 ──

    def _emit(self, text: str) -> None:
        if self._skip_depth == 0 and text:
            self._parts.append(text)

    def _emit_break(self) -> None:
        """块级分隔：引用内保持 > 前缀，其余空行分段。"""
        if self._skip_depth:
            return

        if self._quote_depth and not self._pre_depth:
            self._parts.append("\n> ")
        else:
            self._parts.append("\n\n")

    def _pop_marked(self, mark: str) -> str:
        """回取最近一个哨兵之后的文本并移除哨兵。"""
        try:
            index = self._parts.index(mark)
        except ValueError:
            return ""

        text = "".join(
            part for part in self._parts[index + 1 :] if isinstance(part, str)
        )
        del self._parts[index:]

        return text.strip()

    # ── 标签处理 ──

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth:
            return

        if tag == "pre":
            self._pre_depth += 1
            self._emit("\n```\n")
        elif tag in self.HEADING_TAGS:
            self._parts.append(f"<h:{tag}>")
        elif tag in self.INLINE_MARKS:
            if not self._pre_depth:  # pre 内保留原文，不套行内记号
                self._parts.append(f"<i:{tag}>")
        elif tag == "li":
            indent = "  " * max(0, self._list_depth - 1)
            self._emit(f"\n{indent}- ")
        elif tag in {"ul", "ol", "dl"}:
            self._list_depth += 1
        elif tag == "blockquote":
            self._quote_depth += 1
            if self._quote_depth == 1:
                self._emit("> ")
        elif tag == "br":
            self._emit("\n")
        elif tag == "hr":
            self._emit("\n\n---\n\n")
        elif tag in {"tr"}:
            pass  # 行分隔在单元格结束时统一处理
        elif tag in {"td", "th"}:
            pass

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if self._skip_depth:
            return

        if tag == "pre":
            self._pre_depth = max(0, self._pre_depth - 1)
            self._emit("\n```\n\n")
        elif tag in self.HEADING_TAGS:
            level = int(tag[1])
            text = self._pop_marked(f"<h:{tag}>")
            self._parts.append(f"\n\n{'#' * level} {text}\n\n")
        elif tag in self.INLINE_MARKS:
            if self._pre_depth:
                return

            mark = self.INLINE_MARKS[tag]
            text = self._pop_marked(f"<i:{tag}>")

            if text:
                self._parts.append(f"{mark}{text}{mark}")
        elif tag in {"ul", "ol", "dl"}:
            self._list_depth = max(0, self._list_depth - 1)
            self._emit_break()
        elif tag == "blockquote":
            self._quote_depth = max(0, self._quote_depth - 1)
            self._emit_break()
        elif tag in {"td", "th"}:
            self._emit(" | ")
        elif tag == "tr":
            self._emit("\n\n")
        elif tag in self.BLOCK_TAGS:
            self._emit_break()

    def handle_startendtag(self, tag: str, attrs) -> None:
        # 自闭合标签（xhtml 常见 <br/> <hr/>）走 starttag 即可
        if tag in self.SKIP_TAGS:
            return

        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self._pre_depth:
            self._parts.append(data)  # pre 内保留原始空白
        else:
            self._emit(data)

    def result(self) -> str:
        text = "".join(p for p in self._parts if isinstance(p, str))
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+\n", "\n", text)  # 行尾空白
        text = re.sub(r"^>\s*$", "", text, flags=re.MULTILINE)  # 引用块空行残留
        text = re.sub(r"\|[ \t]*$", "", text, flags=re.MULTILINE)  # 表格行尾分隔符
        text = re.sub(r"\n{3,}", "\n\n", text)  # 折叠连续空行

        return text.strip()


def _xhtml_to_markdown(data: bytes) -> str:
    extractor = _MarkdownExtractor()
    extractor.feed(_decode_xhtml(data))
    extractor.close()

    return extractor.result()
