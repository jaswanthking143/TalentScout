"""
TrendScout Tkinter GUI
- Load profiles from data/sample_candidates.json
- Enter role name and comma-separated required skills
- Compute suitability scores and show ranked list
- Select a candidate to view details
- Visualize top-k suitability scores (bar chart)
- Export the report (uses trend_scout.report.generate_report)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import logging

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data_loader import load_profiles_from_json, profiles_to_dataframe
from recommender import Recommender
from report import generate_report
from utils import get_logger, TrendScoutError

logger = get_logger("trendscout.gui")

DEFAULT_DATA_PATH = "data/sample_candidates.json"


class TrendScoutGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TrendScout — Talent Visualization")
        self.geometry("1000x700")
        self.resizable(True, True)

        self.profiles = []
        self.df = None
        self.scored_df = None

        self._build_ui()
        self.load_data(DEFAULT_DATA_PATH)

    def _build_ui(self):
        # Top frame: inputs
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=8, pady=6)

        ttk.Label(top_frame, text="Data file:").grid(row=0, column=0, sticky="w")
        self.data_path_var = tk.StringVar(value=DEFAULT_DATA_PATH)
        self.data_entry = ttk.Entry(top_frame, textvariable=self.data_path_var, width=60)
        self.data_entry.grid(row=0, column=1, sticky="w")
        ttk.Button(top_frame, text="Browse", command=self.browse_data).grid(row=0, column=2, padx=4)

        ttk.Label(top_frame, text="Role name:").grid(row=1, column=0, sticky="w", pady=4)
        self.role_var = tk.StringVar(value="Senior Data Analyst")
        ttk.Entry(top_frame, textvariable=self.role_var, width=40).grid(row=1, column=1, sticky="w")

        ttk.Label(top_frame, text="Required skills (comma-separated):").grid(row=2, column=0, sticky="w")
        self.skills_var = tk.StringVar(value="python,sql,pandas")
        ttk.Entry(top_frame, textvariable=self.skills_var, width=60).grid(row=2, column=1, sticky="w")

        ttk.Button(top_frame, text="Analyze", command=self.run_analysis_thread).grid(row=1, column=2, rowspan=2, padx=6)

        # Middle frame: results list and details
        mid_frame = ttk.Panedwindow(self, orient="horizontal")
        mid_frame.pack(fill="both", expand=True, padx=8, pady=6)

        left_panel = ttk.Frame(mid_frame, width=300)
        right_panel = ttk.Frame(mid_frame)

        mid_frame.add(left_panel, weight=1)
        mid_frame.add(right_panel, weight=3)

        # Left: list of candidates
        ttk.Label(left_panel, text="Ranked Candidates:").pack(anchor="w")
        self.cand_listbox = tk.Listbox(left_panel, height=20)
        self.cand_listbox.pack(fill="both", expand=True, pady=4)
        self.cand_listbox.bind("<<ListboxSelect>>", self.on_candidate_select)

        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Top 5", command=lambda: self.plot_top_k(5)).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Top 10", command=lambda: self.plot_top_k(10)).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Export Report", command=self.export_report).pack(side="right", padx=4)

        # Right: details and chart
        details_frame = ttk.Frame(right_panel)
        details_frame.pack(fill="x", pady=4)
        ttk.Label(details_frame, text="Candidate Details:").pack(anchor="w")
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill="x", padx=2, pady=2)

        chart_frame = ttk.Frame(right_panel)
        chart_frame.pack(fill="both", expand=True, pady=6)
        ttk.Label(chart_frame, text="Suitability Scores:").pack(anchor="w")

        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def browse_data(self):
        path = filedialog.askopenfilename(title="Select data JSON", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            self.data_path_var.set(path)
            self.load_data(path)

    def load_data(self, path):
        try:
            self.profiles = load_profiles_from_json(path)
            self.df = profiles_to_dataframe(self.profiles)
            self.status_var.set(f"Loaded {len(self.profiles)} profiles from {path}")
            logger.info("Loaded %d profiles", len(self.profiles))
        except Exception as e:
            logger.exception("Failed to load data: %s", e)
            messagebox.showerror("Error", f"Failed to load data: {e}")
            self.status_var.set("Error loading data")

    def run_analysis_thread(self):
        t = threading.Thread(target=self.run_analysis, daemon=True)
        t.start()

    def run_analysis(self):
        role_name = self.role_var.get().strip()
        skills_raw = self.skills_var.get().strip()
        required_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        if self.df is None:
            messagebox.showwarning("No data", "No data loaded.")
            return

        self.status_var.set("Running analysis...")
        try:
            weights = {
                "skill_match": 0.45,
                "norm_perf": 0.3,
                "norm_experience": 0.15,
                "norm_achievements": 0.05,
                "norm_on_time": 0.05
            }
            recommender = Recommender(self.df, weights=weights)
            self.scored_df = recommender.compute_suitability(required_skills)
            self.update_listbox()
            self.plot_top_k(10)
            self.status_var.set(f"Analysis complete for role '{role_name}' ({len(self.scored_df)} profiles)")
            logger.info("Analysis complete for role %s", role_name)
        except Exception as e:
            logger.exception("Analysis failed: %s", e)
            messagebox.showerror("Analysis error", f"Analysis failed: {e}")
            self.status_var.set("Analysis error")

    def update_listbox(self):
        self.cand_listbox.delete(0, tk.END)
        if self.scored_df is None or len(self.scored_df) == 0:
            return
        for i, row in self.scored_df.iterrows():
            display = f"{i+1}. {row['name']} ({row['type']}) — score: {row['suitability_score']:.3f}"
            self.cand_listbox.insert(tk.END, display)

    def on_candidate_select(self, event):
        if not self.scored_df is None and self.cand_listbox.curselection():
            idx = self.cand_listbox.curselection()[0]
            row = self.scored_df.iloc[idx]
            details = (
                f"ID: {row['id']}\n"
                f"Name: {row['name']}\n"
                f"Type: {row['type']}\n"
                f"Years experience: {row['years_experience']}\n"
                f"Avg performance score: {row['avg_performance_score']}\n"
                f"Suitability score: {row['suitability_score']:.3f}\n"
                f"Skill match: {row['skill_match']:.2f}\n"
                f"Achievement impact: {row['achievement_impact']}\n"
                f"Projects delivered: {row['projects_delivered']}\n"
                f"On-time rate: {row['on_time_rate']}\n"
                f"Skills: {', '.join(row['skills'])}\n"
                f"Certifications: {', '.join(row.get('certifications') or [])}\n"
            )
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, details)

    def plot_top_k(self, k=10):
        if self.scored_df is None:
            return
        top = self.scored_df.head(k)
        names = top["name"].tolist()
        scores = top["suitability_score"].tolist()

        self.ax.clear()
        bars = self.ax.barh(range(len(names))[::-1], scores[::-1], color="tab:blue")
        self.ax.set_yticks(range(len(names))[::-1])
        self.ax.set_yticklabels(names[::-1])
        self.ax.set_xlabel("Suitability score")
        self.ax.set_xlim(0, 1.0)
        self.ax.set_title(f"Top {min(k, len(names))} candidates")
        for i, b in enumerate(bars):
            w = b.get_width()
            self.ax.text(w + 0.01, b.get_y() + b.get_height()/2, f"{scores[::-1][i]:.2f}", va="center", fontsize=9)
        self.fig.tight_layout()
        self.canvas.draw()

    def export_report(self):
        if self.scored_df is None:
            messagebox.showwarning("No results", "Run analysis before exporting a report.")
            return
        role_name = self.role_var.get().strip()
        skills_raw = self.skills_var.get().strip()
        required_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        try:
            out = generate_report(self.scored_df, role_name, required_skills, out_dir="output")
            messagebox.showinfo("Report exported", f"Report files: {out}")
            self.status_var.set(f"Report exported to {out['json']} and {out['csv']}")
        except Exception as e:
            logger.exception("Failed to export report: %s", e)
            messagebox.showerror("Export error", f"Failed to export report: {e}")
            self.status_var.set("Export error")


if __name__ == "__main__":
    try:
        app = TrendScoutGUI()
        app.mainloop()
    except TrendScoutError as te:
        logger.exception("TrendScout error: %s", te)
        print("Error:", te)
    except Exception as e:
        logger.exception("Unhandled error in GUI: %s", e)
        print("Unhandled error:", e)