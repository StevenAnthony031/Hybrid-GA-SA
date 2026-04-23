import random
import copy
from data.instance import CourseSession, DAYS, ROOMS
from utils.constraintEngine import ConstraintEngine, allowed_slots
from typing import List, Dict, Optional, Callable

class GA:
    def __init__(
        self,
        sessions: List[CourseSession],
        num_generations: int = 300,
        num_parents_mating: int = 10,
        sol_per_pop: int = 30,
        mutation_probability: float = 0.05,
        crossover_type: str = "single_point",
        parent_selection_type: str = "tournament",
        keep_parents: int = 2,
        on_generation: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        fitness_func: Optional[Callable] = None,
        random_seed: Optional[int] = None,
    ):
        self.sessions_template = sessions
        self.num_generations = num_generations
        self.num_parents_mating = num_parents_mating
        self.sol_per_pop = sol_per_pop
        self.mutation_probability = mutation_probability
        self.crossover_type = crossover_type
        self.parent_selection_type = parent_selection_type
        self.keep_parents = keep_parents
        self.on_generation = on_generation
        self.on_stop = on_stop
        self.constraint_engine = ConstraintEngine()
        self._fitness_func = fitness_func
        self.best_solution = None
        self.best_fitness = 0.0
        self.fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        self.population: List[List[CourseSession]] = []
        self.generation = 0

        if random_seed is not None:
            random.seed(random_seed)


    def _default_fitness(self, chromosome: List[CourseSession], idx: int) -> float:
        penalty = self.constraint_engine.evaluate(chromosome)
        return 1.0 / (penalty + 1.0)

    def fitness(self, chromosome: List[CourseSession], idx: int) -> float:
        if self._fitness_func:
            return self._fitness_func(chromosome, idx)
        return self._default_fitness(chromosome, idx)


    def _random_chromosome(self) -> List[CourseSession]:
        chrom = []
        for tmpl in self.sessions_template:
            s = copy.copy(tmpl)
            # days = allowed_days(s)
            s.day = random.choice(DAYS)
            slots = allowed_slots(s, s.day)
            s.slot_index = random.choice(slots)
            s.room = random.choice(ROOMS)
            chrom.append(s)
        return chrom

    def _init_population(self):
        self.population = [self._random_chromosome() for _ in range(self.sol_per_pop)]


    def _evaluate_all(self) -> List[float]:
        return [self.fitness(chrom, i) for i, chrom in enumerate(self.population)]

    def _select_parents(self, fitnesses: List[float]) -> List[List[CourseSession]]:
        n = self.num_parents_mating
        if self.parent_selection_type == "tournament":
            return self._tournament_selection(fitnesses, n)
        elif self.parent_selection_type == "roulette":
            return self._roulette_selection(fitnesses, n)
        else:
            return self._rank_selection(fitnesses, n)

    def _tournament_selection(self, fitnesses, n, k=3):
        parents = []
        for _ in range(n):
            contenders = random.sample(range(len(self.population)), min(k, len(self.population)))
            winner = max(contenders, key=lambda i: fitnesses[i])
            parents.append(copy.deepcopy(self.population[winner]))
        return parents

    def _roulette_selection(self, fitnesses, n):
        min_f = min(fitnesses)
        shifted = [f - min_f + 1e-6 for f in fitnesses]
        total = sum(shifted)
        parents = []
        for _ in range(n):
            pick = random.uniform(0, total)
            cum = 0
            for i, w in enumerate(shifted):
                cum += w
                if cum >= pick:
                    parents.append(copy.deepcopy(self.population[i]))
                    break
        return parents

    def _rank_selection(self, fitnesses, n):
        ranked = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i])
        weights = list(range(1, len(ranked) + 1))
        total = sum(weights)
        parents = []
        for _ in range(n):
            pick = random.uniform(0, total)
            cum = 0
            for idx, w in zip(ranked, weights):
                cum += w
                if cum >= pick:
                    parents.append(copy.deepcopy(self.population[idx]))
                    break
        return parents

    def _crossover(self, parents: List[List[CourseSession]]) -> List[List[CourseSession]]:
        offspring = []
        num_offspring = self.sol_per_pop - self.keep_parents
        while len(offspring) < num_offspring:
            p1, p2 = random.sample(parents, 2)
            if self.crossover_type == "uniform":
                child = self._uniform_crossover(p1, p2)
            else:
                child = self._single_point_crossover(p1, p2)
            offspring.append(child)
        return offspring

    def _single_point_crossover(self, p1, p2):
        point = random.randint(1, len(p1) - 1)
        child = p1[:point] + p2[point:]
        return [copy.copy(g) for g in child]

    def _uniform_crossover(self, p1, p2):
        child = []
        for g1, g2 in zip(p1, p2):
            child.append(copy.copy(g1 if random.random() < 0.5 else g2))
        return child

    def _mutate(self, offspring: List[List[CourseSession]]) -> List[List[CourseSession]]:
        for chrom in offspring:
            for gene in chrom:
                if random.random() < self.mutation_probability:
                    self._mutate_gene(gene)
        return offspring

    def _mutate_gene(self, gene: CourseSession):
        choice = random.randint(0, 2)
        if choice == 0:
            # days = allowed_days(gene)
            gene.day = random.choice(DAYS)
            slots = allowed_slots(gene, gene.day)
            gene.slot_index = random.choice(slots)
        elif choice == 1:
            if gene.day:
                slots = allowed_slots(gene, gene.day)
                gene.slot_index = random.choice(slots)
        else:
            gene.room = random.choice(ROOMS)

    def _elitism(self, fitnesses: List[float]) -> List[List[CourseSession]]:
        sorted_idx = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
        return [copy.deepcopy(self.population[i]) for i in sorted_idx[:self.keep_parents]]

    def run(self):
        self._init_population()
        for gen in range(self.num_generations):
            self.generation = gen + 1
            fitnesses = self._evaluate_all()
            best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
            best_fit = fitnesses[best_idx]
            avg_fit = sum(fitnesses) / len(fitnesses)
            self.fitness_history.append(best_fit)
            self.avg_fitness_history.append(avg_fit)

            if best_fit > self.best_fitness:
                self.best_fitness = best_fit
                self.best_solution = copy.deepcopy(self.population[best_idx])

            if self.on_generation:
                self.on_generation(self)

            if self.best_fitness == 1:
                print(f"  [Gen {gen+1}] Perfect solution found! Fitness = 1")
                break

            # Build next generation
            elites = self._elitism(fitnesses)
            parents = self._select_parents(fitnesses)
            offspring = self._crossover(parents)
            offspring = self._mutate(offspring)
            self.population = elites + offspring

        if self.on_stop:
            self.on_stop(self, self.best_solution, self.best_fitness)

        return self.best_solution, self.best_fitness

    def best_solution_fitness(self):
        return self.best_fitness

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "GA SCHEDULER — SUMMARY",
            "=" * 60,
            f"  Generations run  : {self.generation}",
            f"  Population size  : {self.sol_per_pop}",
            f"  Crossover type   : {self.crossover_type}",
            f"  Parent selection : {self.parent_selection_type}",
            f"  Mutation prob    : {self.mutation_probability}",
            f"  Best fitness     : {self.best_fitness:.5f}",
            f"  Penalty (hard)   : {self.best_fitness:.5f}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def get_schedule_as_dict(self) -> List[Dict]:
        if not self.best_solution:
            return []
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
        result.sort(key=lambda x: (day_order.get(x["day"], 99), x["start_time"] or "", x["room"] or ""))
        return result

    def constraint_breakdown(self) -> Dict[str, int]:
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