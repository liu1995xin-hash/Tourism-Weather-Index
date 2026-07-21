# 五项指标 PNG 流程图

本目录保存论文插图式的总体计算框架，以及五项旅游气象指数的流程图源文件和 PNG 成品。五项指标图均包括：输入、质量控制、核心计算、分级输出和计算公式。

`00-two-program-workflow.png` 是论文方法框架图：它明确区分“程序一：历史基准构建”和“程序二：未来逐日预报计算”，并以冻结基准 Excel 作为两者的唯一参数接口。图中同时列出五项指数公式、UVP 固定站点参数、D 的经验冷位次规则、综合指数 TI 的子得分转换、权重和本地历史分位阈值。

| 指标 | PNG 文件 | SVG 源文件 |
|---|---|---|
| 两程序总体框架 | `00-two-program-workflow.png` | `00-two-program-workflow.svg` |
| 日照紫外暴露潜势 UVP | `01-uvp.png` | `01-uvp.svg` |
| 着装保温需求 D | `02-clothing.png` | `02-clothing.svg` |
| 人体舒适度 C | `03-comfort.png` | `03-comfort.svg` |
| 温湿度指数 THI | `04-thi.png` | `04-thi.svg` |
| 风效指数 K | `05-wind-effect-k.png` | `05-wind-effect-k.svg` |

`render_flowcharts.py` 是可复现的图表生成脚本。修改其中的流程或公式后，运行：

```powershell
python .\docs\flowcharts\render_flowcharts.py
```

该命令生成 SVG；再用支持 SVG 的浏览器或图形工具导出同名 PNG。

`render_two_program_workflow.py` 用于生成两程序总体框架 SVG。
