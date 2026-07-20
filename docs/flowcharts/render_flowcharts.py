#!/usr/bin/env python3
"""Render the five documented index flows as standalone SVG diagrams.

Run this script, then use a browser or an SVG renderer to export the files as
PNG. The generated diagrams deliberately present one index per page.
"""

from __future__ import annotations

from html import escape
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1600, 1000

FLOWS = {
    "01-uvp": {
        "title": "日照紫外暴露潜势指数（UVP）",
        "subtitle": "固定站高 3087.6m 的日照暴露潜势；不是标准 UVI",
        "nodes": [
            ("输入", ["日期", "日照时数 S"], "input"),
            ("质量控制", ["999xxx 缺测", "0≤S≤24", "理论昼长校验"], "qc"),
            ("太阳几何", ["固定纬度 36.7833°", "计算 δ、N、h", "UVP_base"], "compute"),
            ("海拔修正", ["H=3087.6m", "A_alt=1.30876", "UVP=UVP_base×A_alt"], "compute"),
            ("分级输出", ["历史分位数阈值", "低—高暴露潜势", "输出原/修正值与因子"], "output"),
        ],
        "formula": [
            "decl=23.45×sin(2×pi×(284+d)/365)；N=(24/pi)×arccos(-tan(lat)×tan(decl))",
            "h=arcsin(sin(lat)×sin(decl)+cos(lat)×cos(decl))；lat=36.7833",
            "UVP=(100×S_adj×sin(h)/14.131644170491846)×1.30876",
        ],
    },
    "02-clothing": {
        "title": "着装保温需求指数（D）",
        "subtitle": "全天出游的相对保温准备需求；不是衣物厚度或 clo",
        "nodes": [
            ("输入", ["最低气温 Tmin", "平均气温 t", "风速 V、日照 S"], "input"),
            ("质量控制", ["999xxx 缺测", "变量合理范围", "日照昼长校验"], "qc"),
            ("风效计算", ["K=f(t, V, S)", "保留 Tmin", "使用质控后 S"], "compute"),
            ("历史冷位次", ["Rmin=P(Tmin_hist≥Tmin)", "RK=P(K_hist≥K)", "D=max(Rmin, RK)"], "compute"),
            ("分级输出", ["历史 D 分位数", "极低—高保温需求", "输出两个冷位次"], "output"),
        ],
        "formula": [
            "K=−(10×sqrt(V)+10.45−V)×(33−t)+8.55×S",
            "Rmin=100×P(Tmin_hist≥Tmin)；RK=100×P(K_hist≥K)",
            "D=max(Rmin, RK)",
        ],
    },
    "03-comfort": {
        "title": "人体舒适度（C）",
        "subtitle": "未通过加衣、遮阳等行为调整的原始天气热舒适度",
        "nodes": [
            ("输入", ["平均气温 t", "湿度 RH", "风速 V、日照 S"], "input"),
            ("质量控制", ["999xxx 缺测", "变量合理范围", "日照昼长校验"], "qc"),
            ("基础指标", ["计算 THI 与 THI_score", "计算 K 与 K_score", "保留有方向分值"], "compute"),
            ("最不利因子", ["A=max(|THI_score|,", "      |K_score|)", "C=100−12.5×A"], "compute"),
            ("分级输出", ["C∈{0,25,50,75,100}", "舒适—不舒适", "输出最大偏离 A"], "output"),
        ],
        "formula": [
            "A=max(|THI_score|, |K_score|)",
            "C=100−12.5×A",
            "THI_score 与 K_score 分别由既定的 THI、K 九档分段映射得到",
        ],
    },
    "04-thi": {
        "title": "温湿度指数（THI）",
        "subtitle": "温度与相对湿度的逐日体感指标",
        "nodes": [
            ("输入", ["平均气温 t", "平均相对湿度 RH"], "input"),
            ("质量控制", ["999xxx 缺测", "−80≤t≤70", "0≤RH≤100"], "qc"),
            ("湿度换算", ["f=RH/100", "统一为比例值", "准备公式输入"], "compute"),
            ("THI 计算", ["THI=(1.8t+32)", "−0.55(1−f)(1.8t−26)", "得到连续值"], "compute"),
            ("分级输出", ["9 档参考分段", "极冷—极闷热", "输出 THI 与分值"], "output"),
        ],
        "formula": [
            "f=RH/100",
            "THI=(1.8t+32)−0.55×(1−f)×(1.8t−26)",
        ],
    },
    "05-wind-effect-k": {
        "title": "风效指数（K）",
        "subtitle": "温度、平均 2 分钟风速和日照时数的逐日综合体感指标",
        "nodes": [
            ("输入", ["平均气温 t", "平均 2 分钟风速 V", "日照时数 S"], "input"),
            ("质量控制", ["999xxx 缺测", "变量合理范围", "日照昼长校验"], "qc"),
            ("公式计算", ["K=−(10×sqrt(V)+10.45−V)", "×(33−t)+8.55S", "使用质控后 S"], "compute"),
            ("体感赋分", ["按 K 连续值", "映射有方向 K_score", "冷侧为负、热侧为正"], "compute"),
            ("分级输出", ["9 档参考分段", "酷冷—炎热", "输出 K 与分值"], "output"),
        ],
        "formula": [
            "K=−(10×sqrt(V)+10.45−V)×(33−t)+8.55×S",
            "K_score=g(K)，其中 g(·) 为既定九档有方向分段映射",
        ],
    },
}

STYLE = {
    "input": ("#EAF2FF", "#3A6EA5"),
    "qc": ("#FFF4E5", "#B66A16"),
    "compute": ("#F1F5F9", "#546274"),
    "output": ("#E8F6EE", "#2E7D5B"),
}


def multiline(lines: list[str], x: float, y: float, *, title: bool = False) -> str:
    size = 25 if title else 20
    weight = 600 if title else 400
    line_height = 34 if title else 29
    return "".join(
        f'<text x="{x}" y="{y + i * line_height}" text-anchor="middle" '
        f'font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#182230">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )


def left_multiline(lines: list[str], x: float, y: float) -> str:
    return "".join(
        f'<text x="{x}" y="{y + i * 31}" '
        f'font-family="Consolas, Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" '
        f'font-size="20" font-weight="400" fill="#182230">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )


def render(name: str, flow: dict) -> None:
    node_x = [60, 365, 670, 975, 1280]
    node_y, node_w, node_h = 265, 255, 240
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#7B8794"/></marker></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#FFFFFF"/>',
        '<line x1="60" x2="1540" y1="170" y2="170" stroke="#D8E0E8" stroke-width="2"/>',
        f'<text x="60" y="88" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="36" font-weight="600" fill="#182230">{escape(flow["title"])}</text>',
        f'<text x="60" y="130" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="20" fill="#607082">{escape(flow["subtitle"])}</text>',
    ]
    for index in range(len(node_x) - 1):
        start, end = node_x[index] + node_w, node_x[index + 1]
        svg.append(f'<line x1="{start + 16}" x2="{end - 18}" y1="385" y2="385" stroke="#7B8794" stroke-width="3" marker-end="url(#arrow)"/>')
    for x, (heading, lines, kind) in zip(node_x, flow["nodes"]):
        fill, stroke = STYLE[kind]
        svg.extend([
            f'<rect x="{x}" y="{node_y}" width="{node_w}" height="{node_h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
            f'<rect x="{x}" y="{node_y}" width="{node_w}" height="54" rx="14" fill="{stroke}"/>',
            f'<rect x="{x}" y="{node_y + 40}" width="{node_w}" height="14" fill="{stroke}"/>',
            multiline([heading], x + node_w / 2, node_y + 36, title=True),
            multiline(lines, x + node_w / 2, node_y + 104),
        ])
    svg.extend([
        '<rect x="60" y="585" width="1480" height="180" rx="14" fill="#F6F8FA" stroke="#D8E0E8" stroke-width="2"/>',
        '<text x="90" y="630" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="23" font-weight="600" fill="#182230">计算公式</text>',
        left_multiline(flow["formula"], 90, 672),
        '<line x1="60" x2="1540" y1="850" y2="850" stroke="#D8E0E8" stroke-width="2"/>',
        '<circle cx="72" cy="905" r="8" fill="#3A6EA5"/><text x="88" y="912" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="18" fill="#48576A">输入</text>',
        '<circle cx="220" cy="905" r="8" fill="#B66A16"/><text x="236" y="912" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="18" fill="#48576A">质量控制</text>',
        '<circle cx="415" cy="905" r="8" fill="#546274"/><text x="431" y="912" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="18" fill="#48576A">计算与映射</text>',
        '<circle cx="635" cy="905" r="8" fill="#2E7D5B"/><text x="651" y="912" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="18" fill="#48576A">分级输出</text>',
        '<text x="1540" y="912" text-anchor="end" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" font-size="17" fill="#607082">逐日尺度 · ≥999000 为缺测 · 方法版本 v1.1</text>',
        '</svg>',
    ])
    (OUT_DIR / f"{name}.svg").write_text("\n".join(svg), encoding="utf-8")


if __name__ == "__main__":
    for flow_name, flow_spec in FLOWS.items():
        render(flow_name, flow_spec)
    print(f"Generated {len(FLOWS)} SVG flowcharts in {OUT_DIR}")
