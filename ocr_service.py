"""OCR 识别模块 - 使用 easyocr 识别发票图片中的文字"""

import easyocr


# 全局 reader 实例（避免重复加载模型）
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return _reader


def recognize(image_path: str) -> list[dict]:
    """
    识别图片中的文字，返回结构化结果。

    Args:
        image_path: 图片文件路径

    Returns:
        List of dicts with keys:
            - text: 识别的文字
            - bbox: 边界框坐标 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            - confidence: 置信度
    """
    reader = _get_reader()
    results = reader.readtext(image_path)

    parsed = []
    for bbox, text, conf in results:
        parsed.append({
            'text': text.strip(),
            'bbox': bbox,
            'confidence': round(conf, 4),
        })

    # 按 y 坐标排序（从上到下），y 相近时按 x 排序（从左到右）
    parsed.sort(key=lambda r: (r['bbox'][0][1], r['bbox'][0][0]))

    return parsed


def recognize_texts(image_path: str) -> list[str]:
    """简化接口：只返回识别的文字行列表"""
    results = recognize(image_path)
    return [r['text'] for r in results if r['text']]


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'test.jpg'
    print(f'正在识别: {path}')
    texts = recognize_texts(path)
    for i, t in enumerate(texts):
        print(f'  [{i}] {t}')
