# Ecosystem Sustainability Simulator - McKinsey Discontinued test in Solve

## Overview

This project implements a **constraint-based ecosystem sustainability simulator**.

Given a set of species with:
- limited shared resources,
- priority-based consumption rules,
- irreversible depletion,
- and extinction constraints,

the simulator determines **which combinations of species can coexist sustainably**.

The project focuses on **formalizing ambiguous system rules into deterministic, executable logic**.

---

## Problem Class

Many real-world systems share similar characteristics:

- agents consume shared resources,
- consumption follows priority or ordering rules,
- resources deplete irreversibly,
- local feasibility does not imply global feasibility,
- intuition often fails due to second-order effects.

This simulator models such systems and evaluates **feasibility**, not optimization.

---

## What the Simulator Does

For a given ecosystem definition, the simulator:

1. Enumerates all valid combinations of agents (species)
2. Simulates sequential consumption under greedy priority rules
3. Dynamically updates system state after each action
4. Detects failure conditions such as:
   - unmet consumption needs
   - resource exhaustion (extinction)
5. Returns all combinations that are **globally sustainable**

The simulation is **fully deterministic** and **order-sensitive**.

---

## Key Modeling Features

- **Priority-based consumption**  
  Agents consume resources in descending priority order.

- **Dynamic re-ordering**  
  Consumption reduces available resources, which can change future priority ordering.

- **Shared resource pools**  
  Multiple agents may compete for the same resource.

- **Extinction constraints**  
  If any resource is fully depleted, the configuration is considered unsustainable.

- **Combinatorial evaluation**  
  All possible agent subsets are evaluated exhaustively.

---

## Input Model

The simulator accepts an Excel file defining one or more ecosystems.

Each row represents a species with the following fields:

| Column | Description |
|------|------------|
| Ecosystem | Ecosystem identifier |
| Species | Unique species name |
| Type | Producer or Animal |
| CaloriesProvided | Resource units available |
| CaloriesNeeded | Resource units required (animals only) |
| FoodSources | Comma-separated list of species this species can consume |

Producers are always included; combinations are evaluated over subsets of animals.

---

## Output

For each ecosystem, the simulator reports:

- whether **any sustainable configuration exists**
- how many sustainable configurations were found
- the exact species combinations that satisfy all constraints

Results are exported to Excel for inspection.

---

## Why This Project Exists

This project explores:

- how hidden constraints emerge in dynamic systems,
- why greedy local decisions can cause global failure,
- how to rigorously validate feasibility under ambiguity,
- how narrative rules can be translated into executable logic.

It is intentionally **generic** and **domain-agnostic**.

---

## What This Is Not

- This is not a game solver.
- This is not an optimization engine.
- This is not designed for end-user consumption.

It is a **systems modeling and reasoning artifact**.

---

## Project Structure

.
├── solve_ecosystem.py # Core simulation logic
├── input.xlsx # Example input file
├── solve_output.xlsx # Generated output
└── README.md


---

## Running the Simulator

1. Install dependencies:
   ```bash
   pip install pandas openpyxl
2. Place input.xlsx in the project directory.

3. Run: python solve_ecosystem.py

4. Review results in solve_output.xlsx.

## Notes

The simulator assumes clean and consistent input data.
All logic is deterministic; identical inputs always produce identical outputs.
Full resource depletion is treated as a failure condition by design.

## License

This project is provided for demonstration and educational purposes.
