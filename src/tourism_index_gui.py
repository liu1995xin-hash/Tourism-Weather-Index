#!/usr/bin/env python3
"""Desktop GUI for calculating the five Tea Card tourism-weather indices."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from tourism_indices import InputError, calculate_indices, load_baseline_xlsx


APP_TITLE = "茶卡盐湖旅游气象指数计算器"
SCENIC_SPOTS = ("茶卡盐湖",)


def resource_path(relative_path: str) -> Path:
    """Find a bundled resource in an EXE, or the project resource when run from source."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return root / relative_path


class TourismIndexApp(tk.Tk):
    """One-day forecast calculator backed by the packaged Tea Card baseline."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1040x790")
        self.minsize(900, 660)
        self.baseline_path = resource_path("data/baseline_tea_card_v2.xlsx")
        self.baseline = None
        self.latest_result: dict | None = None
        self.spot_vars = {spot: tk.BooleanVar(value=(spot == "茶卡盐湖")) for spot in SCENIC_SPOTS}
        self.inputs: dict[str, ttk.Entry] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 17, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Run.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=(18, 8))

        main = ttk.Frame(self, padding=18)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        ttk.Label(main, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            main,
            text="填写未来某日的逐日预报数据，系统将读取内置的茶卡盐湖历史基准并输出五项指数及综合旅游气象指数。",
        ).grid(row=1, column=0, sticky="w", pady=(3, 14))

        input_frame = ttk.LabelFrame(main, text="预报输入", style="Section.TLabelframe", padding=14)
        input_frame.grid(row=2, column=0, sticky="ew")
        for column in (1, 3, 5):
            input_frame.columnconfigure(column, weight=1)

        self._add_spot_selector(input_frame)
        fields = (
            ("date", "预报日期", "YYYY-MM-DD", date.today().isoformat()),
            ("avg_temp", "日平均气温", "℃", ""),
            ("min_temp", "日最低气温", "℃", ""),
            ("avg_rh", "日平均相对湿度", "%", ""),
            ("avg_wind", "日平均2分钟风速", "m/s", ""),
            ("sunshine_hours", "日照时数", "小时", ""),
        )
        for index, (key, label, unit, default) in enumerate(fields):
            row = 1 + index // 3
            column = (index % 3) * 2
            ttk.Label(input_frame, text=label).grid(row=row, column=column, sticky="e", padx=(0, 7), pady=8)
            entry = ttk.Entry(input_frame, width=22)
            entry.insert(0, default)
            entry.grid(row=row, column=column + 1, sticky="ew", pady=8)
            self.inputs[key] = entry
            ttk.Label(input_frame, text=unit, foreground="#555555").grid(
                row=row, column=column + 1, sticky="e", padx=(0, 5), pady=8
            )

        action_frame = ttk.Frame(main)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(14, 10))
        action_frame.columnconfigure(1, weight=1)
        ttk.Button(action_frame, text="运行计算", style="Run.TButton", command=self.calculate).grid(
            row=0, column=0, sticky="w"
        )
        self.status_var = tk.StringVar(value="请填写预报数据后点击“运行计算”。")
        ttk.Label(action_frame, textvariable=self.status_var).grid(row=0, column=1, sticky="w", padx=16)
        self.save_button = ttk.Button(action_frame, text="保存结果到本地", command=self.save_result, state="disabled")
        self.save_button.grid(row=0, column=2, sticky="e")

        result_frame = ttk.LabelFrame(main, text="计算结果", style="Section.TLabelframe", padding=10)
        result_frame.grid(row=4, column=0, sticky="nsew")
        main.rowconfigure(4, weight=1)
        self.result_text = ScrolledText(
            result_frame,
            wrap="word",
            height=22,
            font=("Microsoft YaHei UI", 10),
            state="disabled",
            background="#FFFFFF",
        )
        self.result_text.pack(fill="both", expand=True)

    def _add_spot_selector(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(parent, text="景点").grid(row=0, column=0, sticky="e", padx=(0, 7), pady=(0, 8))
        self.spot_menu = ttk.Menubutton(parent, text="茶卡盐湖", direction="below")
        menu = tk.Menu(self.spot_menu, tearoff=False)
        for spot in SCENIC_SPOTS:
            menu.add_checkbutton(label=spot, variable=self.spot_vars[spot], command=self._update_spot_text)
        self.spot_menu["menu"] = menu
        self.spot_menu.grid(row=0, column=1, sticky="w", pady=(0, 8))
        ttk.Label(parent, text="多选下拉列表（当前仅配置茶卡盐湖）", foreground="#555555").grid(
            row=0, column=2, columnspan=4, sticky="w", padx=12, pady=(0, 8)
        )

    def _update_spot_text(self) -> None:
        selected = self._selected_spots()
        self.spot_menu.configure(text="、".join(selected) if selected else "请选择景点")

    def _selected_spots(self) -> list[str]:
        return [spot for spot, variable in self.spot_vars.items() if variable.get()]

    def _forecast(self) -> dict[str, str]:
        return {key: entry.get().strip() for key, entry in self.inputs.items()}

    def _get_baseline(self):
        if self.baseline is None:
            if not self.baseline_path.is_file():
                raise InputError(f"未找到内置基准文件：{self.baseline_path}")
            self.baseline = load_baseline_xlsx(self.baseline_path)
        return self.baseline

    def calculate(self) -> None:
        selected = self._selected_spots()
        if not selected:
            messagebox.showwarning(APP_TITLE, "请至少选择一个景点。")
            return
        if selected != ["茶卡盐湖"]:
            messagebox.showerror(APP_TITLE, "当前版本仅内置茶卡盐湖的历史基准。")
            return
        try:
            result = calculate_indices(self._forecast(), self._get_baseline())
        except (InputError, OSError) as exc:
            self.latest_result = None
            self.save_button.configure(state="disabled")
            self.status_var.set("计算失败：请检查输入参数。")
            messagebox.showerror("无法计算", str(exc))
            return

        result["application"] = {"scenic_spots": selected, "calculator": APP_TITLE}
        self.latest_result = result
        self._show_result(result)
        self.save_button.configure(state="normal")
        self.status_var.set("计算完成。可查看结果或保存为 JSON 文件。")

    def _show_result(self, result: dict) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", json.dumps(result, ensure_ascii=False, indent=2))
        self.result_text.configure(state="disabled")

    def save_result(self) -> None:
        if self.latest_result is None:
            return
        default_date = self.latest_result["input"]["date"]
        target = filedialog.asksaveasfilename(
            title="保存旅游气象指数结果",
            defaultextension=".json",
            initialfile=f"茶卡盐湖旅游气象指数_{default_date}.json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not target:
            return
        try:
            Path(target).write_text(json.dumps(self.latest_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        self.status_var.set(f"结果已保存：{target}")
        messagebox.showinfo(APP_TITLE, "结果已保存到本地。")


def main() -> None:
    app = TourismIndexApp()
    app.mainloop()


if __name__ == "__main__":
    main()
