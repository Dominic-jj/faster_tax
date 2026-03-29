"""
发票图片自动识别转电子发票 - Streamlit 主应用

使用方法：streamlit run app.py
"""

import os
import sys
import tempfile
import streamlit as st
import pandas as pd
from PIL import Image

# 确保当前目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import Item, parse_text_lines  # noqa: E402
from tax_matcher import TaxMatcher  # noqa: E402
from xlsx_writer import generate, generate_to_bytes  # noqa: E402


# ─── 页面配置 ────────────────────────────────────────────
st.set_page_config(
    page_title='发票识别转换',
    page_icon=' Invoice',
    layout='wide',
)

# ─── 初始化（带缓存） ────────────────────────────────────
@st.cache_resource
def get_tax_matcher():
    return TaxMatcher()


def do_ocr(image_file) -> list[str]:
    """对上传的图片进行 OCR 识别"""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(image_file.getvalue())
        temp_path = f.name

    try:
        from ocr_service import recognize_texts
        return recognize_texts(temp_path)
    finally:
        os.unlink(temp_path)


# ─── 主界面 ──────────────────────────────────────────────
st.title('发票图片识别转换')
st.markdown('上传发票图片 → 自动识别物品信息 → 匹配税收分类 → 生成标准 xlsx 文件')

# ─── 选择输入方式 ──────────────────────────────────────
tab1, tab2 = st.tabs(['图片上传识别', '手动输入/粘贴'])

items_from_input = []

# ===================== Tab1: 图片上传 =====================
with tab1:
    uploaded_file = st.file_uploader(
        '上传发票图片',
        type=['jpg', 'jpeg', 'png'],
        help='支持 jpg/png 格式的发票图片',
        key='file_uploader',
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader('原始图片')
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)

        with col2:
            st.subheader('处理结果')

            with st.spinner('正在识别中...（首次运行需下载OCR模型，请耐心等待）'):
                raw_texts = do_ocr(uploaded_file)

            # 显示 OCR 原始结果
            with st.expander(f'OCR 识别原始文本（{len(raw_texts)} 行）', expanded=True):
                for i, text in enumerate(raw_texts):
                    st.text(f'[{i}] {text}')

            # 解析
            items_from_input = parse_text_lines(raw_texts)

            if not items_from_input:
                st.warning('未能从图片中识别出物品信息。请尝试"手动输入"标签页。')

# ===================== Tab2: 手动输入 =====================
with tab2:
    st.subheader('手动输入物品信息')
    st.markdown('每行一个物品，格式：`物品名 数量 单价 总价`（用空格分隔）')

    manual_text = st.text_area(
        '物品列表',
        value='',
        height=200,
        placeholder=(
            '示例：\n'
            '16A 折産 4 15 60\n'
            '公牛有线 14座 4 38 152\n'
            '2P 324空气开关 3 30 90\n'
            '30X 60平板灯 2 50 100\n'
            '热水器 1 37 37\n'
            '时控开关 1 55 55'
        ),
        key='manual_input',
    )

    if manual_text.strip():
        lines = [l.strip() for l in manual_text.strip().split('\n') if l.strip()]
        manual_items = parse_text_lines(lines)
        if manual_items:
            items_from_input = manual_items
        else:
            st.warning('无法解析输入内容，请检查格式。')

# ─── 公共处理：税收匹配 + 可编辑表格 + 下载 ──────────────
if items_from_input:
    # 税收匹配
    matcher = get_tax_matcher()
    matcher.match_items(items_from_input)

    st.divider()
    st.subheader(f'物品明细（共 {len(items_from_input)} 项，可编辑修正）')

    # 构建可编辑 DataFrame
    df_data = []
    for item in items_from_input:
        df_data.append({
            '物品名称': item.name,
            '规格型号': item.spec,
            '单位': item.unit,
            '数量': item.quantity,
            '单价': item.unit_price,
            '总价': item.amount,
            '税收分类编码': item.tax_code,
            '税收分类名称': item.tax_name,
        })

    edited_df = st.data_editor(
        pd.DataFrame(df_data),
        use_container_width=True,
        num_rows='dynamic',
        key='items_editor',
    )

    # 生成 xlsx
    st.divider()
    if st.button('生成电子发票 xlsx', type='primary'):
        try:
            # 从编辑后的 DataFrame 构建 Item 列表
            final_items = []
            for _, row in edited_df.iterrows():
                # 重新匹配税收分类（如果名称被修改了）
                name = str(row['物品名称'])
                code, cat_name = matcher.match(name)
                if not row['税收分类编码'] or str(row['税收分类编码']).strip() == '':
                    pass  # use newly matched code
                else:
                    code = str(row['税收分类编码'])
                    cat_name = str(row['税收分类名称'])

                final_items.append(Item(
                    name=name,
                    spec=str(row['规格型号']),
                    unit=str(row['单位']),
                    quantity=float(row['数量']),
                    unit_price=float(row['单价']),
                    amount=float(row['总价']),
                    tax_code=code,
                    tax_name=cat_name,
                ))

            xlsx_bytes = generate_to_bytes(final_items)

            st.download_button(
                label='下载电子发票 xlsx',
                data=xlsx_bytes,
                file_name='发票明细.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            st.success('xlsx 文件已生成，点击上方按钮下载')

            # 预览生成的内容
            with st.expander('预览生成内容'):
                for item in final_items:
                    st.text(
                        f'{item.name} | 规格:{item.spec} | '
                        f'{item.quantity}{item.unit} x {item.unit_price} = {item.amount} | '
                        f'税率:0.01 | 分类:{item.tax_name}'
                    )
        except Exception as e:
            st.error(f'生成失败: {e}')

# ─── 使用说明（底部） ──────────────────────────────────
with st.expander('使用说明'):
    st.markdown("""
    ### 使用流程
    1. **图片模式**：上传发票图片，自动 OCR 识别 → 编辑修正 → 下载 xlsx
    2. **手动模式**：直接输入/粘贴物品列表 → 编辑修正 → 下载 xlsx

    ### 输入格式
    每行一个物品，空格分隔：`物品名 数量 单价 总价`
    - 规格型号会自动从物品名前缀提取（如 `2P 324空气开关` → 规格 `2P 324`，名称 `空气开关`）
    - 单位默认为"个"

    ### 注意事项
    - 税率固定为 0.01（1%）
    - 表格支持直接编辑和添加/删除行
    - 税收分类按关键词模糊匹配 tax_list.xlsx，建议人工复核
    - 修改物品名称后会自动重新匹配税收分类
    """)
