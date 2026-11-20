import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from kd_energy import MONTHS, KDEnergyData, kd_analyze_year, kd_calculate_statistics, kd_load_csv, kd_save_csv


DATA_FILE = Path(__file__).resolve().parent / "fogyasztas.csv"


class EnergyApp:
    def __init__(self, root):
        self.root = root
        self.records = []
        self.current_file = DATA_FILE
        self.year_var = tk.StringVar(value="2026")
        self.month_var = tk.StringVar(value=MONTHS[0])
        self.electricity_var = tk.StringVar()
        self.gas_var = tk.StringVar()
        self.chart_var = tk.StringVar(value="Áram (kWh)")
        self.status_var = tk.StringVar(value="Készen áll")
        self.electricity_limit_var = tk.StringVar(value="3000")
        self.gas_limit_var = tk.StringVar(value="1200")
        self.statistics_var = tk.StringVar(value="Még nincs megjeleníthető adat.")
        self.chart_redraw_job = None
        self.build_interface()
        self.open_initial_file()

    def build_interface(self):
        self.root.title("Otthoni energiafogyasztás-elemző")
        available_height = self.root.winfo_screenheight()
        available_width = self.root.winfo_screenwidth()
        self.root.geometry(f"{min(1200, available_width - 80)}x{min(750, available_height - 120)}")
        self.root.minsize(850, 500)

        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        heading = ttk.Frame(main)
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="Otthoni energiafogyasztás-elemző", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(heading, text="Éves elemzés", command=self.open_analysis_window).grid(row=0, column=1, sticky="e")

        entry_frame = ttk.LabelFrame(main, text="Havi fogyasztás megadása", padding=12)
        entry_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        entry_frame.columnconfigure(8, weight=1)

        ttk.Label(entry_frame, text="Év").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(entry_frame, textvariable=self.year_var, width=8).grid(row=0, column=1, padx=(0, 14))
        ttk.Label(entry_frame, text="Hónap").grid(row=0, column=2, padx=(0, 5))
        ttk.Combobox(entry_frame, textvariable=self.month_var, values=MONTHS, width=13, state="readonly").grid(
            row=0, column=3, padx=(0, 14)
        )
        ttk.Label(entry_frame, text="Áram (kWh)").grid(row=0, column=4, padx=(0, 5))
        ttk.Entry(entry_frame, textvariable=self.electricity_var, width=11).grid(row=0, column=5, padx=(0, 14))
        ttk.Label(entry_frame, text="Gáz (m³)").grid(row=0, column=6, padx=(0, 5))
        ttk.Entry(entry_frame, textvariable=self.gas_var, width=11).grid(row=0, column=7, padx=(0, 14))
        ttk.Button(entry_frame, text="Mentés / módosítás", command=self.save_record).grid(row=0, column=8, sticky="e")

        content = ttk.Panedwindow(main, orient="horizontal")
        content.grid(row=2, column=0, sticky="nsew")

        left = ttk.Frame(content, padding=(0, 6, 10, 0))
        right = ttk.Frame(content, padding=(10, 6, 0, 0))
        content.add(left, weight=2)
        content.add(right, weight=3)

        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        table_frame = ttk.LabelFrame(left, text="Rögzített adatok", padding=8)
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.table = ttk.Treeview(
            table_frame, columns=("year", "month", "electricity", "gas"),
            show="headings", selectmode="browse", height=14
        )
        for name, title, width in (
            ("year", "Év", 55), ("month", "Hónap", 110),
            ("electricity", "Áram (kWh)", 95), ("gas", "Gáz (m³)", 95)
        ):
            self.table.heading(name, text=title)
            self.table.column(name, width=width, anchor="center", stretch=True)
        self.table.grid(row=0, column=0, sticky="nsew")
        self.table.bind("<<TreeviewSelect>>", self.select_record)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)

        table_buttons = ttk.Frame(left)
        table_buttons.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        ttk.Button(table_buttons, text="Kijelölt törlése", command=self.delete_record).pack(side="left", padx=(0, 6))
        ttk.Button(table_buttons, text="Mezők ürítése", command=self.clear_fields).pack(side="left")

        file_buttons = ttk.LabelFrame(left, text="CSV fájl", padding=8)
        file_buttons.grid(row=2, column=0, sticky="ew")
        ttk.Button(file_buttons, text="CSV megnyitása", command=self.import_csv).pack(side="left", padx=(0, 6))
        ttk.Button(file_buttons, text="Mentés másként", command=self.export_csv).pack(side="left")

        tabs = ttk.Notebook(right)
        tabs.grid(row=0, column=0, sticky="nsew")
        graph_tab = ttk.Frame(tabs, padding=8)
        analysis_tab = ttk.Frame(tabs, padding=8)
        tabs.add(graph_tab, text="Grafikon és statisztika")
        tabs.add(analysis_tab, text="Éves fogyasztásfigyelő")
        graph_tab.columnconfigure(0, weight=1)
        graph_tab.rowconfigure(1, weight=1)
        analysis_tab.columnconfigure(0, weight=1)
        analysis_tab.rowconfigure(1, weight=1)

        chart_header = ttk.Frame(graph_tab)
        chart_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(chart_header, text="Grafikon:").pack(side="left", padx=(0, 6))
        ttk.Combobox(
            chart_header, textvariable=self.chart_var, values=("Áram (kWh)", "Gáz (m³)"),
            state="readonly", width=16
        ).pack(side="left")
        ttk.Button(chart_header, text="Grafikon frissítése", command=self.refresh_chart).pack(side="left", padx=8)

        figure_frame = ttk.LabelFrame(graph_tab, text="Fogyasztási grafikon", padding=6)
        figure_frame.grid(row=1, column=0, sticky="nsew")
        self.canvas = tk.Canvas(figure_frame, background="white", highlightthickness=0, height=280)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.schedule_chart_redraw)
        self.root.bind("<Configure>", self.on_window_resize)

        statistics_frame = ttk.LabelFrame(graph_tab, text="Statisztika", padding=10)
        statistics_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(statistics_frame, textvariable=self.statistics_var, justify="left", wraplength=500).pack(anchor="w")

        controls = ttk.LabelFrame(analysis_tab, text="Éves fogyasztási keretek", padding=10)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(controls, text="Éves áramkeret (kWh)").pack(side="left")
        ttk.Entry(controls, textvariable=self.electricity_limit_var, width=8).pack(side="left", padx=(5, 12))
        ttk.Label(controls, text="Gázkeret (m³)").pack(side="left")
        ttk.Entry(controls, textvariable=self.gas_limit_var, width=8).pack(side="left", padx=(5, 12))
        ttk.Button(controls, text="Év elemzése", command=self.refresh_analysis).pack(side="left")

        analysis_frame = ttk.LabelFrame(analysis_tab, text="Elemzés és figyelmeztetések", padding=8)
        analysis_frame.grid(row=1, column=0, sticky="nsew")
        analysis_frame.rowconfigure(0, weight=1)
        analysis_frame.columnconfigure(0, weight=1)
        self.analysis_text = tk.Text(analysis_frame, height=12, wrap="word", font=("Segoe UI", 10), relief="flat", background="#f6f7f9", padx=8, pady=8)
        self.analysis_text.grid(row=0, column=0, sticky="nsew")
        analysis_scroll = ttk.Scrollbar(analysis_frame, orient="vertical", command=self.analysis_text.yview)
        analysis_scroll.grid(row=0, column=1, sticky="ns")
        self.analysis_text.configure(yscrollcommand=analysis_scroll.set, state="disabled")
        tabs.bind("<<NotebookTabChanged>>", lambda event: self.schedule_chart_redraw() if tabs.index(tabs.select()) == 0 else None)

        ttk.Label(main, textvariable=self.status_var, relief="sunken", anchor="w", padding=5).grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )
        self.chart_var.trace_add("write", lambda *_: self.refresh_chart())
        self.year_var.trace_add("write", lambda *_: self.refresh_analysis())

    def open_initial_file(self):
        try:
            self.records = kd_load_csv(self.current_file)
            self.status_var.set(f"Adatfájl: {self.current_file.name} ({len(self.records)} hónap)")
        except (OSError, ValueError) as error:
            messagebox.showerror("Adatbetöltési hiba", str(error))
            self.status_var.set("Nem sikerült betölteni az adatfájlt.")
        self.refresh_all()

    def save_record(self):
        try:
            year = int(self.year_var.get().strip())
            month = MONTHS.index(self.month_var.get()) + 1
            electricity = float(self.electricity_var.get().strip().replace(",", "."))
            gas = float(self.gas_var.get().strip().replace(",", "."))
            record = KDEnergyData(year, month, electricity, gas)
        except (ValueError, OverflowError) as error:
            messagebox.showerror("Hibás adat", f"Ellenőrizd a megadott értékeket!\n{error}")
            return

        updated = [item for item in self.records if (item.year, item.month) != (year, month)]
        updated.append(record)
        if not self.persist(updated):
            return
        self.records = sorted(updated, key=lambda item: (item.year, item.month))
        self.refresh_all()
        self.status_var.set(f"Mentve: {year}. {MONTHS[month - 1]} – {self.current_file.name}")

    def delete_record(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Nincs kijelölés", "Először jelölj ki egy sort!")
            return
        year, month = map(int, selection[0].split("-"))
        if not messagebox.askyesno("Törlés megerősítése", f"Töröljük ezt a hónapot: {year}. {MONTHS[month - 1]}?"):
            return
        updated = [item for item in self.records if (item.year, item.month) != (year, month)]
        if not self.persist(updated):
            return
        self.records = updated
        self.refresh_all()
        self.status_var.set("A kijelölt hónapot töröltük.")

    def persist(self, records):
        try:
            kd_save_csv(self.current_file, records)
            return True
        except OSError as error:
            messagebox.showerror("Mentési hiba", str(error))
            return False

    def select_record(self, event=None):
        selection = self.table.selection()
        if not selection:
            return
        year, month = map(int, selection[0].split("-"))
        record = next((item for item in self.records if (item.year, item.month) == (year, month)), None)
        if record is None:
            return
        self.year_var.set(str(record.year))
        self.month_var.set(MONTHS[record.month - 1])
        self.electricity_var.set(str(record.electricity))
        self.gas_var.set(str(record.gas))
        self.refresh_analysis()

    def clear_fields(self):
        self.electricity_var.set("")
        self.gas_var.set("")
        for item in self.table.selection():
            self.table.selection_remove(item)

    def import_csv(self):
        filename = filedialog.askopenfilename(title="CSV megnyitása", filetypes=[("CSV-fájlok", "*.csv")])
        if not filename:
            return
        try:
            loaded = kd_load_csv(filename)
        except (OSError, ValueError) as error:
            messagebox.showerror("Betöltési hiba", str(error))
            return
        self.records = loaded
        self.current_file = Path(filename)
        self.refresh_all()
        self.status_var.set(f"Betöltve: {self.current_file.name} ({len(self.records)} hónap)")

    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="CSV mentése másként", defaultextension=".csv",
            filetypes=[("CSV-fájlok", "*.csv")], initialfile="fogyasztas_masolat.csv"
        )
        if not filename:
            return
        try:
            kd_save_csv(filename, self.records)
        except OSError as error:
            messagebox.showerror("Mentési hiba", str(error))
            return
        self.status_var.set(f"CSV mentve: {filename}")

    def refresh_all(self):
        for item in self.table.get_children():
            self.table.delete(item)
        for record in sorted(self.records, key=lambda row: (row.year, row.month)):
            self.table.insert(
                "", "end", iid=f"{record.year}-{record.month}",
                values=(record.year, MONTHS[record.month - 1],
                        f"{record.electricity:.1f}", f"{record.gas:.1f}")
            )
        self.refresh_chart()
        self.refresh_analysis()

    def refresh_analysis(self):
        try:
            year = int(self.year_var.get().strip())
            electricity_limit = float(self.electricity_limit_var.get().strip().replace(",", "."))
            gas_limit = float(self.gas_limit_var.get().strip().replace(",", "."))
            report = kd_analyze_year(self.records, year, electricity_limit, gas_limit)
        except (ValueError, OverflowError) as error:
            self.set_analysis_text(f"Hibás év vagy éves keret: {error}")
            return

        lines = [f"{year}. év – {report['months']} rögzített hónap"]
        if report["months"] == 0:
            lines.append("Ehhez az évhez még nincs adat.")
            self.set_analysis_text("\n".join(lines))
            return
        for field, title, unit in (("electricity", "Áram", "kWh"), ("gas", "Gáz", "m³")):
            item = report[field]
            line = f"{title}: eddig {item['total']:.0f} {unit} / keret {item['limit']:.0f} {unit}"
            if item["projection"] is None:
                line += " | becsléshez legalább 3 hónap kell"
            else:
                line += f" | éves becslés {item['projection']:.0f} {unit}"
            if item["over_limit"]:
                line += " | FIGYELMEZTETÉS: várható túllépés!"
            lines.append(line)
        matches = report["comparisons"]
        if matches:
            month, field, change = matches[-1]
            unit = "áram" if field == "electricity" else "gáz"
            lines.append(f"Előző évhez képest ({MONTHS[month - 1]}, {unit}): {change:+.1f}%")
        else:
            lines.append("Előző éves összevetés: nincs azonos havi adat.")
        if report["alerts"]:
            for month, field, change, baseline in report["alerts"][-3:]:
                name = "áram" if field == "electricity" else "gáz"
                lines.append(f"KIUGRÁS: {MONTHS[month - 1]} ({name}) +{change:.0f}% az {baseline} értékéhez képest")
        else:
            lines.append("Nincs 30%-nál nagyobb kiugrás az összehasonlítható adatokban.")
        lines.append("Becslés: havi átlag × 12; szezonális fogyasztásnál pontatlan lehet.")
        self.set_analysis_text("\n".join(lines))

    def open_analysis_window(self):
        self.refresh_analysis()
        window = tk.Toplevel(self.root)
        window.title("Éves fogyasztásfigyelő – részletes elemzés")
        window.geometry("750x440")
        window.minsize(480, 300)
        panel = ttk.Frame(window, padding=12)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Éves energiafogyasztási elemzés", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        controls = ttk.Frame(panel)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Éves áramkeret (kWh)").pack(side="left")
        ttk.Entry(controls, textvariable=self.electricity_limit_var, width=9).pack(side="left", padx=(5, 12))
        ttk.Label(controls, text="Gázkeret (m³)").pack(side="left")
        ttk.Entry(controls, textvariable=self.gas_limit_var, width=9).pack(side="left", padx=(5, 12))
        report_frame = ttk.Frame(panel)
        report_frame.pack(fill="both", expand=True)
        report = tk.Text(report_frame, wrap="word", font=("Segoe UI", 11), padx=12, pady=12)
        scroll = ttk.Scrollbar(report_frame, orient="vertical", command=report.yview)
        report.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        report.pack(side="left", fill="both", expand=True)

        def update_report():
            self.refresh_analysis()
            report.configure(state="normal")
            report.delete("1.0", "end")
            report.insert("1.0", self.analysis_text.get("1.0", "end-1c"))
            report.configure(state="disabled")

        ttk.Button(controls, text="Elemzés frissítése", command=update_report).pack(side="left")
        update_report()

    def set_analysis_text(self, value):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", value)
        self.analysis_text.configure(state="disabled")

    def on_window_resize(self, event):
        if event.widget == self.root:
            self.schedule_chart_redraw()

    def schedule_chart_redraw(self, event=None):
        if self.chart_redraw_job is not None:
            self.root.after_cancel(self.chart_redraw_job)
        self.chart_redraw_job = self.root.after(120, self.refresh_chart)

    def refresh_chart(self, event=None):
        if self.chart_redraw_job is not None:
            self.root.after_cancel(self.chart_redraw_job)
            self.chart_redraw_job = None
        if not self.canvas.winfo_ismapped():
            return
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 120 or height < 120:
            self.schedule_chart_redraw()
            return
        self.canvas.delete("all")

        electricity_mode = self.chart_var.get() == "Áram (kWh)"
        records = sorted(self.records, key=lambda item: (item.year, item.month))
        values = [item.electricity if electricity_mode else item.gas for item in records]
        unit = "kWh" if electricity_mode else "m³"
        title = "Áramfogyasztás" if electricity_mode else "Gázfogyasztás"
        color = "#3678bd" if electricity_mode else "#de8b38"

        self.canvas.create_text(width // 2, 22, text=f"{title} ({unit})", font=("Segoe UI", 12, "bold"))
        if not values:
            self.canvas.create_text(width // 2, height // 2, text="Még nincs rögzített adat")
            self.statistics_var.set("Még nincs megjeleníthető adat.")
            return

        result = kd_calculate_statistics(values)
        self.statistics_var.set(
            f"Hónapok száma: {result['count']}   |   Összesen: {result['total']:.1f} {unit}\n"
            f"Átlag: {result['average']:.1f} {unit}   |   Medián: {result['median']:.1f} {unit}\n"
            f"Minimum: {result['minimum']:.1f} {unit}   |   Maximum: {result['maximum']:.1f} {unit}\n"
            f"Szórás: {result['deviation']:.1f} {unit}"
        )

        displayed = records[-12:]
        points = [item.electricity if electricity_mode else item.gas for item in displayed]
        left, right, top, bottom = 55, width - 18, 52, height - 64
        chart_width = max(1, right - left)
        chart_height = max(1, bottom - top)
        maximum = max(points)
        scale = maximum * 1.15 if maximum > 0 else 1

        for i in range(5):
            level = scale * i / 4
            y = bottom - chart_height * i / 4
            self.canvas.create_line(left, y, right, y, fill="#e6e9ed")
            self.canvas.create_text(left - 7, y, text=f"{level:.0f}", anchor="e", font=("Segoe UI", 9))

        self.canvas.create_line(left, top, left, bottom, fill="#777777")
        self.canvas.create_line(left, bottom, right, bottom, fill="#777777")
        step = chart_width / len(displayed)
        bar_width = min(42, step * 0.7)
        for index, (record, value) in enumerate(zip(displayed, points)):
            x = left + step * (index + 0.5)
            y = bottom - (value / scale) * chart_height
            self.canvas.create_rectangle(x - bar_width / 2, y, x + bar_width / 2, bottom, fill=color, outline="")
            self.canvas.create_text(x, bottom + 14, text=f"{record.month:02d}.", font=("Segoe UI", 8))
            self.canvas.create_text(x, bottom + 28, text=str(record.year), font=("Segoe UI", 8))
            if step >= 31:
                self.canvas.create_text(x, max(top + 8, y - 10), text=f"{value:.0f}", font=("Segoe UI", 8))

        if len(records) > 12:
            self.canvas.create_text(width // 2, height - 9, text="A grafikon az utolsó 12 hónapot mutatja.", font=("Segoe UI", 9))


if __name__ == "__main__":
    root = tk.Tk()
    app = EnergyApp(root)
    root.mainloop()
