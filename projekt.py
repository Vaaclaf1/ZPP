import sqlite3
import csv
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DataModel:
    def __init__(self, db_name="analytika.db"):
        self.__db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.__db_name) as conn:
            conn.cursor().execute('''
                CREATE TABLE IF NOT EXISTS dataset (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kategorie TEXT,
                    hodnota_x REAL,
                    hodnota_y REAL
                )
            ''')
            conn.commit()

    def nacti_data(self):
        with sqlite3.connect(self.__db_name) as conn:
            return conn.cursor().execute("SELECT * FROM dataset").fetchall()

    def pridej_zaznam(self, kat, x, y):
        with sqlite3.connect(self.__db_name) as conn:
            conn.cursor().execute("INSERT INTO dataset (kategorie, hodnota_x, hodnota_y) VALUES (?, ?, ?)", (kat, float(x), float(y)))
            conn.commit()

    def uprav_zaznam(self, id_zaznamu, kat, x, y):
        with sqlite3.connect(self.__db_name) as conn:
            conn.cursor().execute("UPDATE dataset SET kategorie=?, hodnota_x=?, hodnota_y=? WHERE id=?", (kat, float(x), float(y), int(id_zaznamu)))
            conn.commit()

    def smaz_zaznam(self, id_zaznamu):
        with sqlite3.connect(self.__db_name) as conn:
            conn.cursor().execute("DELETE FROM dataset WHERE id=?", (int(id_zaznamu),))
            conn.commit()

    def vycisti_databazi(self):
        with sqlite3.connect(self.__db_name) as conn:
            conn.cursor().execute("DELETE FROM dataset")
            conn.commit()

class DataAnalyzer:
    def __init__(self, data):
        self.__data = data

    def get_statistiky(self):
        if not self.__data:
            return {"pocet": 0, "sum_x": 0, "sum_y": 0, "avg_x": 0, "avg_y": 0, "max_x": 0, "max_y": 0}
        x_vals = [r[2] for r in self.__data]
        y_vals = [r[3] for r in self.__data]
        n = len(self.__data)
        return {
            "pocet": n,
            "sum_x": sum(x_vals), "sum_y": sum(y_vals),
            "avg_x": sum(x_vals)/n, "avg_y": sum(y_vals)/n,
            "max_x": max(x_vals), "max_y": max(y_vals)
        }

    def bubble_sort_dle_sloupce(self, index_sloupce):
        serazeno = list(self.__data)
        n = len(serazeno)
        for i in range(n):
            for j in range(0, n - i - 1):
                if serazeno[j][index_sloupce] > serazeno[j + 1][index_sloupce]:
                    serazeno[j], serazeno[j + 1] = serazeno[j + 1], serazeno[j]
        return serazeno

class DataDashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data analyzer")
        self.root.geometry("1100x750")
        
        self.db = DataModel()
        self.vybrane_id = None
        self.colorbar = None
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="  Správce Dat ")

        self.tab_dash = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dash, text="  Dashboard & Vizualizace ")

        self.sestav_tab_data()
        self.sestav_tab_dash()
        self.obnov_tabulku()

    def sestav_tab_data(self):
        toolbar = tk.Frame(self.tab_data, bg="#34495e", pady=10, padx=10)
        toolbar.pack(fill="x")
        
        
        btn_import = ttk.Menubutton(toolbar, text="📥 Import Dat")
        menu_import = tk.Menu(btn_import, tearoff=0)
        menu_import.add_command(label="Z CSV souboru", command=self.import_csv)
        menu_import.add_command(label="Z JSON souboru", command=self.import_json)
        btn_import["menu"] = menu_import
        btn_import.pack(side="left", padx=5)

        btn_export = ttk.Menubutton(toolbar, text="📤 Export Dat")
        menu_export = tk.Menu(btn_export, tearoff=0)
        menu_export.add_command(label="Do CSV souboru", command=self.export_csv)
        menu_export.add_command(label="Do JSON souboru", command=self.export_json)
        btn_export["menu"] = menu_export
        btn_export.pack(side="left", padx=5)

        tk.Button(toolbar, text=" Vymazat vše", command=self.vymaz_vse, bg="#e74c3c", fg="white").pack(side="right", padx=5)

        main_content = tk.Frame(self.tab_data)
        main_content.pack(fill="both", expand=True, padx=10, pady=10)

        form_frame = tk.LabelFrame(main_content, text="Editor záznamu", padx=10, pady=10)
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(form_frame, text="Kategorie (Label):").pack(anchor="w")
        self.ent_kat = ttk.Entry(form_frame)
        self.ent_kat.pack(fill="x", pady=(0, 10))

        tk.Label(form_frame, text="Hodnota X:").pack(anchor="w")
        self.ent_x = ttk.Entry(form_frame)
        self.ent_x.pack(fill="x", pady=(0, 10))

        tk.Label(form_frame, text="Hodnota Y:").pack(anchor="w")
        self.ent_y = ttk.Entry(form_frame)
        self.ent_y.pack(fill="x", pady=(0, 15))

        tk.Button(form_frame, text=" Přidat", bg="#2ecc71", fg="white", command=self.pridej).pack(fill="x", pady=2)
        tk.Button(form_frame, text=" Upravit", bg="#3498db", fg="white", command=self.uprav).pack(fill="x", pady=2)
        tk.Button(form_frame, text=" Smazat", bg="#e74c3c", fg="white", command=self.smaz).pack(fill="x", pady=2)
        
        tk.Label(form_frame, text="Algoritmus řazení:", pady=10).pack()
        tk.Button(form_frame, text="Seřadit podle X", command=lambda: self.aplikuj_razeni(2)).pack(fill="x", pady=2)
        tk.Button(form_frame, text="Seřadit podle Y", command=lambda: self.aplikuj_razeni(3)).pack(fill="x", pady=2)

        cols = ('ID', 'Kategorie', 'Hodnota X', 'Hodnota Y')
        self.tree = ttk.Treeview(main_content, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column('ID', width=50, anchor="center")
        self.tree.pack(side="right", fill="both", expand=True)
        self.tree.bind('<ButtonRelease-1>', self.vyber_zaznam)

    def sestav_tab_dash(self):
        stats_frame = tk.Frame(self.tab_dash, width=250, bg="#2c3e50")
        stats_frame.pack(side="left", fill="y")
        
        tk.Label(stats_frame, text="DASHBOARD", fg="white", bg="#2c3e50", font=("Arial", 16, "bold")).pack(pady=20)
        
        self.lbl_stats = tk.Label(stats_frame, text="", fg="white", bg="#2c3e50", font=("Arial", 11), justify="left")
        self.lbl_stats.pack(padx=20, anchor="w")
        
        tk.Button(stats_frame, text="Aktualizovat Dashboard", command=self.obnov_dashboard, bg="#f1c40f").pack(pady=30, padx=20, fill="x")

        graph_ctrl_frame = tk.Frame(self.tab_dash, pady=10)
        graph_ctrl_frame.pack(side="top", fill="x", padx=10)

        tk.Label(graph_ctrl_frame, text="Vyber typ vizualizace:").pack(side="left")
        
        seznam_grafu = [
            "Bar chart (Suma Y dle Kat.)",
            "Horizontální Bar chart",
            "Scatter plot (X vs Y)",
            "Line chart (Trend)",
            "Area chart (Plošný graf X vs Y)",
            "Pie chart (Podíl Y)",

        ]
        self.combo_graf = ttk.Combobox(graph_ctrl_frame, values=seznam_grafu, state="readonly", width=40)
        self.combo_graf.set(seznam_grafu[0])
        self.combo_graf.pack(side="left", padx=10)
        
        tk.Button(graph_ctrl_frame, text="Vykreslit graf", bg="#3498db", fg="white", command=self.vykresli_graf).pack(side="left")

        self.canvas_frame = tk.Frame(self.tab_dash, bg="white", relief="sunken", bd=1)
        self.canvas_frame.pack(side="bottom", fill="both", expand=True, padx=10, pady=10)
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def obnov_tabulku(self, data=None):
        for r in self.tree.get_children(): self.tree.delete(r)
        dataset = data if data else self.db.nacti_data()
        for row in dataset: self.tree.insert('', tk.END, values=row)

    def aplikuj_razeni(self, index_sloupce):
        data = self.db.nacti_data()
        serazena_data = DataAnalyzer(data).bubble_sort_dle_sloupce(index_sloupce)
        self.obnov_tabulku(serazena_data)

    def vycisti_formular(self):
        self.vybrane_id = None
        self.ent_kat.delete(0, tk.END)
        self.ent_x.delete(0, tk.END)
        self.ent_y.delete(0, tk.END)

    def vyber_zaznam(self, event):
        vybrany = self.tree.focus()
        hodnoty = self.tree.item(vybrany, 'values')
        if hodnoty:
            self.vycisti_formular()
            self.vybrane_id = hodnoty[0]
            self.ent_kat.insert(0, hodnoty[1])
            self.ent_x.insert(0, hodnoty[2])
            self.ent_y.insert(0, hodnoty[3])

    def ziskej_vstupy(self):
        try:
            k = self.ent_kat.get()
            x = float(self.ent_x.get())
            y = float(self.ent_y.get())
            if not k: raise ValueError
            return k, x, y
        except ValueError:
            messagebox.showwarning("Chyba", "Kategorie nesmí být prázdná a X/Y musí být čísla!")
            return None

    def pridej(self):
        v = self.ziskej_vstupy()
        if v:
            self.db.pridej_zaznam(*v)
            self.obnov_tabulku()
            self.vycisti_formular()

    def uprav(self):
        v = self.ziskej_vstupy()
        if v and self.vybrane_id:
            self.db.uprav_zaznam(self.vybrane_id, *v)
            self.obnov_tabulku()
            self.vycisti_formular()

    def smaz(self):
        if self.vybrane_id:
            self.db.smaz_zaznam(self.vybrane_id)
            self.obnov_tabulku()
            self.vycisti_formular()

    def vymaz_vse(self):
        if messagebox.askyesno("Varování", "Opravdu vymazat celou databázi?"):
            self.db.vycisti_databazi()
            self.obnov_tabulku()

    def import_csv(self):
        cesta = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not cesta: return
        try:
            with open(cesta, 'r', encoding='utf-8') as f:
                ctenar = csv.DictReader(f) 
                for r in ctenar:
                    self.db.pridej_zaznam(r['Kategorie'], r['HodnotaX'], r['HodnotaY'])
            self.obnov_tabulku()
            messagebox.showinfo("OK", "CSV nahráno úspěšně.")
        except Exception as e: 
            messagebox.showerror("Chyba", f"Chyba importu CSV: {e}\nUjistěte se, že CSV má hlavičku: Kategorie,HodnotaX,HodnotaY")

    def import_json(self):
        cesta = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not cesta: return
        try:
            with open(cesta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for r in data:
                    self.db.pridej_zaznam(
                        r.get('kategorie', 'Neznámá'), 
                        r.get('hodnota_x', 0), 
                        r.get('hodnota_y', 0)
                    )
            self.obnov_tabulku()
            messagebox.showinfo("OK", "JSON nahrán úspěšně.")
        except Exception as e: 
            messagebox.showerror("Chyba", f"Chyba importu JSON: {e}")
    def export_csv(self):
        cesta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not cesta: return
        try:
            with open(cesta, 'w', encoding='utf-8', newline='') as f:
                zapis = csv.writer(f)
                zapis.writerow(['ID', 'Kategorie', 'HodnotaX', 'HodnotaY'])
                zapis.writerows(self.db.nacti_data())
            messagebox.showinfo("OK", "Úspěšně exportováno do CSV.")
        except Exception as e: messagebox.showerror("Chyba", str(e))

    def export_json(self):
        cesta = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not cesta: return
        try:
            data = self.db.nacti_data()
            json_data = [{"id": r[0], "kategorie": r[1], "hodnota_x": r[2], "hodnota_y": r[3]} for r in data]
            with open(cesta, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("OK", "Úspěšně exportováno do JSON.")
        except Exception as e: messagebox.showerror("Chyba", str(e))

    def obnov_dashboard(self):
        data = self.db.nacti_data()
        stats = DataAnalyzer(data).get_statistiky()
        text = (
            f"Celkem záznamů: {stats['pocet']}\n\n"
            f"--- STATISTIKA X ---\n"
            f"Součet: {stats['sum_x']:,.2f}\n"
            f"Průměr: {stats['avg_x']:,.2f}\n"
            f"Maximum: {stats['max_x']:,.2f}\n\n"
            f"--- STATISTIKA Y ---\n"
            f"Součet: {stats['sum_y']:,.2f}\n"
            f"Průměr: {stats['avg_y']:,.2f}\n"
            f"Maximum: {stats['max_y']:,.2f}"
        )
        self.lbl_stats.config(text=text)
        self.vykresli_graf()

    def vykresli_graf(self):
        data = self.db.nacti_data()
        self.ax.clear()
        
        if hasattr(self, 'colorbar') and self.colorbar:
            self.colorbar.remove()
            self.colorbar = None
        
        if not data:
            self.ax.text(0.5, 0.5, "Žádná data k zobrazení", ha='center', va='center')
            self.canvas.draw()
            return

        typ = self.combo_graf.get()
        
        if typ == "Bar chart (Suma Y dle Kat.)":
            agregace = {}
            for r in data: agregace[r[1]] = agregace.get(r[1], 0) + r[3]
            self.ax.bar(list(agregace.keys()), list(agregace.values()), color='#3498db')
            self.ax.set_title("Bar chart - Suma hodnot Y")
            
        elif typ == "Horizontální Bar chart":
            agregace = {}
            for r in data: agregace[r[1]] = agregace.get(r[1], 0) + r[3]
            self.ax.barh(list(agregace.keys()), list(agregace.values()), color='#2ecc71')
            self.ax.set_title("Horizontální Bar chart")

        elif typ == "Scatter plot (X vs Y)":
            x = [r[2] for r in data]
            y = [r[3] for r in data]
            self.ax.scatter(x, y, color='#e74c3c', alpha=0.7)
            self.ax.set_xlabel("Hodnota X")
            self.ax.set_ylabel("Hodnota Y")
            self.ax.set_title("Scatter plot")
            
        elif typ == "Line chart (Trend)":
            data_serazena = sorted(data, key=lambda row: row[2])
            x = [r[2] for r in data_serazena]
            y = [r[3] for r in data_serazena]
            self.ax.plot(x, y, marker='o', linestyle='-', color='#9b59b6', linewidth=2)
            self.ax.set_xlabel("Hodnota X")
            self.ax.set_title("Line chart")

        elif typ == "Area chart (Plošný graf X vs Y)":
            data_serazena = sorted(data, key=lambda row: row[2])
            x = [r[2] for r in data_serazena]
            y = [r[3] for r in data_serazena]
            self.ax.fill_between(x, y, color="#87CEFA", alpha=0.5)
            self.ax.plot(x, y, color="#4682B4", linewidth=2)
            self.ax.set_xlabel("Hodnota X")
            self.ax.set_ylabel("Hodnota Y")
            self.ax.set_title("Area chart (Plošný graf)")

        elif typ == "Pie chart (Podíl Y)":
            agregace = {}
            for r in data: agregace[r[1]] = agregace.get(r[1], 0) + r[3]
            self.ax.pie(list(agregace.values()), labels=list(agregace.keys()), autopct='%1.1f%%', startangle=90)
            self.ax.set_title("Pie chart")
            
        self.canvas.draw()
    
if __name__ == "__main__":
    root = tk.Tk()
    app = DataDashboardApp(root)
    root.mainloop()