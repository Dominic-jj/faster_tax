"""解析文本行并提取结构化物品信息。

该模块用于把 OCR 结果或手工整理后的单行文本解析为 ``Item``。
核心规则如下：

- 支持 ``物品名 数量 单价``，总价缺省时自动按数量乘单价计算。
- 支持 ``物品名 数量 单价 总价``，总价优先采用输入值。
- 物品名前缀中的规格型号会被拆分到 ``spec`` 字段。
- 物品名末尾常见单位会被识别并拆分到 ``unit`` 字段。
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
    从物品名开头提取规格型号前缀。

    Returns:
        (spec, clean_name): 规格型号与去除规格后的名称。

    如果前缀不匹配已知规格模式，则返回空规格和原始名称。
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
    解析单行文本并提取物品信息。

    输入行默认采用空格分隔，末尾数字按以下规则解释：

    - 两个数字：依次视为数量、单价，总价自动计算。
    - 三个及以上数字：最后三个数字依次视为数量、单价、总价。

    其余文本部分会继续拆分规格型号、物品名称和单位。

    Examples:
        "插座 4 15"          → 总价自动算 60
        "16A 插座 4 15 60"   → 使用填写的总价 60
        "公牛有线 14座 4 38 152"
        "2P 324空气开关 3 30 90"
    """
    line = line.strip()
    if not line:
        return None

    # 提取所有数字（整数或小数）
    numbers = re.findall(r'\d+\.?\d*', line)

    if len(numbers) < 2:
        return None

    try:
        if len(numbers) == 2:
            # 只有数量、单价 → 总价自动计算
            qty = float(numbers[-2])
            price = float(numbers[-1])
            total = qty * price
        else:
            # 最后三个数字：数量、单价、总价
            qty = float(numbers[-3])
            price = float(numbers[-2])
            total = float(numbers[-1])
    except (ValueError, IndexError):
        return None

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
    # 先尝试匹配末尾双字单位，再尝试单字单位
    unit = '个'  # 默认
    known_units_2 = {'公斤', '千克', '平米', '立方'}
    known_units_1 = {'个', '只', '把', '条', '件', '台', '套', '组', '米', '箱',
                     '盒', '包', '瓶', '罐', '块', '片', '张', '副', '对', '根',
                     '支', '卷', '袋', '桶', '升', '吨', '克', '卷', '批', '扎'}

    if len(clean_name) >= 2 and clean_name[-2:] in known_units_2:
        unit = clean_name[-2:]
        clean_name = clean_name[:-2].strip()
    elif clean_name and clean_name[-1] in known_units_1:
        unit = clean_name[-1]
        clean_name = clean_name[:-1].strip()

    # 关键词推断：根据物品名中的产品类型词推断单位
    _unit_hints = {
        '线': '米', '电缆': '米', '电线': '米', '导线': '米', '网线': '米',
        '管': '根', '水管': '根', '线管': '根', '钢管': '根',
        '灯': '个', '平板灯': '个', '日光灯': '个', '灯泡': '个', '灯管': '个',
        '开关': '个', '插座': '个', '断路器': '个', '接触器': '个',
        '螺丝': '包', '钉子': '包', '胶带': '卷',
    }
    if unit == '个':
        for keyword, hint_unit in _unit_hints.items():
            if keyword in clean_name:
                unit = hint_unit
                break

    return Item(
        name=clean_name,
        spec=spec,
        unit=unit,
        quantity=qty,
        unit_price=price,
        amount=total,
    )


def parse_text_lines(lines: list[str]) -> list[Item]:
    """
    批量解析多行文本中的物品信息。

    Args:
        lines: 待解析的文本行列表。

    Returns:
        成功解析出的 ``Item`` 列表；无法解析的行会被跳过。
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
        "16A 插座 4 15 60",
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
