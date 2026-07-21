# 茶卡盐湖旅游气象指数桌面程序

## 1. 程序用途

`src/tourism_index_gui.py` 是对“程序二：未来逐日预报计算”的桌面界面封装。它不重新构建历史基准，也不读取原始历史工作簿；只读取内置的 `baseline_tea_card_v2.xlsx`，并将一日预报转化为五项旅游气象指数及综合旅游气象指数。

界面包含：

- 景点多选下拉列表：当前仅配置“茶卡盐湖”；
- 六项逐日预报输入：日期、日平均气温、日最低气温、日平均相对湿度、日平均 2 分钟风速、日照时数；
- “运行计算”按钮：按既定规则计算五项指数及其综合旅游气象指数；
- 下方结果窗口：显示完整 UTF-8 JSON 结果；
- “保存结果到本地”按钮：将结果另存为 UTF-8 JSON 文件。

景点列表预留了多选结构，但当前 EXE 只内置茶卡盐湖的冻结历史基准。因此必须选择茶卡盐湖；后续加入其他景点时，必须分别提供其已验证的历史基准，不能复用茶卡基准。

## 2. 从源码运行

在项目根目录执行：

```powershell
python .\src\tourism_index_gui.py
```

源码运行时，程序读取项目中的 `data/baseline_tea_card_v2.xlsx`。

## 3. 打包单文件 EXE

先安装打包依赖：

```powershell
python -m pip install -r requirements-build.txt
```

随后运行项目提供的打包脚本：

```powershell
.\tools\build_gui_exe.ps1
```

生成文件为：

```text
dist\TeaCardTourismIndex.exe
```

脚本以 `--onefile` 生成单个 EXE，以 `--windowed` 隐藏命令行窗口，并使用 `--optimize 2` 去除 Python 文档字符串、启用最高级别字节码优化。它还会自动定位当前 Python 的 Tcl/Tk 资源目录，确保界面所需文件被完整打入 EXE；`--add-data` 会将冻结基准 Excel 内置到 EXE 的临时运行目录。

当前包只包含 GUI、指数计算规则、`openpyxl` 和冻结基准等运行必需内容，不包含历史原始工作簿、流程图或开发工具。`dist/`、`build/` 和 PyInstaller 生成的 `.spec` 文件被 Git 忽略，避免把构建产物误加入源码版本库。

## 4. 操作顺序

1. 启动 `TeaCardTourismIndex.exe`；
2. 在景点下拉菜单中保留“茶卡盐湖”勾选；
3. 输入未来某日的六项逐日预报数据；
4. 点击“运行计算”；
5. 在结果窗口确认五项指数、综合旅游气象指数、等级和基准信息；
6. 点击“保存结果到本地”，选择保存位置。

输入口径、范围与五项指标含义见 [代码使用与计算逻辑说明](使用说明.md)；综合指数的子得分转换、权重与分级见 [综合指数说明](COMPOSITE_INDEX.md)。

## 5. 发布与版本边界

- 当前 EXE 内置的是 `baseline_tea_card_v2.xlsx`，方法版本为 `1.2-composite-index`；
- 历史数据或指标口径更新后，应先运行 `build_baseline.py` 生成新的版本化基准文件，再以新基准重新打包 EXE；
- EXE 只计算气象体验指标，不包含降水、雷电、能见度或其他旅游安全风险；
- UVP 是日照紫外暴露潜势，不是标准 UVI；着装需求是相对保温需求，不是衣物真实厚度或 `clo`。
