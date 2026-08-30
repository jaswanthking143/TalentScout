"""
gui.py
Tkinter desktop interface for TalentScout Resume Analyzer.

Flow:
  1. App opens on an About screen: project name + a short description of
     what TalentScout does. HR user clicks "Enter TalentScout" to continue.
  2. HR user clicks "Upload Resumes (PDF)" -> selects one or more .pdf files.
  3. Each resume is parsed and shown as a row: Name | Email | Phone | Skills | Experience.
  4. HR user types a target role (e.g. "Python Developer"), picks how many
     top candidates to keep (Top 5 / Top 10 / custom), and clicks "Analyze".
  5. Results are scored, ranked, and saved to an .xlsx workbook (cover sheet
     with the project info + a Results sheet with the top-N ranked candidates).
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pdf_parser import parse_resume
from analyzer import analyze_candidates
from exceptions import TalentScoutError
from excel_export import export_candidates_to_excel, PROJECT_NAME, PROJECT_TAGLINE, PROJECT_DESCRIPTION
from logger_config import get_logger

logger = get_logger(__name__)

# ---- Theme (matches the navy / mint "dev terminal" palette) --------------
BG_DARK = "#0a192f"
BG_PANEL = "#112240"
FG_TEXT = "#ccd6f6"
FG_MUTED = "#8892b0"
ACCENT = "#64ffda"
ACCENT_DIM = "#4fd1b5"
ROW_ALT = "#0e2038"
DANGER = "#ff6b6b"

TOP_N_CHOICES = ["Top 5", "Top 10", "Custom"]


class TalentScoutApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TalentScout — Resume Analyzer")
        self.root.geometry("1080x640")
        self.root.configure(bg=BG_DARK)
        self.root.minsize(860, 520)

        self.candidates = []  # list[Candidate]

        self._build_style()
        self._build_intro_screen()
        self._build_main_frame()  # built up front, shown after intro

        self.intro_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Styling
    # ------------------------------------------------------------------ #
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)

        style.configure(
            "Treeview",
            background=BG_PANEL,
            fieldbackground=BG_PANEL,
            foreground=FG_TEXT,
            rowheight=28,
            borderwidth=0,
            font=("Consolas", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#0d1f38",
            foreground=ACCENT,
            font=("Consolas", 10, "bold"),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#1d3a63")])

        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground=BG_DARK,
            font=("Consolas", 10, "bold"),
            padding=8,
            borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", ACCENT_DIM)])

        style.configure(
            "Secondary.TButton",
            background="#1d3a63",
            foreground=FG_TEXT,
            font=("Consolas", 10),
            padding=8,
            borderwidth=0,
        )
        style.map("Secondary.TButton", background=[("active", "#274a7d")])

        style.configure(
            "TopN.TCombobox",
            fieldbackground=BG_PANEL,
            background=BG_PANEL,
            foreground=FG_TEXT,
            arrowcolor=ACCENT,
        )

    # ------------------------------------------------------------------ #
    # About / intro screen
    # ------------------------------------------------------------------ #
    def _build_intro_screen(self):
        self.intro_frame = tk.Frame(self.root, bg=BG_DARK)

        wrapper = tk.Frame(self.intro_frame, bg=BG_DARK)
        wrapper.place(relx=0.5, rely=0.5, anchor="center", width=760)

        tk.Label(
            wrapper, text=PROJECT_NAME, fg=ACCENT, bg=BG_DARK,
            font=("Consolas", 32, "bold"),
        ).pack(pady=(0, 4))

        tk.Label(
            wrapper, text=PROJECT_TAGLINE, fg=FG_MUTED, bg=BG_DARK,
            font=("Consolas", 13, "italic"),
        ).pack(pady=(0, 24))

        desc_panel = tk.Frame(wrapper, bg=BG_PANEL, highlightbackground="#1d3a63", highlightthickness=1)
        desc_panel.pack(fill="x", pady=(0, 28))

        for para in PROJECT_DESCRIPTION.split("\n\n"):
            tk.Label(
                desc_panel, text=para, fg=FG_TEXT, bg=BG_PANEL,
                font=("Consolas", 11), justify="left", wraplength=700, anchor="w",
            ).pack(fill="x", padx=20, pady=(14, 0))
        tk.Frame(desc_panel, bg=BG_PANEL, height=14).pack()

        ttk.Button(
            wrapper, text="Enter TalentScout  →", style="Accent.TButton",
            command=self._show_main_app,
        ).pack()

    def _show_main_app(self):
        self.intro_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Main app layout
    # ------------------------------------------------------------------ #
    def _build_main_frame(self):
        self.main_frame = tk.Frame(self.root, bg=BG_DARK)

        # Header
        header = tk.Frame(self.main_frame, bg=BG_DARK)
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(
            header, text="TalentScout", fg=ACCENT, bg=BG_DARK,
            font=("Consolas", 20, "bold"),
        ).pack(side="left")
        tk.Label(
            header, text="  Resume Intake & Role-Fit Analyzer", fg=FG_MUTED, bg=BG_DARK,
            font=("Consolas", 12),
        ).pack(side="left", padx=(6, 0))

        ttk.Button(
            header, text="ℹ  About", style="Secondary.TButton",
            command=self._back_to_intro,
        ).pack(side="right")

        # Toolbar
        toolbar = tk.Frame(self.main_frame, bg=BG_DARK)
        toolbar.pack(fill="x", padx=20, pady=(0, 10))

        ttk.Button(
            toolbar, text="⬆  Upload Resumes (PDF)", style="Accent.TButton",
            command=self.upload_resumes,
        ).pack(side="left")

        ttk.Button(
            toolbar, text="🗑  Clear All", style="Secondary.TButton",
            command=self.clear_all,
        ).pack(side="left", padx=(10, 0))

        self.count_label = tk.Label(
            toolbar, text="0 candidates loaded", fg=FG_MUTED, bg=BG_DARK,
            font=("Consolas", 10),
        )
        self.count_label.pack(side="right")

        # Table
        table_frame = tk.Frame(self.main_frame, bg=BG_PANEL)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        columns = ("name", "email", "phone", "skills", "experience")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "name": ("Name", 150),
            "email": ("Email", 200),
            "phone": ("Contact", 120),
            "skills": ("Skills", 340),
            "experience": ("Experience", 160),
        }
        for col, (label, width) in headings.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("odd", background=BG_PANEL)
        self.tree.tag_configure("even", background=ROW_ALT)

        # Analyze bar
        analyze_bar = tk.Frame(self.main_frame, bg=BG_DARK)
        analyze_bar.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(
            analyze_bar, text="Required Role:", fg=FG_TEXT, bg=BG_DARK,
            font=("Consolas", 11),
        ).pack(side="left")

        self.role_entry = tk.Entry(
            analyze_bar, font=("Consolas", 11), bg=BG_PANEL, fg=FG_TEXT,
            insertbackground=ACCENT, relief="flat", width=26,
        )
        self.role_entry.pack(side="left", padx=10, ipady=4)
        self.role_entry.insert(0, "e.g. Python Developer")
        self.role_entry.bind("<FocusIn>", self._clear_placeholder)
        self.role_entry.bind("<Return>", lambda e: self.run_analysis())

        tk.Label(
            analyze_bar, text="Show:", fg=FG_TEXT, bg=BG_DARK,
            font=("Consolas", 11),
        ).pack(side="left", padx=(6, 0))

        self.top_n_choice = ttk.Combobox(
            analyze_bar, values=TOP_N_CHOICES, state="readonly",
            width=9, style="TopN.TCombobox", font=("Consolas", 10),
        )
        self.top_n_choice.current(0)  # default: Top 5
        self.top_n_choice.pack(side="left", padx=(8, 4), ipady=2)
        self.top_n_choice.bind("<<ComboboxSelected>>", self._on_top_n_change)

        self.top_n_custom = tk.Spinbox(
            analyze_bar, from_=1, to=999, width=4, font=("Consolas", 10),
            bg=BG_PANEL, fg=FG_TEXT, buttonbackground=BG_PANEL, relief="flat",
        )
        self.top_n_custom.delete(0, "end")
        self.top_n_custom.insert(0, "5")
        # hidden until "Custom" is picked

        ttk.Button(
            analyze_bar, text="🔍  Analyze  →  Save as Excel", style="Accent.TButton",
            command=self.run_analysis,
        ).pack(side="left", padx=(14, 0))

        self.status_label = tk.Label(
            self.main_frame, text="", fg=FG_MUTED, bg=BG_DARK, font=("Consolas", 9),
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 14), anchor="w")

    def _clear_placeholder(self, _event):
        if self.role_entry.get() == "e.g. Python Developer":
            self.role_entry.delete(0, tk.END)

    def _on_top_n_change(self, _event=None):
        if self.top_n_choice.get() == "Custom":
            self.top_n_custom.pack(side="left", padx=(0, 4), ipady=2)
        else:
            self.top_n_custom.pack_forget()

    def _resolve_top_n(self) -> int:
        choice = self.top_n_choice.get()
        if choice == "Top 5":
            return 5
        if choice == "Top 10":
            return 10
        try:
            return max(1, int(self.top_n_custom.get()))
        except (ValueError, tk.TclError):
            return 5

    def _back_to_intro(self):
        self.main_frame.pack_forget()
        self.intro_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def upload_resumes(self):
        paths = filedialog.askopenfilenames(
            title="Select Resume PDF(s)",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not paths:
            return

        added, failed = 0, []
        for path in paths:
            if not path.lower().endswith(".pdf"):
                failed.append((os.path.basename(path), "Not a PDF file"))
                continue
            try:
                candidate = parse_resume(path)
                self.candidates.append(candidate)
                added += 1
            except TalentScoutError as e:
                logger.warning(str(e))
                failed.append((os.path.basename(path), str(e)))
            except Exception as e:
                logger.exception(f"Unexpected error parsing {path}")
                failed.append((os.path.basename(path), "Unexpected error"))

        self._refresh_table()
        self.status_label.config(text=f"Added {added} candidate(s).")

        if failed:
            details = "\n".join(f"• {name}: {reason}" for name, reason in failed)
            messagebox.showwarning("Some files were skipped", details)

    def clear_all(self):
        if not self.candidates:
            return
        if messagebox.askyesno("Clear All", "Remove all loaded candidates?"):
            self.candidates.clear()
            self._refresh_table()
            self.status_label.config(text="Cleared.")

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, c in enumerate(self.candidates):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(c.name, c.email, c.phone, c.skills_display(), c.experience),
                tags=(tag,),
            )
        self.count_label.config(text=f"{len(self.candidates)} candidate(s) loaded")

    def run_analysis(self):
        role = self.role_entry.get().strip()
        if role == "e.g. Python Developer":
            role = ""
        try:
            ranked = analyze_candidates(self.candidates, role)
        except TalentScoutError as e:
            messagebox.showerror("Cannot Analyze", str(e))
            return

        top_n = min(self._resolve_top_n(), len(ranked))
        self._export_results(role, ranked, top_n)

    # ------------------------------------------------------------------ #
    # Excel export
    # ------------------------------------------------------------------ #
    def _export_results(self, role, ranked, top_n):
        safe_role = "".join(ch if ch.isalnum() else "_" for ch in role.strip().lower()) or "role"
        default_name = f"TalentScout_{safe_role}_Top{top_n}.xlsx"

        save_path = filedialog.asksaveasfilename(
            title="Save Analysis Results",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not save_path:
            return

        try:
            export_candidates_to_excel(
                output_path=save_path,
                role=role,
                ranked=ranked,
                top_n=top_n,
                total_candidates=len(self.candidates),
            )
        except Exception as e:
            logger.exception("Failed to write Excel report")
            messagebox.showerror("Export Failed", f"Could not save the Excel file:\n{e}")
            return

        top_candidates = ranked[:top_n]
        best_score = top_candidates[0].match_score if top_candidates else 0
        top_names = [c.name for c in top_candidates if c.match_score == best_score and best_score > 0]

        summary = f"Saved top {top_n} candidate(s) for '{role.title()}' to:\n{save_path}"
        if top_names:
            summary += f"\n\n🏆 Top match: {', '.join(top_names)} ({best_score}% skill fit)"
        else:
            summary += "\n\nNo strong match found for this role among loaded candidates."

        self.status_label.config(text=f"Exported top {top_n} results to {os.path.basename(save_path)}")
        messagebox.showinfo("Analysis Complete", summary)


def launch_app():
    root = tk.Tk()
    app = TalentScoutApp(root)
    root.mainloop()