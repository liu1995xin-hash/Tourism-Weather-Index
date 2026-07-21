# 使用说明

本说明对应当前的两程序结构：先由历史观测构建冻结基准，再用该基准计算某日的未来气象预报。共享规则模块 `src/tourism_indices.py` 由两个程序内部调用，不能作为独立命令行程序使用。

## 1. 运行环境

- Python 3；
- 依赖：`openpyxl`，在项目根目录执行 `python -m pip install -r requirements.txt` 安装；
- 所有命令均在项目根目录执行。

```powershell
cd C:\path\to\Tourism-Weather-Index
python -m pip install -r requirements.txt
```

## 2. 程序一：构建冻结基准

### 适用时机

仅在以下情况运行：首次部署、已授权的历史工作簿更新，或指标方法版本改变。不要为了每天的预报重复构建基准。

### 输入与输出

- 输入：原始历史工作簿，例如 `data/SHUJU(1).xlsx`；
- 输出：冻结基准工作簿，例如 `data/baseline_tea_card_v2.xlsx`。

```powershell
python .\src\build_baseline.py `
  --history ".\data\SHUJU(1).xlsx" `
  --output .\data\baseline_tea_card_v2.xlsx
```

成功时，终端输出 UTF-8 JSON，其中包含基准文件路径、方法版本、基准期、有效日数、UVP 与着装需求阈值，以及历史源文件的 SHA-256。

### 基准 Excel 的内容

| 工作表 | 保存内容 | 用途 |
|---|---|---|
| `Metadata` | 结构版本、方法版本、站点参数、源文件哈希、基准日期范围及固定质控参数 | 追溯和口径校验。 |
| `Thresholds` | UVP、着装需求、综合旅游气象指数的 20%/40%/60%/80% 历史分位阈值 | UVP、着装需求和综合指数的五级分段。 |
| `Distributions` | 升序的历史最低气温和风效指数 K | 计算着装需求的连续经验冷位次。 |
| `Validation` | 各项构建时的有效日数 | 检查基准完整性。 |

不要人工修改基准 Excel。程序二会校验结构版本、方法版本、站高、UVP 海拔因子、分布排序及有效样本数；不符合规则时将停止并输出错误信息。

## 3. 程序二：计算某日预报指数

### 输入字段

未来预报须与历史工作簿保持同一逐日统计口径。

| JSON 键 / 命令参数 | 含义 | 单位 |
|---|---|---|
| `date` / `--date` | 预报日期，格式 `YYYY-MM-DD` | 日期 |
| `avg_temp` / `--avg-temp` | 日平均气温 | ℃ |
| `min_temp` / `--min-temp` | 日最低气温 | ℃ |
| `avg_rh` / `--avg-rh` | 日平均相对湿度 | % |
| `avg_wind` / `--avg-wind` | 日平均 2 分钟风速 | m/s |
| `sunshine_hours` / `--sunshine-hours` | 日照时数 | 小时 |

数值 `>=999000` 被视为缺测，不能用于计算。所有输入均为逐日数据，不代表某一具体时刻。

### 方式 A：使用 JSON 文件

创建一个 UTF-8 编码 JSON 文件，例如 `forecast.json`：

```json
{
  "date": "2026-07-20",
  "avg_temp": 14.0,
  "min_temp": 6.0,
  "avg_rh": 45,
  "avg_wind": 3.0,
  "sunshine_hours": 10.0
}
```

执行：

```powershell
python .\src\calculate_indices.py `
  --baseline .\data\baseline_tea_card_v2.xlsx `
  --input-json .\examples\forecast.json
```

### 方式 B：直接传入六项参数

```powershell
python .\src\calculate_indices.py `
  --baseline .\data\baseline_tea_card_v2.xlsx `
  --date 2026-07-20 `
  --avg-temp 14.0 `
  --min-temp 6.0 `
  --avg-rh 45 `
  --avg-wind 3.0 `
  --sunshine-hours 10.0
```

`--input-json` 与六项独立参数只能二选一。

## 4. 输出解释

成功时输出 UTF-8 JSON，包括以下五项连续指数、其后追加的综合旅游气象指数、等级和计算所用基准信息。

| 输出键 | 含义 |
|---|---|
| `uvp` | 日照紫外暴露潜势。是以固定站高 3087.6m 修正的相对直接日照暴露潜势，不是标准 UVI。 |
| `clothing` | 0–100 的相对着装保温需求，不是衣物实际厚度或 `clo`。 |
| `comfort` | 未叠加着装调整的原始天气舒适度。 |
| `thi` | 温湿度指数及九级分级。 |
| `wind_effect_k` | 风效指数 K 及九级分级。 |
| `tourism_composite` | 按五项输出加权得到的综合旅游气象指数，包含五项子得分、权重和本地历史分位等级。 |

计算器还返回基准期、UVP、着装需求与综合旅游气象指数阈值、站高、UVP 海拔因子和历史源文件哈希，便于追溯某次结果所用的基准。

## 5. 日常运行顺序

```text
首次部署 / 历史数据或方法更新：运行 build_baseline.py
                      ↓
               生成并保存基准 Excel
                      ↓
每个预报日：运行 calculate_indices.py
                      ↓
       输出五项旅游气象指数及综合旅游气象指数
```

两个程序与五项公式的关系见 [总体方法框架图](flowcharts/00-two-program-workflow.png)。单项公式流程图见 [流程图目录](flowcharts/README.md)。

## 6. 结果使用边界

- 当前模型只覆盖五项气象体验指标，不包含降水、雷电、能见度或灾害性大风等旅游安全风险；
- UVP 缺少辐射和大气成分观测，不能解释为健康剂量或标准紫外线指数 UVI；
- 如需更换历史基准期或指标方法，请生成新的、带版本号的基准文件，保留旧文件以确保历史结果可追溯。
