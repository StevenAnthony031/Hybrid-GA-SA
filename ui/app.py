import tkinter as tk
import time
from algorithm.genetic_algorithm import GA
from algorithm.simulated_annealing import SA
from algorithm.hybrid import Hybrid
from data.instance import parse_raw_data, CourseSession
from data.data import RAW_DATA
from tkinter import ttk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Penjadwalan Matakuliah")
        self.root.geometry("1000x750")

        self.courses = []
        self.rooms = []
        self.sessions = []

        self.build_landing_page()

    def start_app(self):
        self.landing_frame.destroy()

        # load UI utama
        self.build_form()
        self.build_course_list()
        self.build_buttons()
        self.build_status()
        self.build_schedule_table()

    #================== Landing page ===============
    def build_landing_page(self):
        self.landing_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.landing_frame.pack(fill="both", expand=True)

        try:
            self.logo = tk.PhotoImage(file="ui/logo_usu.png")  
            self.logo = self.logo.subsample(2, 2)
            logo_label = tk.Label(self.landing_frame, image=self.logo, bg="#f5f5f5")
            logo_label.pack(pady=20)
        except:
            tk.Label(self.landing_frame, text="[LOGO]", font=("Arial", 20), bg="#f5f5f5").pack(pady=30)

        # Judul
        tk.Label(
            self.landing_frame,
            text="Implementasi Genetic Algorithm - Simulated Annealing\nuntuk Optimasi Jadwal Kuliah",
            font=("Arial", 20, "bold"),
            bg="#f5f5f5",
            justify="center"
        ).pack(pady=10)

        # Nama
        tk.Label(
            self.landing_frame,
            text="Skripsi oleh Steven Anthony (221401031)",
            font=("Arial", 14),
            bg="#f5f5f5"
        ).pack(pady=10)

        # Tombol mulai
        tk.Button(
            self.landing_frame,
            text="Mulai",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="white",
            width=20,
            height=2,
            command=self.start_app
        ).pack(pady=40)

    # ================= FORM INPUT =================
    def build_form(self):
        frame = ttk.LabelFrame(self.root, text="Input Matakuliah")
        frame.place(x=20, y=20, width=350, height=340)

        labels = [
            "Kode MK", "Nama MK", "Semester",
            "Tipe (MKWU/NON)", "SKS Total",
            "Kom:Dosen (per baris)"
        ]

        self.entries = {}

        for i, label in enumerate(labels[:-1]):
            ttk.Label(frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(frame)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label] = entry

        # Text area khusus kom:dosen
        ttk.Label(frame, text=labels[-1]).grid(row=5, column=0, padx=5, pady=5, sticky="nw")
        self.kom_dosen_text = tk.Text(frame, height=5, width=20)
        self.kom_dosen_text.grid(row=5, column=1, padx=5, pady=5)

    # ================= LIST MK =================
    def build_course_list(self):
        frame = ttk.LabelFrame(self.root, text="Daftar Matakuliah Saat Ini")
        frame.place(x=400, y=20, width=560, height=260)

        self.course_listbox = tk.Listbox(frame, height=12)
        self.course_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ================= BUTTONS =================
    def build_buttons(self):
        frame = ttk.Frame(self.root)
        frame.place(x=20, y=300, width=940, height=50)

        ttk.Button(frame, text="Tambah MK", command=self.add_course).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Hapus MK", command=self.delete_course).pack(side=tk.LEFT, padx=5)

        ttk.Separator(frame, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(frame, text="Run GA", command=self.run_ga).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Run SA", command=self.run_sa).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Run Hybrid", command=self.run_hybrid).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Load Data Uji", command=self.load_sample_data).pack(side=tk.LEFT, padx=5)

    # ================= STATUS =================
    def build_status(self):
        self.status_label = ttk.Label(self.root, text="Siap.", foreground="blue")
        self.status_label.place(x=20, y=360)

        self.penalty_label = ttk.Label(self.root, text="", justify="left")
        self.penalty_label.place(x=20, y=380)

    def set_status(self, msg, success=True):
        self.status_label.config(text=msg, foreground="green" if success else "red")

    # ================= TABLE =================
    def build_schedule_table(self):
        frame = ttk.LabelFrame(self.root, text="Jadwal Hasil")
        frame.place(x=20, y=500, width=940, height=220)

        columns = (
            "Hari", "Jam", "Kode", "Nama MK",
            "Kom", "Dosen", "Ruang", "Semester", "SKS"
        )

        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Hari":
                self.tree.column(col, width=80, anchor="center")
            elif col == "Jam":
                self.tree.column(col, width=100, anchor="center")
            elif col == "Kode":
                self.tree.column(col, width=90, anchor="center")
            elif col == "Nama MK":
                self.tree.column(col, width=200, anchor="w")
            elif col == "Kom":
                self.tree.column(col, width=50, anchor="center")
            elif col == "Dosen":
                self.tree.column(col, width=200, anchor="w")
            elif col == "Ruang":
                self.tree.column(col, width=80, anchor="center")
            elif col == "Semester":
                self.tree.column(col, width=70, anchor="center")
            else:
                self.tree.column(col, width=50, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

    def update_schedule_table(self, schedule):
        self.tree.delete(*self.tree.get_children())

        for e in schedule:

            self.tree.insert("", tk.END, values=(
                e['day'],
                f"{e['start_time']} - {e['end_time']}",
                e['course_code'],
                e['course_name'],
                e['classes'],
                e['lecturer'],
                e['room'],
                e['semester'],
                e['credit_per_classes']
            ))

    # ================= ACTIONS =================
    def add_course(self):
        try:
            kode = self.entries["Kode MK"].get()
            nama = self.entries["Nama MK"].get()
            semester = int(self.entries["Semester"].get())
            tipe = self.entries["Tipe (MKWU/NON)"].get()
            sks_total = int(self.entries["SKS Total"].get())

            kom_lines = self.kom_dosen_text.get("1.0", tk.END).strip().splitlines()

            if not kom_lines:
                raise Exception("Kom kosong")

            sks_per_kom = sks_total // len(kom_lines)

            for line in kom_lines:
                if ":" not in line:
                    raise Exception("Format harus Kom:Dosen")

                kom, dosen = line.split(":")
                session = CourseSession(
                    lecturer=dosen.strip(),
                    course_code=kode,
                    course_name=nama,
                    credit_per_classes=sks_per_kom,
                    classes=kom.strip().upper(),
                    semester=semester,
                    tipe=tipe
                )

                self.sessions.append(session)

                self.course_listbox.insert(
                    tk.END,
                    f"{session.course_code} | {session.course_name} | "
                    f"Kom {session.classes} | {session.lecturer} | {session.credit_per_classes} SKS"
                )

            self.set_status("Matakuliah berhasil ditambahkan.")
            self.clear_form()
            self.kom_dosen_text.delete("1.0", tk.END)

        except Exception as e:
            self.set_status(f"Error: {str(e)}", False)
            
    def delete_course(self):
        sel = self.course_listbox.curselection()
        if not sel:
            self.set_status("Pilih matakuliah terlebih dahulu.", False)
            return

        idx = sel[0]

        self.course_listbox.delete(idx)
        self.sessions.pop(idx)

        self.set_status("Matakuliah dihapus.")

    # ================= RUN =================
    def run_ga(self):
        self.set_status("GA sedang berjalan...")

        ga = GA(
            sessions=self.sessions,
            num_generations=500,
            num_parents_mating=20,
            sol_per_pop=120,
            mutation_probability=0.08,
            crossover_type="uniform",
            parent_selection_type="tournament",
            keep_parents=4,
            # random_seed=42,
        )

        t0 = time.time()
        solution, fitness = ga.run()
        elapsed = time.time() - t0
        schedule = ga.get_schedule_as_dict()
        penalty_detail = ga.constraint_breakdown()
        
        self.update_schedule_table(schedule)
        self.show_penalty_detail(penalty_detail)

        self.set_status(
            f"GA selesai | Fitness: {ga.best_solution_fitness():.4f} | Waktu: {elapsed:.2f} s"
        )

        return schedule, penalty_detail

    def run_sa(self):
        self.set_status("SA sedang berjalan...")
 
        sa = SA(
            sessions=self.sessions,
            initial_temperature=100.0,
            cooling_rate=0.995,
            min_temperature=0.001,
            iterations_per_temp=50,
            neighbor_type="random", #targeted
        )
 
        t0 = time.time()
        solution, fitness = sa.run()
        elapsed = time.time() - t0
 
        schedule = sa.get_schedule_as_dict()
        penalty_detail = sa.constraint_breakdown()
 
        self.update_schedule_table(schedule)
        self.show_penalty_detail(penalty_detail)
        self.set_status(
            f"SA selesai | Fitness: {sa.best_solution_fitness():.4f} | Waktu: {elapsed:.2f} s"
        )
 
        return schedule, penalty_detail

    def run_hybrid(self):
        if not self.sessions:
            self.set_status("Data matakuliah kosong.", False)
            return
 
        self.set_status("Hybrid (GA+SA) sedang berjalan...")
 
        hybrid = Hybrid(
            sessions=self.sessions,
            # Parameter GA
            ga_generations=300,
            ga_num_parents_mating=20,
            ga_sol_per_pop=120,
            ga_mutation_probability=0.08,
            ga_crossover_type="uniform",
            ga_parent_selection_type="tournament",
            ga_keep_parents=4,
            # Parameter SA
            sa_initial_temperature=500.0,
            sa_cooling_rate=0.995,
            sa_min_temperature=0.1,
            sa_iterations_per_temp=50,
            sa_neighbor_type="targeted",
        )
 
        t0 = time.time()
        solution, fitness = hybrid.run()
        elapsed = time.time() - t0
 
        schedule = hybrid.get_schedule_as_dict()
        penalty_detail = hybrid.constraint_breakdown()
 
        self.update_schedule_table(schedule)
        self.show_penalty_detail(penalty_detail)
        self.set_status(
            f"Hybrid selesai | Fitness: {hybrid.best_solution_fitness():.4f} | Waktu: {elapsed:.2f} s"
        )
 
        return schedule, penalty_detail

    def clear_form(self):
        for e in self.entries.values():
            e.delete(0, tk.END)

    def load_sample_data(self):
        self.course_listbox.delete(0, tk.END)

        self.sessions = parse_raw_data(RAW_DATA)

        count = 0

        for s in self.sessions:
            self.course_listbox.insert(
                tk.END,
                f"{s.course_code} | {s.course_name} | "
                f"Kom {s.classes} | {s.lecturer} | {s.credit_per_classes} SKS"
            )
            count += 1

        self.set_status(f"Data RAW berhasil dimuat ({count} kelas).")

    def show_penalty_detail(self, schedule):

        text = (
            f"Dosen bentrok: {schedule['Lecturer/Room/Class conflicts']} \n"
            f"MKWU salah hari: {schedule['MKWU not on Monday']} \n"
            f"Kelas di hari Selasa: {schedule['Tuesday classes']} \n"
            f"Semester 2 dan 4 di Senin/Selasa: {schedule['Sem 2&4 on Mon/Tue']} \n"
            f"Isoma Jumat: {schedule['Friday break violation']}"
        )

        self.penalty_label.config(text=text)