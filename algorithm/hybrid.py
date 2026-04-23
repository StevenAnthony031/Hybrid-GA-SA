import copy
from typing import List, Dict, Optional, Callable

from algorithm.genetic_algorithm import GA
from algorithm.simulated_annealing import SA
from data.instance import CourseSession


class Hybrid:
    """
    Hybrid Genetic Algorithm + Simulated Annealing.

    Alur kerja:
      1. GA berjalan penuh selama `ga_generations` generasi.
      2. Solusi terbaik GA diserahkan ke SA sebagai initial_solution.
      3. SA memperhalus solusi tersebut (local search / intensifikasi).
      4. Hasil akhir adalah solusi terbaik SA.

    Semua parameter GA dan SA dapat dikonfigurasi secara terpisah.
    """

    def __init__(
        self,
        sessions: List[CourseSession],

        # ── Parameter GA ──────────────────────────────────────────────
        ga_generations: int = 300,
        ga_num_parents_mating: int = 10,
        ga_sol_per_pop: int = 30,
        ga_mutation_probability: float = 0.05,
        ga_crossover_type: str = "uniform",
        ga_parent_selection_type: str = "tournament",
        ga_keep_parents: int = 2,

        # ── Parameter SA ──────────────────────────────────────────────
        sa_initial_temperature: float = 500.0,
        sa_cooling_rate: float = 0.995,
        sa_min_temperature: float = 0.1,
        sa_iterations_per_temp: int = 50,
        sa_neighbor_type: str = "targeted",   # targeted lebih efektif saat refinement

        # ── Shared ────────────────────────────────────────────────────
        on_ga_generation: Optional[Callable] = None,
        on_sa_iteration: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        fitness_func: Optional[Callable] = None,
        random_seed: Optional[int] = None,
    ):
        self.sessions = sessions
        self.on_stop = on_stop

        # Buat instance GA
        self.ga = GA(
            sessions=sessions,
            num_generations=ga_generations,
            num_parents_mating=ga_num_parents_mating,
            sol_per_pop=ga_sol_per_pop,
            mutation_probability=ga_mutation_probability,
            crossover_type=ga_crossover_type,
            parent_selection_type=ga_parent_selection_type,
            keep_parents=ga_keep_parents,
            on_generation=on_ga_generation,
            fitness_func=fitness_func,
            random_seed=random_seed,
        )

        # Buat instance SA (initial_solution akan diset saat run())
        self.sa = SA(
            sessions=sessions,
            initial_temperature=sa_initial_temperature,
            cooling_rate=sa_cooling_rate,
            min_temperature=sa_min_temperature,
            iterations_per_temp=sa_iterations_per_temp,
            neighbor_type=sa_neighbor_type,
            on_iteration=on_sa_iteration,
            fitness_func=fitness_func,
            random_seed=random_seed,
        )

        # Hasil akhir
        self.best_solution: Optional[List[CourseSession]] = None
        self.best_fitness: float = 0.0

        # Histori gabungan (GA dulu, lanjut SA)
        self.fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        self.ga_generations_run: int = 0
        self.sa_iterations_run: int = 0

    # ─────────────────────────── RUN ────────────────────────────────

    def run(self):
        # ── Fase 1 : GA ──────────────────────────────────────────────
        print("[Hybrid] Fase 1: Menjalankan Genetic Algorithm...")
        ga_solution, ga_fitness = self.ga.run()
        self.ga_generations_run = self.ga.generation

        print(
            f"[Hybrid] GA selesai | Gen: {self.ga_generations_run} "
            f"| Fitness: {ga_fitness:.5f}"
        )

        # Simpan histori GA
        self.fitness_history.extend(self.ga.fitness_history)
        self.avg_fitness_history.extend(self.ga.avg_fitness_history)

        # ── Fase 2 : SA (refinement) ─────────────────────────────────
        print("[Hybrid] Fase 2: Menyempurnakan dengan Simulated Annealing...")
        sa_solution, sa_fitness = self.sa.run(initial_solution=ga_solution)
        self.sa_iterations_run = self.sa.iteration

        print(
            f"[Hybrid] SA selesai | Iter: {self.sa_iterations_run} "
            f"| Fitness: {sa_fitness:.5f}"
        )

        # Lanjutkan histori dengan SA
        self.fitness_history.extend(self.sa.fitness_history)
        self.avg_fitness_history.extend(self.sa.avg_fitness_history)

        # ── Pilih solusi terbaik ──────────────────────────────────────
        # SA selalu lebih baik atau sama (karena dimulai dari hasil GA),
        # tapi kita tetap bandingkan untuk keamanan.
        if sa_fitness >= ga_fitness:
            self.best_solution = sa_solution
            self.best_fitness = sa_fitness
        else:
            self.best_solution = copy.deepcopy(ga_solution)
            self.best_fitness = ga_fitness

        print(
            f"[Hybrid] Selesai | Fitness akhir: {self.best_fitness:.5f} "
            f"(GA: {ga_fitness:.5f} → SA: {sa_fitness:.5f})"
        )

        if self.on_stop:
            self.on_stop(self, self.best_solution, self.best_fitness)

        return self.best_solution, self.best_fitness

    # ─────────────────────────── UTILS ──────────────────────────────

    def best_solution_fitness(self) -> float:
        return self.best_fitness

    def summary(self) -> str:
        ga = self.ga
        sa = self.sa
        lines = [
            "=" * 60,
            "HYBRID (GA + SA) SCHEDULER — SUMMARY",
            "=" * 60,
            "  ── Genetic Algorithm ──",
            f"  Generations run  : {self.ga_generations_run}",
            f"  Population size  : {ga.sol_per_pop}",
            f"  Crossover type   : {ga.crossover_type}",
            f"  Parent selection : {ga.parent_selection_type}",
            f"  Mutation prob    : {ga.mutation_probability}",
            f"  GA best fitness  : {ga.best_fitness:.5f}",
            "  ── Simulated Annealing ──",
            f"  Iterations run   : {self.sa_iterations_run}",
            f"  Init temperature : {sa.initial_temperature}",
            f"  Cooling rate     : {sa.cooling_rate}",
            f"  Neighbor type    : {sa.neighbor_type}",
            f"  SA best fitness  : {sa.best_fitness:.5f}",
            "  ── Final ──",
            f"  Best fitness     : {self.best_fitness:.5f}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def get_schedule_as_dict(self) -> List[Dict]:
        """Delegasi ke SA (pemilik solusi akhir)."""
        # Pastikan SA punya solusi; jika tidak fallback ke GA
        if self.sa.best_solution:
            return self.sa.get_schedule_as_dict()
        return self.ga.get_schedule_as_dict()

    def constraint_breakdown(self) -> Dict[str, int]:
        """Delegasi ke SA (pemilik solusi akhir)."""
        if self.sa.best_solution:
            return self.sa.constraint_breakdown()
        return self.ga.constraint_breakdown()