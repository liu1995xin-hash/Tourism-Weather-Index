#!/usr/bin/env python3
"""Render the complete baseline-to-forecast workflow as a paper-style SVG."""

from __future__ import annotations

from html import escape
from pathlib import Path


OUT = Path(__file__).resolve().parent / "00-two-program-workflow.svg"
WIDTH, HEIGHT = 2700, 1940
FONT = "Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif"

PALETTE = {
    "blue": ("#EAF2FF", "#2B5D8A"),
    "orange": ("#FFF4E5", "#A85E0C"),
    "slate": ("#F1F5F9", "#4E6278"),
    "green": ("#E8F6EE", "#287753"),
    "purple": ("#F4EFFF", "#6C4BA6"),
}


def text(lines: list[str], x: int, y: int, *, size: int = 24, bold: bool = False, anchor: str = "middle", fill: str = "#17263A") -> str:
    weight = 600 if bold else 400
    line_height = size + 12
    return "".join(
        f'<text x="{x}" y="{y + i * line_height}" text-anchor="{anchor}" '
        f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )


def node(x: int, y: int, width: int, height: int, heading: str, body: list[str], role: str, *, body_size: int = 22) -> str:
    fill, stroke = PALETTE[role]
    header_height = 52
    body_top = y + header_height + 47
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="15" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{width}" height="{header_height}" rx="15" fill="{stroke}"/>',
        f'<rect x="{x}" y="{y + header_height - 12}" width="{width}" height="12" fill="{stroke}"/>',
        text([heading], x + width // 2, y + 35, size=24, bold=True, fill="#FFFFFF"),
        text(body, x + width // 2, body_top, size=body_size),
    ])


def arrow(x1: int, y1: int, x2: int, y2: int, *, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="10 8"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#718096" stroke-width="3"{dash} marker-end="url(#arrow)"/>'


def section(x: int, y: int, width: int, height: int, title: str, subtitle: str, role: str) -> list[str]:
    _, stroke = PALETTE[role]
    return [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="20" fill="#FAFCFE" stroke="{stroke}" stroke-width="2"/>',
        text([title], x + 38, y + 47, size=30, bold=True, anchor="start", fill=stroke),
        text([subtitle], x + 38, y + 82, size=20, anchor="start", fill="#607082"),
    ]


def render() -> None:
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#718096"/></marker></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#FFFFFF"/>',
        text(["茶卡盐湖逐日旅游气象指数：历史基准构建、未来预报计算与综合指数"], 80, 72, size=39, bold=True, anchor="start"),
        text(["方法版本 1.2-composite-index｜历史数据仅用于构建冻结基准；未来计算仅读取该基准，不重算历史分布"], 80, 115, size=21, anchor="start", fill="#607082"),
    ]

    elements += section(60, 155, 2580, 570, "程序一  历史基准构建", "首次部署、历史工作簿更新或方法版本更新时运行；输出可追溯的 baseline_tea_card_v2.xlsx", "blue")
    top_y = 270
    top_nodes = [
        (105, 390, "历史逐日输入", ["日期；平均气温 T；最低气温 Tmin", "平均相对湿度 RH；平均风速 V", "日照时数 S", "数据源：SHUJU(1).xlsx"], "blue", 21),
        (545, 405, "质量控制", ["999xxx（≥999000）剔除", "T、Tmin：−80～70 ℃；RH：0～100%", "V：0～100 m/s；S：0～24 h", "S ≤ 理论昼长 + 0.05 h"], "orange", 19),
        (1000, 520, "逐日公式引擎（与程序二相同）", ["THI、K、UVP、D、C 与 TI", "UVP：固定纬度 36.7833°、站高 3087.6 m", "D：保留排序后的 Tmin、K 历史分布", "完整六字段日：计算 TI 历史样本"], "slate", 19),
        (1570, 420, "本地历史参数", ["UVP 阈值：36.329 / 46.897 / 64.190 / 87.407", "D 阈值：27.991 / 45.830 / 67.151 / 86.813", "TI 阈值：21.349 / 36.745 / 58.937 / 69.944", "分位点均为 20% / 40% / 60% / 80%"], "purple", 18),
        (2040, 500, "冻结基准 Excel", ["Metadata：版本、站点、源文件 SHA-256", "Thresholds：UVP、D、TI 阈值", "Distributions：排序后的 Tmin、K", "Validation：有效样本数"], "green", 19),
    ]
    for x, width, heading, body, role, body_size in top_nodes:
        elements.append(node(x, top_y, width, 305, heading, body, role, body_size=body_size))
    for left, right in zip(top_nodes, top_nodes[1:]):
        elements.append(arrow(left[0] + left[1] + 18, top_y + 152, right[0] - 20, top_y + 152))

    elements += section(60, 765, 2580, 1005, "程序二  未来逐日预报计算", "输入与历史相同口径的一日预报；加载并校验冻结基准后，输出五项指数与综合旅游气象指数 TI", "green")

    # Input and validation column.
    elements.append(node(105, 900, 405, 300, "未来预报输入", ["date（YYYY-MM-DD）", "avg_temp=T；min_temp=Tmin", "avg_rh=RH；avg_wind=V", "sunshine_hours=S"], "blue", body_size=22))
    elements.append(node(105, 1260, 405, 270, "输入校验与日照归一", ["同一范围、缺测规则", "按日期与纬度算理论昼长", "超出昼长 +0.05 h：报错", "否则 S=min(S, 理论昼长)"], "orange", body_size=20))
    elements.append(arrow(307, 1205, 307, 1238))
    elements.append(arrow(530, 1395, 548, 1395))

    # Calculation core.
    elements.append(node(570, 850, 675, 700, "五项指数：精确计算", [
        "① THI=(1.8T+32)−0.55×(1−RH/100)×(1.8T−26)",
        "   按既有 9 档得 score_THI∈{−8,−6,…,8}",
        "② K=−(10√V+10.45−V)×(33−T)+8.55×S",
        "   按既有 9 档得 score_K∈{−8,−6,…,8}",
        "③ UVP_raw=100×S×sin(h₀)/14.131644",
        "   sin(h₀)由 date、纬度 36.7833° 的太阳几何计算",
        "   海拔因子=1+0.10×3087.6/1000=1.30876",
        "   UVP=UVP_raw×1.30876",
        "④ coldRank(x)=100×[n−lower_bound(历史排序分布,x)]/n",
        "   D=max(coldRank(Tmin), coldRank(K))",
        "⑤ C=100−12.5×max(|score_THI|,|score_K|)",
    ], "slate", body_size=19))

    # Baseline input/quality into calculation.
    elements.append(node(570, 1605, 675, 120, "基准加载并校验", ["Schema / 方法版本 / 站高 / 海拔因子 / 权重 / UVP 评分 / 分布排序 / 有效样本数"], "green", body_size=17))
    elements.append(arrow(2300, 575, 910, 1645, dashed=True))
    elements.append(arrow(908, 1600, 908, 1575))
    elements.append(text(["程序二读取冻结基准；不读取原始历史工作簿"], 1580, 1500, size=19, fill="#3C6E55"))

    # Composite logic.
    elements.append(node(1310, 850, 670, 700, "综合指数 TI：子得分与权重", [
        "S_C=C",
        "S_THI=100−12.5×|score_THI|",
        "S_K=100−12.5×|score_K|",
        "S_D=100−D",
        "UVP 以历史 5 档映射 S_UVP：50 / 75 / 100 / 75 / 50",
        "TI=0.35×S_C + 0.15×S_THI + 0.15×S_K",
        "   +0.20×S_D + 0.15×S_UVP",
        "权重和=1；THI、K 的直接权重各为 0.15",
        "TI 用历史阈值 21.349 / 36.745 / 58.937 / 69.944",
        "划分：极低 / 较低 / 中等 / 较高 / 高",
    ], "purple", body_size=19))
    elements.append(arrow(1268, 1200, 1288, 1200))

    # Output.
    elements.append(node(2045, 900, 500, 500, "结构化结果输出", [
        "UVP：连续值、UVP_raw、海拔因子、等级",
        "D：连续值、Tmin/K 冷位次、等级",
        "C：连续值、最大偏离、等级",
        "THI、K：连续值、score、等级",
        "TI：连续值、5 个子得分、权重、等级",
        "基准期、阈值、站点参数、源文件哈希",
    ], "green", body_size=19))
    elements.append(arrow(2005, 1200, 2023, 1200))

    # Bottom notes.
    elements += [
        '<line x1="60" x2="2640" y1="1820" y2="1820" stroke="#D6DEE7" stroke-width="2"/>',
        text(["边界：TI 表达五项气象条件的加权综合位置；不包含降水、雷电、能见度、最大风速等旅游安全风险。UVP 为日照紫外暴露潜势，不是标准 UVI。"], 80, 1866, size=20, anchor="start", fill="#607082"),
        text(["历史基准期：1961-01-01 至 2026-07-11；TI 完整样本数：23,628 天。"], 80, 1905, size=20, anchor="start", fill="#607082"),
        '</svg>',
    ]
    OUT.write_text("\n".join(elements), encoding="utf-8")


if __name__ == "__main__":
    render()
    print(f"Generated {OUT}")
