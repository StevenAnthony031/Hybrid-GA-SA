import random
import copy
import math
from data.instance import CourseSession, DAYS, ROOMS
from utils.constraintEngine import ConstraintEngine, allowed_slots
from typing import List, Dict, Optional, Callable

class SA:
    def __init__(
        self,
        sessions: List[CourseSession],
        initial_temperature: float = 1000.0,
        cooling_rate: float = 0.995,
        min_temperature: float = 0.1,
        iterations_per_temp: int = 50,
        neighbor_type: str = "targeted",        
        on_iteration: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        fitness_func: Optional[Callable] = None,
        random_seed: Optional[int] = None,
    ):
        self.sessions_template = sessions
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.iterations_per_temp = iterations_per_temp
        self.neighbor_type = neighbor_type
        self.on_iteration = on_iteration
        self.on_stop = on_stop
        self._fitness_func = fitness_func
        self.constraint_engine = ConstraintEngine()

        self.best_solution: Optional[List[CourseSession]] = None
        self.best_fitness: float = 0.0
        self.current_solution: Optional[List[CourseSession]] = None
        self.current_fitness: float = 0.0

        self.fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []   # SA tidak ada avg, diisi sama sbg kompatibilitas
        self.temperature_history: List[float] = []
        self.iteration = 0
        self.generation = 0   # alias iteration untuk kompatibilitas dengan GA/Hybrid

        if random_seed is not None:
            random.seed(random_seed)

    # ─────────────────────────── FITNESS ────────────────────────────

    def _default_fitness(self, chromosome: List[CourseSession]) -> float:
        penalty = self.constraint_engine.evaluate(chromosome)
        return 1.0 / (penalty + 1.0)

    def fitness(self, chromosome: List[CourseSession], idx: int = 0) -> float:
        if self._fitness_func:
            return self._fitness_func(chromosome, idx)
        return self._default_fitness(chromosome)

    # ─────────────────────────── INIT ───────────────────────────────

    def _random_solution(self) -> List[CourseSession]:
        chrom = []
        for tmpl in self.sessions_template:
            s = copy.copy(tmpl)
            s.day = random.choice(DAYS)
            slots = allowed_slots(s, s.day)
            s.slot_index = random.choice(slots)
            s.room = random.choice(ROOMS)
            chrom.append(s)
        return chrom

    # ─────────────────────────── NEIGHBOR ───────────────────────────

    def _get_neighbor(self, solution: List[CourseSession]) -> List[CourseSession]:
        """
        Hasilkan solusi tetangga dengan memutasi 1 gen.
        - "random"   : pilih gen secara acak
        - "targeted" : prioritaskan gen yang punya pelanggaran constraint
        """
        neighbor = [copy.copy(g) for g in solution]

        if self.neighbor_type == "targeted":
            gene_idx = self._pick_violated_gene(neighbor)
        else:
            gene_idx = random.randrange(len(neighbor))

        self._mutate_gene(neighbor[gene_idx])
        return neighbor

    def _pick_violated_gene(self, solution: List[CourseSession]) -> int:
        """
        Kembalikan index gen yang memiliki pelanggaran.
        Jika tidak ada, kembalikan index acak.
        """
        violated = []
        for i, gene in enumerate(solution):
            violations = self.constraint_engine.violations_for_session(gene, solution)
            if violations:
                violated.append(i)
        if violated:
            return random.choice(violated)
        return random.randrange(len(solution))

    def _mutate_gene(self, gene: CourseSession):
        """Sama persis dengan GA._mutate_gene untuk konsistensi."""
        choice = random.randint(0, 2)
        if choice == 0:
            gene.day = random.choice(DAYS)
            slots = allowed_slots(gene, gene.day)
            gene.slot_index = random.choice(slots)
        elif choice == 1:
            if gene.day:
                slots = allowed_slots(gene, gene.day)
                gene.slot_index = random.choice(slots)
        else:
            gene.room = random.choice(ROOMS)

    # ─────────────────────────── ACCEPTANCE ─────────────────────────

    @staticmethod
    def _accept(current_fit: float, neighbor_fit: float, temperature: float) -> bool:
        """
        Terima solusi lebih baik selalu.
        Terima solusi lebih buruk dengan probabilitas e^(Δ/T).
        """
        if neighbor_fit >= current_fit:
            return True
        delta = neighbor_fit - current_fit          # delta < 0
        prob = math.exp(delta / temperature)
        return random.random() < prob

    # ─────────────────────────── RUN ────────────────────────────────

    def run(self, initial_solution: Optional[List[CourseSession]] = None):
        """
        Jalankan SA.
        Jika `initial_solution` diberikan (mis. dari GA Hybrid),
        SA akan memulai dari sana alih-alih solusi acak.
        """
        # Inisialisasi solusi awal
        if initial_solution is not None:
            self.current_solution = [copy.copy(g) for g in initial_solution]
        else:
            self.current_solution = self._random_solution()

        self.current_fitness = self.fitness(self.current_solution)
        self.best_solution = copy.deepcopy(self.current_solution)
        self.best_fitness = self.current_fitness

        temperature = self.initial_temperature
        self.iteration = 0

        while temperature > self.min_temperature:
            self.iteration += 1
            self.generation = self.iteration   # alias untuk kompatibilitas

            iter_fitnesses = []

            for _ in range(self.iterations_per_temp):
                neighbor = self._get_neighbor(self.current_solution)
                neighbor_fit = self.fitness(neighbor)
                iter_fitnesses.append(neighbor_fit)

                if self._accept(self.current_fitness, neighbor_fit, temperature):
                    self.current_solution = neighbor
                    self.current_fitness = neighbor_fit

                    if self.current_fitness > self.best_fitness:
                        self.best_fitness = self.current_fitness
                        self.best_solution = copy.deepcopy(self.current_solution)

            # Rekam histori per tahap pendinginan
            self.fitness_history.append(self.best_fitness)
            self.avg_fitness_history.append(
                sum(iter_fitnesses) / len(iter_fitnesses)
            )
            self.temperature_history.append(temperature)

            if self.on_iteration:
                self.on_iteration(self)

            if self.best_fitness == 1.0:
                print(f"  [Iter {self.iteration}] Solusi sempurna ditemukan! Fitness = 1")
                break

            temperature *= self.cooling_rate

        if self.on_stop:
            self.on_stop(self, self.best_solution, self.best_fitness)

        return self.best_solution, self.best_fitness

    # ─────────────────────────── UTILS ──────────────────────────────

    def best_solution_fitness(self) -> float:
        return self.best_fitness

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "SA SCHEDULER — SUMMARY",
            "=" * 60,
            f"  Iterations run   : {self.iteration}",
            f"  Init temperature : {self.initial_temperature}",
            f"  Cooling rate     : {self.cooling_rate}",
            f"  Min temperature  : {self.min_temperature}",
            f"  Iter per temp    : {self.iterations_per_temp}",
            f"  Neighbor type    : {self.neighbor_type}",
            f"  Best fitness     : {self.best_fitness:.5f}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def get_schedule_as_dict(self) -> List[Dict]:
        """Format output identik dengan GA.get_schedule_as_dict()."""
        if not self.best_solution:
            return []
        from data.instance import DAYS
        result = []
        for s in self.best_solution:
            result.append({
                "lecturer": s.lecturer,
                "course_code": s.course_code,
                "course_name": s.course_name,
                "classes": s.classes,
                "semester": s.semester,
                "tipe": s.tipe,
                "credit_per_classes": s.credit_per_classes,
                "day": s.day,
                "room": s.room,
                "start_time": s.start_str(),
                "end_time": s.end_str(),
            })
        day_order = {d: i for i, d in enumerate(DAYS)}
        result.sort(
            key=lambda x: (day_order.get(x["day"], 99), x["start_time"] or "", x["room"] or "")
        )
        return result

    def constraint_breakdown(self) -> Dict[str, int]:
        """Format output identik dengan GA.constraint_breakdown()."""
        if not self.best_solution:
            return {}
        chrom = self.best_solution
        ce = self.constraint_engine
        return {
            "Slot out of bounds": int(ce._slot_bounds(chrom) / ce.PENALTY_SLOT_OUT_OF_BOUNDS),
            "Lecturer/Room/Class conflicts": int(ce._time_conflicts(chrom) / 100),
            "MKWU not on Monday": int(ce._mkwu_monday(chrom) / ce.PENALTY_MKWU_NOT_MONDAY),
            "Tuesday classes": int(ce._no_tuesday(chrom) / ce.PENALTY_TUESDAY_CLASS),
            "Sem 2&4 on Mon/Tue": int(ce._sem24_restrictions(chrom) / ce.PENALTY_SEM24_MONDAY),
            "Friday break violation": int(ce._friday_break(chrom) / ce.PENALTY_FRIDAY_BREAK),
        }