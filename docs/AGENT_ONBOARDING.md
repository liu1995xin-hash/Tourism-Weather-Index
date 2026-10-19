# 大模型与开发者接手指南

本文为项目接手入口，整理日期为 2026-10-19。接手者应先核验所在分支与代码版本，再执行复现命令；本文记录的是当前实现和已确认需求，不代表以下待办事项已获实施授权。

## 1. 项目目标与交付状态

项目将茶卡盐湖附近国家气象站的历史逐日观测转化为冻结历史基准，再将一日气象预报转换为五项旅游气象指数与综合指数。输入是日期、日平均气温、日最低气温、日平均相对湿度、日平均 2 分钟风速、日照时数；输出顺序固定为 UVP、D、C、THI、K、TI。

当前已有历史基准构建 CLI、预报计算 CLI、共享规则模块、Tkinter 桌面界面、单文件 EXE 打包脚本、v2 基准 Excel、历史源数据、论文截图、流程图及说明文档。当前没有提供完整的自动化测试套件，也未实现多日批量输入接口。

完整实现位于 `agent/add-index-flow-diagrams` 分支；上一次功能提交为 `7afc46a`。截至本次核验，PR #1 仍为未合并草稿，基分支及仓库默认分支为 `agent/tea-card-tourism-indices`。接手者应使用功能分支，避免只读取默认分支后误判功能缺失。

```powershell
git clone --branch agent/add-index-flow-diagrams https://github.com/liu1995xin-hash/Tourism-Weather-Index.git
cd Tourism-Weather-Index
git status -sb
git log -3 --oneline
```

## 2. 推荐阅读顺序与信息优先级

| 顺序 | 文件 | 阅读目的 |
|---:|---|---|
| 1 | 本文件 | 确认目标、当前状态、已确认决策和接手步骤。 |
| 2 | [详细方法说明](METHODOLOGY_SPECIFICATION.md) | 了解所有字段、公式、分级、精度、基准构建和输出语义。 |
| 3 | [综合指数说明](COMPOSITE_INDEX.md) | 理解 TI 的子得分、权重和 UVP 中等最佳偏好。 |
| 4 | `src/tourism_indices.py` | 对照实际函数实现与参数读取边界。 |
| 5 | [使用说明](USAGE.md)、[GUI/EXE 说明](GUI_EXE_USAGE.md) | 运行 CLI、界面和打包流程。 |
| 6 | [交接文档](HANDOFF.md)、[项目上下文](PROJECT_CONTEXT.md)、[逻辑审查](LOGIC_REVIEW.md) | 查阅需求演变、既有历史检查和限制。 |
| 7 | [总流程图](flowcharts/00-two-program-workflow.png)、[单项流程图目录](flowcharts/README.md) | 复核各阶段依赖与图示。 |

发生不一致时，先区分“当前代码实际行为”“已确认业务定义”“历史检查记录”三类信息。用当前代码和对应基准解释实际结果；若代码与已确认口径冲突，应列出证据、向用户说明，不应自行静默修改方法。

## 3. 两部分程序与共享规则

| 文件或目录 | 职责 | 接手注意事项 |
|---|---|---|
| `src/build_baseline.py` | 程序一：历史 Excel → 冻结基准 Excel | 日常计算不需要重复运行。 |
| `src/calculate_indices.py` | 程序二：一日预报 + 冻结基准 → JSON | 不读取原始历史工作簿。 |
| `src/tourism_indices.py` | 公式、质控、分级、基准构建和基准读写 | 唯一共享规则实现，不是独立 CLI。 |
| `src/tourism_index_gui.py` | 程序二的 Tkinter 界面 | 当前景点仅茶卡盐湖，读取 v2 基准。 |
| `tools/build_gui_exe.ps1` | PyInstaller 单文件打包 | 依赖所选 Python 的 Tcl/Tk 资源布局。 |
| `data/SHUJU(1).xlsx` | 用户授权提供的原始历史数据 | 不手工修改；版本追踪使用源文件哈希。 |
| `data/baseline_tea_card_v2.xlsx` | 当前冻结历史参数 | 程序二与 GUI 应使用此版本。 |
| `data/baseline_tea_card_v1.xlsx` | 旧版基准 | 当前方法版本不兼容，不用于当前计算。 |
| `examples/forecast.json` | 固定的示例输入 | 仅用于复现，不是真实天气预报。 |
| `docs/flowcharts/` | PNG、SVG 和生成脚本 | 修改方法或图后同步源文件与成品。 |

历史数据构建的是 Tmin/K 经验分布及 UVP/D/TI 分位阈值。现阶段没有回归训练、优化器或从游客标签拟合系数的程序；不要将“基准构建”描述为已完成监督模型训练。

## 4. 已确认且应保留的业务决策

1. 茶卡盐湖附近的国家气象站数据作为景区计算基础；所有结果为逐日尺度。
2. 未来气象数据由用户取得，本项目负责按规则转换指数；不自行生成天气预报。
3. 不补充外部气象观测，不通过猜测填补缺失的辐射、臭氧、人体活动等变量。
4. UVP 表示日照紫外暴露潜势，D 表示相对保温需求，C 表示未作着装补偿的原始天气热舒适度。
5. 海拔只对 UVP 使用固定乘数，历史与未来同时使用；THI、K、C、D 不额外增加海拔项，不新增高原提示。
6. 综合指数保留 THI/K/C/D 之间的重复影响，THI、K 直接权重各为 0.15；不擅自改成去重后的三指标模型。
7. UVP 采用中等最佳：历史五档对应子得分 50、75、100、75、50。
8. TI 权重按 C/THI/K/D/UVP 顺序为 0.35/0.15/0.15/0.20/0.15；这些是已确认设计权重，不是历史数据拟合权重。
9. 两部分程序通过基准 Excel 连接；GUI 只封装程序二；EXE 要求单文件、体积尽量小。
10. 公式、分级、基准期、权重或数据口径改变时应说明影响并管理版本；事实不足时向用户询问。

## 5. 版本、参数与数值复核

| 项目 | 当前值 |
|---|---|
| 方法版本 | `1.2-composite-index` |
| 基准结构版本 | `1.1` |
| 纬度 / 站高 | 36.7833° / 3087.6 m |
| UVP 海拔因子 | 1.30876 |
| 历史日期范围 | 1961-01-01 至 2026-07-11 |
| 源文件 SHA-256 | `3c562498a7537286815bbd8811d419eb8207ee21d090f61b195351ae2e7c7997` |
| 缺测判定 | 数值 `>=999000` |
| 日照超昼长容差 | 0.05 h |

历史有效样本：Tmin 23,894；K 23,723；UVP 23,751；D 23,722；TI 23,628。C 的既有独立历史检查为 23,629；C 与 TI 所需字段不同，不能用 C 的样本数替代 TI 样本数。

展示精度的分位阈值：UVP 为 36.329、46.897、64.190、87.407；D 为 27.991、45.830、67.151、86.813；TI 为 21.349、36.745、58.937、69.944。实际等级比较使用基准 Excel 的完整精度。所有阈值采用“等于阈值进入更高一档”；内部计算不先对 D/UVP 或 TI 子得分舍入。

## 6. 最小复现步骤

需要支持项目语法和依赖的 Python 3 环境；运行依赖见 `requirements.txt`。所有命令从仓库根目录执行。

```powershell
python -m pip install -r requirements.txt
python .\src\calculate_indices.py --baseline .\data\baseline_tea_card_v2.xlsx --input-json .\examples\forecast.json
```

示例输入为日期 2026-07-20，T=14 ℃，Tmin=6 ℃，RH=45%，V=3 m/s，S=10 h。输出预期为：UVP=88.96，D=19.71，C=75，THI=57.44，K=−385.14，TI=76.06（高）。

复核历史构建时，写入一个新文件，避免覆盖已冻结参数：

```powershell
python .\src\build_baseline.py --history '.\data\SHUJU(1).xlsx' --output .\baseline_verification.xlsx
python .\src\calculate_indices.py --baseline .\baseline_verification.xlsx --input-json .\examples\forecast.json
```

比较重新加载后的分布、完整精度阈值、有效样本数与示例输出，不以 Excel 二进制文件哈希作为两次构建相等的充分判据。原始历史源文件哈希应与上表一致。

CLI 正常情况下输出 UTF-8 JSON。业务错误以 `status="error"` 和 `message` 表示；当前 CLI 的业务错误处理没有显式设置非零退出码，调用方不能仅凭进程退出码判断指数计算成功，应检查 JSON 的 `status`。这是当前实现行为，不是已完成的错误处理改进。

## 7. GUI、EXE 与流程图复现

```powershell
python .\src\tourism_index_gui.py
python -m pip install -r requirements-build.txt
.\tools\build_gui_exe.ps1
```

打包产物为 `dist/TeaCardTourismIndex.exe`，内置 v2 基准。`dist/`、`build/` 与 `.spec` 已被 Git 忽略，克隆仓库不会取得先前本地生成的 EXE；接手者需要重新打包。既有约 11.76 MB 的包体积与启动冒烟检查属于先前环境记录，不代表当前环境已复测。打包脚本应先核验 Tcl/Tk 路径，不能假定换一台机器后路径布局相同。

总流程图脚本为 `docs/flowcharts/render_two_program_workflow.py`；运行后生成 SVG，PNG 需通过支持 SVG 的浏览器或图形工具另行导出。更新图后应同时检查 SVG、PNG 与代码口径。

## 8. 当前实现的检查边界与建议待办

以下条目为供后续讨论和实施的待办，不得描述成当前已有功能：

- 多日 CSV/Excel/JSONL 批量输入与单次加载基准复用。
- 自动化测试：THI/K 九档边界、UVP/D/TI 分位边界、相同历史值、越过历史极值、缺测、非数值、日照容差和闰年日期。
- 数据质量加强：重复日期、日期字段严格类型、Tmin 与 T 的一致性、源数据单位和异常检测；当前代码并未全部检查。
- 基准校验加强：阈值单调性、重复参数行、全部元数据与运行常数一致性及文件内容完整性。当前加载器检查不是全面防篡改机制。
- 错误处理：异常文件格式/JSON 损坏的完整覆盖，以及业务错误的非零退出码。
- 太阳几何沿用固定 365 分母近似；闰年与近似公式适用性应记录并验证，不能静默替换。
- 现有站点固定参数与历史站点元数据变化的关系，需在正式发布前进一步核实。
- 未来若增加安全风险模块、标准 UVI、真实 clo 或游客标签校准，应先确认新增数据与业务定义。

## 9. 给下一位大模型的启动指令

可将以下文字与仓库功能分支链接一起交给下一位模型：

> 请先阅读 docs/AGENT_ONBOARDING.md、docs/METHODOLOGY_SPECIFICATION.md 和 docs/COMPOSITE_INDEX.md，再核对 src/tourism_indices.py 与 data/baseline_tea_card_v2.xlsx。当前项目是逐日气象输入到 UVP、D、C、THI、K、TI 的规则计算，分为历史基准构建和未来预报计算两部分。请先运行 examples/forecast.json，确认 TI=76.06（高）。保留已确认的公式、权重、UVP 中等最佳规则与海拔方案；先说明当前事实、缺失信息和拟变更范围，再实施我提出的新任务。不要把历史记录或建议待办当成已完成功能。
