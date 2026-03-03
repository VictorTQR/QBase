import re
from typing import List, Dict, Any


class TextChunker:
    @staticmethod
    def split_by_semantic_boundary(text: str) -> List[str]:
        """按语义边界（标点、换行）分割"""
        sentences = re.split(r"(?<=[。！？\n])\s+", text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if not sentence.strip():
                continue
            if len(current_chunk) + len(sentence) > 500 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    @staticmethod
    def split_by_fixed_size(
        text: str, chunk_size: int = 512, chunk_overlap: int = 128
    ) -> List[str]:
        """按固定大小分割"""
        chunks = []
        i = 0

        while i < len(text):
            chunk = text[i : i + chunk_size]
            chunks.append(chunk)
            i += chunk_size - chunk_overlap

        return chunks

    @staticmethod
    def chunk(text: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """混合分块策略"""
        options = options or {}
        chunk_size = options.get("chunk_size", 512)
        chunk_overlap = options.get("chunk_overlap", 128)
        use_semantic = options.get("use_semantic", True)

        raw_chunks = []
        if use_semantic:
            semantic_chunks = TextChunker.split_by_semantic_boundary(text)
            for sem_chunk in semantic_chunks:
                if len(sem_chunk) <= chunk_size:
                    raw_chunks.append(sem_chunk)
                else:
                    raw_chunks.extend(
                        TextChunker.split_by_fixed_size(
                            sem_chunk, chunk_size, chunk_overlap
                        )
                    )
        else:
            raw_chunks = TextChunker.split_by_fixed_size(
                text, chunk_size, chunk_overlap
            )

        result = []
        current_pos = 0
        for idx, content in enumerate(raw_chunks):
            start_idx = text.find(content, current_pos)
            if start_idx == -1:
                start_idx = current_pos
            end_idx = start_idx + len(content)

            result.append(
                {
                    "content": content,
                    "index": idx,
                    "start_char": start_idx,
                    "end_char": end_idx,
                }
            )
            current_pos = end_idx - chunk_overlap

        return result
