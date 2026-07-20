#!/usr/bin/env python3
"""Render the paper-style two-program workflow as SVG."""

from __future__ import annotations

from html import escape
from pathlib import Path


OUT = Path(__file__).resolve().parent / "00-two-program-workflow.svg"
WIDTH, HEIGHT = 2200, 1220
FONT = "Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif"

PALETTE = {
    "blue": ("#EAF2FF", "#2B5D8A"),
    "orange": ("#FFF4E5", "#A85E0C"),
    "slate": ("#F1F5F9", "#4E6278"),
    "green": ("#E8F6EE", "#287753"),
}


def text(lines: list[str], x: int, y: int, *, size: int = 24, bold: bool = False) -> str:
    weight = 600 if bold else 400
    line_height = size + 12
    return "".join(
        f'<text x="{x}" y="{y + i * line_height}" text-anchor="middle" '
        f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="#17263A">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )


def node(x: int, y: int, width: int, height: int, heading: str, body: list[str], role: str) -> str:
    fill, stroke = PALETTE[role]
    header_height = 54
    body_top = y + header_height + 58
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{width}" height="{header_height}" rx="14" fill="{stroke}"/>',
        f'<rect x="{x}" y="{y + header_height - 12}" width="{width}" height="12" fill="{stroke}"/>',
        text([heading], x + width // 2, y + 36, size=25, bold=True),
        text(body, x + width // 2, body_top, size=22),
    ])


def arrow(x1: int, y1: int, x2: int, y2: int, *, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="10 8"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#718096" stroke-width="3"{dash} marker-end="url(#arrow)"/>'


def render() -> None:
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#718096"/></marker></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#FFFFFF"/>',
        f'<text x="70" y="82" font-family="{FONT}" font-size="40" font-weight="600" fill="#17263A">茶卡盐湖旅游气象指数：两程序计算框架</text>',
        f'<text x="70" y="124" font-family="{FONT}" font-size="22" fill="#607082">历史数据仅用于构建冻结基准；未来预报计算仅读取冻结基准 Excel，不重算历史分布</text>',
        '<rect x="60" y="175" width="2080" height="410" rx="18" fill="#F8FBFE" stroke="#C5D7E8" stroke-width="2"/>',
        '<rect x="60" y="650" width="2080" height="450" rx="18" fill="#F8FCFA" stroke="#C7DED3" stroke-width="2"/>',
        f'<text x="100" y="220" font-family="{FONT}" font-size="29" font-weight="600" fill="#2B5D8A">程序一  历史基准构建（仅在更新历史数据或方法时运行）</text>',
        f'<text x="100" y="695" font-family="{FONT}" font-size="29" font-weight="600" fill="#287753">程序二  未来逐日预报计算（每次输入未来气象数据时运行）</text>',
    ]

    top_y, top_h = 285, 230
    top_nodes = [
        (120, 280, "历史输入", ["茶卡国家基准气候站", "逐日历史工作簿", "SHUJU(1).xlsx"], "blue"),
        (500, 280, "字段与质量控制", ["字段映射", "999xxx 缺测剔除", "日照昼长校验"], "orange"),
        (880, 280, "历史计算", ["计算 K、UVP", "保留 Tmin 与 K 分布", "计算 D 历史样本"], "slate"),
        (1260, 280, "阈值构建", ["UVP：20/40/60/80%", "D：20/40/60/80%", "记录有效样本数"], "slate"),
        (1640, 280, "冻结基准 Excel", ["Metadata", "Thresholds", "Distributions", "Validation"], "green"),
    ]
    for x, width, heading, body, role in top_nodes:
        elements.append(node(x, top_y, width, top_h, heading, body, role))
    for left, right in zip(top_nodes, top_nodes[1:]):
        elements.append(arrow(left[0] + left[1] + 18, top_y + 105, right[0] - 20, top_y + 105))

    bottom_y, bottom_h = 765, 220
    bottom_nodes = [
        (120, 300, "未来预报输入", ["日期、平均/最低气温", "平均湿度、平均风速", "日照时数"], "blue"),
        (500, 300, "输入质量控制", ["同一字段口径", "范围与缺测检查", "日照昼长校验"], "orange"),
        (880, 330, "加载并校验基准", ["读取基准 Excel", "版本、站高、海拔因子", "分布排序与样本数"], "green"),
        (1290, 350, "五项指数计算", ["THI：t、RH", "K：t、V、S", "UVP：日期、S、海拔因子", "D：Tmin、K、历史分布", "C：THI_score、K_score"], "slate"),
        (1720, 320, "结果输出", ["五项连续值与等级", "D 的两个冷位次", "基准版本与源文件哈希"], "green"),
    ]
    for x, width, heading, body, role in bottom_nodes:
        elements.append(node(x, bottom_y, width, bottom_h, heading, body, role))
    elements.append(arrow(438, 875, 478, 875))
    elements.append(arrow(818, 875, 858, 875))
    elements.append(arrow(1238, 875, 1268, 875))
    elements.append(arrow(1658, 875, 1698, 875))
    elements.append(arrow(1800, 495, 1045, 745, dashed=True))
    elements.append(f'<text x="1440" y="610" font-family="{FONT}" font-size="20" fill="#3C6E55">读取冻结基准（不读取原始历史数据）</text>')
    elements.extend([
        '<line x1="60" x2="2140" y1="1140" y2="1140" stroke="#D6DEE7" stroke-width="2"/>',
        f'<text x="70" y="1185" font-family="{FONT}" font-size="20" fill="#607082">说明：程序一和程序二均调用相同的五项指数公式、质量控制和分级口径；仅数据读取职责被拆分。</text>',
        '</svg>',
    ])
    OUT.write_text("\n".join(elements), encoding="utf-8")


if __name__ == "__main__":
    render()
    print(f"Generated {OUT}")
