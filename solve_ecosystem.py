import itertools
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import pandas as pd


SHEET_NAME = "Species"


@dataclass(frozen=True)
class Species:
    name: str
    typ: str  # "Producer" or "Animal"
    cp0: float
    cn0: float
    foods: Tuple[str, ...]  # species names it can eat


def parse_food_sources(cell: object) -> Tuple[str, ...]:
    if cell is None:
        return tuple()
    if isinstance(cell, float) and math.isnan(cell):
        return tuple()
    s = str(cell).strip()
    if not s:
        return tuple()
    return tuple([x.strip() for x in s.split(",") if x.strip()])


def load_ecosystems(excel_path: str) -> Dict[str, Dict[str, Species]]:
    df = pd.read_excel(excel_path, sheet_name=SHEET_NAME)

    required = ["Ecosystem", "Species", "Type", "CaloriesProvided", "CaloriesNeeded", "FoodSources"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in '{SHEET_NAME}': {missing}")

    ecosystems: Dict[str, Dict[str, Species]] = {}
    for _, r in df.iterrows():
        eco = str(r["Ecosystem"]).strip()
        name = str(r["Species"]).strip()
        typ = str(r["Type"]).strip()

        cp0 = float(r["CaloriesProvided"])
        cn0 = float(r["CaloriesNeeded"])
        foods = parse_food_sources(r["FoodSources"])

        ecosystems.setdefault(eco, {})
        ecosystems[eco][name] = Species(
            name=name,
            typ=typ,
            cp0=cp0,
            cn0=cn0,
            foods=foods
        )

    return ecosystems


def simulate_set(
    sp_map: Dict[str, Species],
    producers: Tuple[str, ...],
    animals: Tuple[str, ...],
    eps: float = 1e-9
) -> bool:
    """
    Returns True iff configuration is sustainable under Solve rules.

    Dynamic turn order:
      - After each animal finishes eating, choose next eater = animal with highest CURRENT CP among those with CN > 0.
      - Not mid-turn.
    """
    selected = set(producers) | set(animals)

    # Remaining calories provided (pool) for each selected species
    cp: Dict[str, float] = {s: sp_map[s].cp0 for s in selected}

    # Remaining calories needed for each selected animal
    cn: Dict[str, float] = {a: sp_map[a].cn0 for a in animals}

    # Loop until all animals are satisfied or one fails
    while True:
        hungry = [a for a in animals if cn[a] > eps]
        if not hungry:
            # all satisfied
            return True

        # Next eater: highest CURRENT CP among hungry animals (deterministic tie-break by name)
        eater = max(hungry, key=lambda a: (cp.get(a, 0.0), a))

        need = cn[eater]
        if need <= eps:
            cn[eater] = 0.0
            continue

        allowed_foods = [f for f in sp_map[eater].foods if f in selected]
        if not allowed_foods:
            return False

        # Eater consumes until CN hits 0 or it runs out of usable food
        while need > eps:
            available = [(f, cp.get(f, 0.0)) for f in allowed_foods if cp.get(f, 0.0) > eps]
            if not available:
                return False

            # Pick food source(s) with highest CURRENT CP
            max_cp = max(v for _, v in available)
            top = [f for f, v in available if abs(v - max_cp) <= eps]

            k = len(top)
            if k == 0:
                return False

            # Equal split if tie
            min_top_cp = min(cp[f] for f in top)
            max_total_take = k * min_top_cp
            take_total = min(need, max_total_take)
            take_each = take_total / k

            for f in top:
                cp[f] -= take_each
                    # Never allow negative
                if cp[f] < -eps:
                        return False

                    # EXTINCTION RULE: CP must never become 0 (or below) for any selected species
                if cp[f] <= eps:
                       return False


            need -= take_total

        cn[eater] = 0.0
        # Important: turn ends. We do NOT keep a static order. Next iteration picks next eater based on updated cp.

    # Unreachable
    # return False


def find_sustainable_sets_for_ecosystem(
    sp_map: Dict[str, Species],
    animals_to_choose: int = 5,
    cap_results: Optional[int] = None
) -> List[Dict[str, object]]:
    producers = tuple([s.name for s in sp_map.values() if s.typ == "Producer"])
    animals_all = [s.name for s in sp_map.values() if s.typ == "Animal"]

    if len(producers) != 3:
        raise ValueError(f"Expected exactly 3 producers, found {len(producers)}")
    if len(animals_all) != 10:
        raise ValueError(f"Expected exactly 10 animals, found {len(animals_all)}")

    results: List[Dict[str, object]] = []

    for animal_set in itertools.combinations(animals_all, animals_to_choose):
        ok = simulate_set(sp_map, producers, animal_set)
        if ok:
            results.append({
                "Producers": ", ".join(producers),
                "Animals": ", ".join(animal_set),
                "AllSpecies": ", ".join(list(producers) + list(animal_set)),
            })
            if cap_results is not None and len(results) >= cap_results:
                break

    return results


def run_solver(
    input_excel: str,
    output_excel: str = "solve_output.xlsx",
    animals_to_choose: int = 5,
    cap_results_per_ecosystem: Optional[int] = None
) -> None:
    ecosystems = load_ecosystems(input_excel)

    summary_rows = []
    all_sets_rows = []

    for eco, sp_map in ecosystems.items():
        sustainable_sets = find_sustainable_sets_for_ecosystem(
            sp_map,
            animals_to_choose=animals_to_choose,
            cap_results=cap_results_per_ecosystem
        )

        summary_rows.append({
            "Ecosystem": eco,
            "AnimalsChosen": animals_to_choose,
            "TotalCombosTested": math.comb(10, animals_to_choose),
            "NumSustainableSetsFound": len(sustainable_sets),
            "HasAnySustainableSet": len(sustainable_sets) > 0,
            "Capped": cap_results_per_ecosystem is not None,
        })

        for idx, row in enumerate(sustainable_sets, start=1):
            all_sets_rows.append({
                "Ecosystem": eco,
                "SetID": idx,
                **row
            })

    summary_df = pd.DataFrame(summary_rows).sort_values(["Ecosystem"])
    sets_df = pd.DataFrame(all_sets_rows).sort_values(["Ecosystem", "SetID"]) if all_sets_rows else pd.DataFrame(
        columns=["Ecosystem", "SetID", "Producers", "Animals", "AllSpecies"]
    )

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        sets_df.to_excel(writer, index=False, sheet_name="SustainableSets")

    print(f"Wrote results to: {output_excel}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    # Example:
    # python solve_ecosystem.py
    # Make sure your file is named input.xlsx OR change this path.
    run_solver(
        input_excel="input.xlsx",
        output_excel="solve_output.xlsx",
        animals_to_choose=5,
        cap_results_per_ecosystem=None
    )
