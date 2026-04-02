"""
OCR 识别模块 - 支持多引擎切换

支持引擎：
  - easyocr     : EasyOCR (默认，支持多语言)
  - rapidocr    : RapidOCR (轻量快速，基于 ONNX)
  - paddleocr   : PaddleOCR (中文最佳，需额外安装 paddlepaddle)
"""

# ─── 引擎注册表 ──────────────────────────────────────────
_ENGINES = {}


def _register_engine(name):
    """装饰器：注册 OCR 引擎"""
    def decorator(fn):
        _ENGINES[name] = fn
        return fn
    return decorator


def list_engines() -> list[str]:
    """返回所有已注册的引擎名"""
    return list(_ENGINES.keys())


def check_engine_available(name: str) -> tuple[bool, str]:
    """检查引擎是否可用（轻量检测，不实际导入包）"""
    import importlib.util
    if name == 'easyocr':
        found = importlib.util.find_spec('easyocr') is not None
        return (True, '') if found else (False, 'pip install easyocr')
    elif name == 'rapidocr':
        found = importlib.util.find_spec('rapidocr_onnxruntime') is not None
        return (True, '') if found else (False, 'pip install rapidocr_onnxruntime')
    elif name == 'paddleocr':
        found = importlib.util.find_spec('paddleocr') is not None
        return (True, '') if found else (False, 'pip install paddlepaddle paddleocr')
    return False, f'未知引擎: {name}'


# ─── EasyOCR 引擎 ────────────────────────────────────────
_easyocr_reader = None


@_register_engine('easyocr')
def _recognize_easyocr(image_path: str) -> list[dict]:
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

    results = _easyocr_reader.readtext(image_path)
    parsed = []
    for bbox, text, conf in results:
        parsed.append({
            'text': text.strip(),
            'bbox': bbox,
            'confidence': round(conf, 4),
        })
    parsed.sort(key=lambda r: (r['bbox'][0][1], r['bbox'][0][0]))
    return parsed


# ─── RapidOCR 引擎 ───────────────────────────────────────
_rapidocr_engine = None


@_register_engine('rapidocr')
def _recognize_rapidocr(image_path: str) -> list[dict]:
    global _rapidocr_engine
    if _rapidocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _rapidocr_engine = RapidOCR()

    result, _ = _rapidocr_engine(image_path)
    if not result:
        return []

    parsed = []
    for item in result:
        bbox = item[0]        # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        text = item[1]        # str
        conf = item[2]        # float
        parsed.append({
            'text': text.strip(),
            'bbox': bbox,
            'confidence': round(conf, 4),
        })
    parsed.sort(key=lambda r: (r['bbox'][0][1], r['bbox'][0][0]))
    return parsed


# ─── PaddleOCR 引擎 ──────────────────────────────────────
_paddleocr_engine = None


@_register_engine('paddleocr')
def _recognize_paddleocr(image_path: str) -> list[dict]:
    global _paddleocr_engine
    if _paddleocr_engine is None:
        from paddleocr import PaddleOCR
        _paddleocr_engine = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

    result = _paddleocr_engine.ocr(image_path, cls=True)
    if not result or not result[0]:
        return []

    parsed = []
    for line in result[0]:
        bbox = line[0]        # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        text = line[1][0]     # str
        conf = line[1][1]     # float
        parsed.append({
            'text': text.strip(),
            'bbox': bbox,
            'confidence': round(conf, 4),
        })
    parsed.sort(key=lambda r: (r['bbox'][0][1], r['bbox'][0][0]))
    return parsed


# ─── 公共接口 ────────────────────────────────────────────
def recognize(image_path: str, engine: str = 'easyocr') -> list[dict]:
    """
    使用指定引擎识别图片文字。

    Args:
        image_path: 图片路径
        engine: 引擎名 ('easyocr' | 'rapidocr' | 'paddleocr')

    Returns:
        [{'text': str, 'bbox': list, 'confidence': float}, ...]
    """
    if engine not in _ENGINES:
        raise ValueError(f'未知引擎: {engine}，可选: {list_engines()}')
    return _ENGINES[engine](image_path)


def recognize_texts(image_path: str, engine: str = 'easyocr') -> list[str]:
    """简化接口：只返回识别的文字行列表"""
    results = recognize(image_path, engine)
    return [r['text'] for r in results if r['text']]
