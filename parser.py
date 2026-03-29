"""
解析模块 - 从 OCR 识别结果中提取结构化物品信息

支持两种输入：
1. OCR 原始结果 list[dict]（含坐标，用于表格定位）
2. 纯文本行 list[str]
"""

import re
from dataclasses import dataclass, fields


@dataclass
class Item:
    """发票中的一个物品条目"""
    name: str           # 物品名称（去除规格前缀）
    spec: str           # 规格型号
    unit: str           # 单位（默认"个"）
    quantity: float     # 数量
    unit_price: float   # 单价
    amount: float       # 总价
    tax_code: str = ""  # 税收分类编码（由 tax_matcher 填充）
    tax_name: str = ""  # 税收分类名称（由 tax_matcher 填充）

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# 规格型号前缀模式：字母/数字组合出现在物品名开头
SPEC_PATTERNS = [
    # "16A", "2P 324", "30X 60" 等
    r'^([0-9]+[A-Za-z]+(?:\s*[0-9]+[A-Za-z]*)*(?:\s+[0-9]+[Xx×]\s*[0-9]+)?)\s*',
    # "30X60" 无空格
    r'^([0-9]+[Xx×][0-9]+)\s*',
    # 纯数字+字母 如 "16A"
    r'^([0-9]+[A-Za-z]+)\s*',
    # "2P" 类型
    r'^([0-9]+P)\s*',
]


def extract_spec(name: str) -> tuple[str, str]:
    """
    从物品名中提取规格型号前缀。

    Returns:
        (spec, clean_name) - 规格型号和去除前缀后的名称
    """
    for pattern in SPEC_PATTERNS:
        m = re.match(pattern, name)
        if m:
            spec = m.group(1).strip()
            clean_name = name[m.end():].strip()
            if clean_name:  # 确保去除前缀后还有内容
                return spec, clean_name
    return "", name


def parse_text_line(line: str) -> Item | None:
    """
    解析单行文本，尝试提取物品信息。
    行格式通常是：物品名 + 数量 + 单价 + 总价

    Examples:
        "16A 折産 4 15 60"
        "公牛有线 14座 4 38 152"
        "2P 324空气开关 3 30 90"
    """
    line = line.strip()
    if not line:
        return None

    # 提取所有数字（整数或小数）
    numbers = re.findall(r'\d+\.?\d*', line)

    # 至少需要 3 个数字（数量、单价、总价）
    if len(numbers) < 3:
        return None

    # 尝试不同的数字分配策略
    # 最后三个数字分别是：数量、单价、总价
    try:
        qty = float(numbers[-3])
        price = float(numbers[-2])
        total = float(numbers[-1])
    except (ValueError, IndexError):
        return None

    # 验证：总价 ≈ 数量 × 单价（允许一定误差，手写可能有笔误）
    if qty > 0 and price > 0:
        expected = qty * price
        if abs(expected - total) > max(expected * 0.2, 5):  # 20%误差或5元
            # 尝试其他分配：最后两个数字是单价和总价，倒数第三个不是数量
            # 或者数字含义不同
            pass  # 仍然使用原始值，手写可能有误差

    # 提取物品名：去除尾部的数字
    name_part = line
    for n in reversed(numbers):
        # 从后往前去掉数字
        name_part = re.sub(r'\s*' + re.escape(n) + r'\s*$', '', name_part, count=1)

    name_part = name_part.strip()
    if not name_part:
        return None

    # 检查是否含有中文字符（排除纯数字行）
    if not re.search(r'[\u4e00-\u9fff]', name_part):
        return None

    # 提取规格型号
    spec, clean_name = extract_spec(name_part)

    # 提取单位（如"个"、"只"、"把"等）
    unit_match = re.search(r'([\u4e00-\u9fff]{1})$', clean_name)
    unit = '个'  # 默认
    known_units = {'个', '只', '把', '条', '件', '台', '套', '组', '米', '箱',
                   '盒', '包', '瓶', '罐', '块', '片', '张', '副', '对', '根',
                   '支', '卷', '袋', '桶', '升', '吨', '公斤', '千克', '克'}

    if unit_match and unit_match.group(1) in known_units:
        unit = unit_match.group(1)
        clean_name = clean_name[:-1].strip()

    return Item(
        name=clean_name,
        spec=spec,
        unit=unit,
        quantity=qty,
        unit_price=price,
        amount=total,
    )


def parse_ocr_results(results: list[dict]) -> list[Item]:
    """
    从 OCR 结果中解析物品列表。

    Args:
        results: ocr_service.recognize() 返回的结果

    Returns:
        解析出的 Item 列表
    """
    items = []
    for r in results:
        text = r.get('text', '')
        item = parse_text_line(text)
        if item:
            items.append(item)
    return items


def parse_text_lines(lines: list[str]) -> list[Item]:
    """
    从纯文本行列表中解析物品。

    Args:
        lines: 文本行列表

    Returns:
        解析出的 Item 列表
    """
    items = []
    for line in lines:
        item = parse_text_line(line)
        if item:
            items.append(item)
    return items


if __name__ == '__main__':
    # 测试用例
    test_lines = [
        "16A 折産 4 15 60",
        "公牛有线 14座 4 38 152",
        "2P 324空气开关 3 30 90",
        "30X 60平板灯 2 50 100",
        "热水器 1 37 37",
        "时控开关 1 55 55",
    ]

    for line in test_lines:
        item = parse_text_line(line)
        if item:
            print(f'{line}')
            print(f'  → name={item.name}, spec={item.spec}, qty={item.quantity}, '
                  f'price={item.unit_price}, total={item.amount}')
        else:
            print(f'{line} → 无法解析')
