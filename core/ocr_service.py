"""
OCR 识别模块 - 基于 Chandra (Qwen3VL 视觉语言模型)

使用本地 GPU + HuggingFace 推理，将发票图片转换为文本行。
"""

import re

_engine = None


def get_engine():
    """懒加载 Chandra InferenceManager（全局单例）"""
    global _engine
    if _engine is None:
        from chandra.model import InferenceManager
        _engine = InferenceManager(method="hf")
    return _engine


def recognize_texts(image) -> list[str]:
    """
    对 PIL.Image 进行 OCR，返回纯文本行列表。

    Args:
        image: PIL.Image.Image（RGB）

    Returns:
        识别出的文本行列表，如 ["16A 插座 4 15 60", ...]
    """
    from chandra.model.schema import BatchInputItem

    manager = get_engine()
    batch = BatchInputItem(image=image, prompt_type="ocr")
    result = manager.generate([batch])[0]

    if result.error:
        return []

    # 从 markdown 中提取纯文本行
    lines = _extract_text_lines(result.markdown)
    return lines


def _extract_text_lines(markdown: str) -> list[str]:
    """
    从 Chandra 输出的 Markdown 中提取有意义的纯文本行。
    去除 HTML 标签、表格分隔线、空行等噪声。
    """
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', markdown)

    # 按行分割并清理
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        # 跳过空行
        if not line:
            continue
        # 跳过 Markdown 标题标记
        if line.startswith('#'):
            continue
        # 跳过纯分隔线
        if re.match(r'^[\-\*\_=]{3,}$', line):
            continue
        # 跳过 Markdown 表格分隔行 (|---|---|)
        if re.match(r'^\|[\s\-\:]+\|$', line):
            continue
        # 去除行首尾的 | 和多余空白（表格单元格内容）
        line = line.strip('|').strip()
        if line:
            lines.append(line)

    return lines
