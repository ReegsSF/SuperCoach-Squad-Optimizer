import pandas as pd
from pulp import *

print("🔥 AFL SUPERCOACH 2026 – OPTIMISER 🔥")

SALARY_CAP = 10_000_000
BENCH_PRICE_LIMIT = 200_000

MIN_CAP_SPEND_RATIO = 0
MIN_SALARY_SPEND = SALARY_CAP * MIN_CAP_SPEND_RATIO

POINTS_WEIGHT = 1.0
CASH_WEIGHT = 0.01

ELITE_BONUS = 10

ELITE_THRESHOLDS = {
    "DEF": 104,
    "MID": 116,
    "RUC": 115,
    "FWD": 100
}

# ------------------------
# LOAD DATA
# ------------------------
INPUT_FILE = "input.csv"
df = pd.read_csv(INPUT_FILE)
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

df["positions"] = df["position"].apply(lambda x: x.split("|"))

def primary_position(pos_list):
    if "RUC" in pos_list:
        return "RUC"
    if "FWD" in pos_list:
        return "FWD"
    if "DEF" in pos_list:
        return "DEF"
    return "MID"

df["primary_pos"] = df["positions"].apply(primary_position)

# ------------------------
# ELITE BONUS (PRIMARY POSITION ONLY)
# ------------------------
def elite_bonus(row):
    avg = row["expected_avg"]
    pos = row["primary_pos"]

    if pos == "DEF" and avg >= 104:
        return ELITE_BONUS
    if pos == "MID" and avg >= 116:
        return ELITE_BONUS
    if pos == "RUC" and avg >= 115:
        return ELITE_BONUS
    if pos == "FWD" and avg >= 100:
        return ELITE_BONUS
    return 0

df["elite_bonus"] = df.apply(elite_bonus, axis=1)

# ------------------------
# DETECT EARLY BYE
# ------------------------
def detect_early_bye(val):
    if isinstance(val, str) and "|" in val:
        return 1
    return 0

df["early_bye"] = df["bye"].apply(detect_early_bye)

# ------------------------
# APPLY BYE ADJUSTMENT
# ------------------------
def apply_bye_adjustment(row):
    avg = row["expected_avg"]
    price = row["price"]

    if row["early_bye"] == 1:
        if price > 500_000:
            return avg - 3
        elif 350_000 <= price <= 499_999:
            return avg - 2
        elif 200_000 <= price <= 349_999:
            return avg
        else:
            return avg + 2
    return avg

df["adjusted_avg"] = df.apply(apply_bye_adjustment, axis=1)

# ------------------------
# NORMALISE CASH GENERATION
# ------------------------
max_cash = df["price_change"].max()
df["cash_score"] = 0 if max_cash == 0 else df["price_change"] / max_cash

players = df.index.tolist()

# ------------------------
# MODEL
# ------------------------
model = LpProblem("AFL_Supercoach_2026", LpMaximize)

x = LpVariable.dicts("squad", players, cat="Binary")

field_positions = ["DEF", "MID", "RUC", "FWD", "FLEX"]
bench_positions = ["DEF", "MID", "RUC", "FWD"]

y = LpVariable.dicts(
    "onfield",
    [(p, pos) for p in players for pos in field_positions],
    cat="Binary"
)

z = LpVariable.dicts(
    "bench",
    [(p, pos) for p in players for pos in bench_positions],
    cat="Binary"
)

# ------------------------
# OBJECTIVE
# ------------------------
model += lpSum(
    x[p] * (
        POINTS_WEIGHT * (df.loc[p, "adjusted_avg"] + df.loc[p, "elite_bonus"])
        + CASH_WEIGHT * df.loc[p, "cash_score"]
    )
    for p in players
)

# ------------------------
# SQUAD CONSTRAINTS
# ------------------------
model += lpSum(x[p] for p in players) == 31
model += lpSum(x[p] * df.loc[p, "price"] for p in players) <= SALARY_CAP
model += lpSum(x[p] * df.loc[p, "price"] for p in players) >= MIN_SALARY_SPEND

model += lpSum(x[p] for p in players if "DEF" in df.loc[p, "positions"]) >= 8
model += lpSum(x[p] for p in players if "MID" in df.loc[p, "positions"]) >= 11
model += lpSum(x[p] for p in players if "FWD" in df.loc[p, "positions"]) >= 8
model += lpSum(x[p] for p in players if "RUC" in df.loc[p, "positions"]) == 3

# ------------------------
# EARLY BYE PREMIUM LIMITS (PRIMARY POS ONLY)
# ------------------------
EARLY_BYE_PRICE_THRESHOLD = 400_000

for pos in ["DEF", "MID", "FWD", "RUC"]:
    model += lpSum(
        x[p]
        for p in players
        if (
            df.loc[p, "primary_pos"] == pos
            and df.loc[p, "early_bye"] == 1
            and df.loc[p, "price"] > EARLY_BYE_PRICE_THRESHOLD
        )
    ) <= 1

# ------------------------
# ON FIELD STRUCTURE
# ------------------------
model += lpSum(y[(p, "DEF")] for p in players) == 6
model += lpSum(y[(p, "MID")] for p in players) == 8
model += lpSum(y[(p, "RUC")] for p in players) == 2
model += lpSum(y[(p, "FWD")] for p in players) == 6
model += lpSum(y[(p, "FLEX")] for p in players) == 1

# ------------------------
# BENCH STRUCTURE
# ------------------------
model += lpSum(z[(p, "DEF")] for p in players) == 2
model += lpSum(z[(p, "MID")] for p in players) == 3
model += lpSum(z[(p, "RUC")] for p in players) == 1
model += lpSum(z[(p, "FWD")] for p in players) == 2

# ------------------------
# PLAYER ASSIGNMENT RULES
# ------------------------
for p in players:

    for pos in field_positions:
        model += y[(p, pos)] <= x[p]
        if pos != "FLEX" and pos not in df.loc[p, "positions"]:
            model += y[(p, pos)] == 0

    for pos in bench_positions:
        model += z[(p, pos)] <= x[p]
        if pos not in df.loc[p, "positions"]:
            model += z[(p, pos)] == 0

    model += (
        lpSum(y[(p, pos)] for pos in field_positions)
        + lpSum(z[(p, pos)] for pos in bench_positions)
        <= 1
    )

    model += (
        lpSum(z[(p, pos)] for pos in bench_positions)
        * df.loc[p, "price"]
        <= BENCH_PRICE_LIMIT
    )

# ------------------------
# SOLVE
# ------------------------
model.solve()

print("Status:", LpStatus[model.status])
if LpStatus[model.status] != "Optimal":
    raise Exception("❌ Infeasible solution")

# ------------------------
# BUILD OUTPUT
# ------------------------
squad = df[[x[p].value() == 1 for p in players]].copy()
total_price_change = squad["price_change"].sum()

print("\nElite players selected:")
print(
    squad[squad["elite_bonus"] > 0][
        ["name", "primary_pos", "expected_avg", "elite_bonus", "price"]
    ].sort_values("expected_avg", ascending=False)
)

print("\n📊 SUMMARY")
print("Total Squad Price:", squad["price"].sum())
print("Total Squad Adjusted Avg:", squad["adjusted_avg"].sum())
print("Total Projected Price Change:", f"${total_price_change:,.0f}")

# ------------------------
# BUILD ON-FIELD / BENCH OUTPUT
# ------------------------
on_field = []
bench = []

for p in players:
    for pos in field_positions:
        if y[(p, pos)].value() == 1:
            on_field.append((p, pos))
    for pos in bench_positions:
        if z[(p, pos)].value() == 1:
            bench.append((p, pos))

on_field_df = pd.DataFrame([
    {
        "name": df.loc[p, "name"],
        "slot": pos,
        "position": df.loc[p, "position"],
        "price": df.loc[p, "price"],
        "expected_avg": df.loc[p, "expected_avg"],
        "adjusted_avg": df.loc[p, "adjusted_avg"],
        "elite_bonus": df.loc[p, "elite_bonus"]
    }
    for p, pos in on_field
])

bench_df = pd.DataFrame([
    {
        "name": df.loc[p, "name"],
        "bench_slot": pos,
        "position": df.loc[p, "position"],
        "price": df.loc[p, "price"],
        "expected_avg": df.loc[p, "expected_avg"],
        "adjusted_avg": df.loc[p, "adjusted_avg"],
        "elite_bonus": df.loc[p, "elite_bonus"]
    }
    for p, pos in bench
])

# ------------------------
# PRINT OUTPUT
# ------------------------
print("\n🏆 ON FIELD")
for line in field_positions:
    print(f"\n{line}:")
    for _, r in (
        on_field_df[on_field_df["slot"] == line]
        .sort_values("adjusted_avg", ascending=False)
        .iterrows()
    ):
        bonus = f"+{r['elite_bonus']}" if r["elite_bonus"] > 0 else ""
        print(
            f"{r['name']} ({r['position']}) - ${r['price']:,} "
            f"- Adj {r['adjusted_avg']} {bonus}"
        )

print("\n🪑 BENCH")
for line in bench_positions:
    print(f"\n{line}:")
    for _, r in (
        bench_df[bench_df["bench_slot"] == line]
        .sort_values("price")
        .iterrows()
    ):
        bonus = f"+{r['elite_bonus']}" if r["elite_bonus"] > 0 else ""
        print(
            f"{r['name']} ({r['position']}) - ${r['price']:,} "
            f"- Adj {r['adjusted_avg']} {bonus}"
        )

print("\n📊 SUMMARY")
print("Total Squad Price:", f"${squad['price'].sum():,}")
print("Total Squad Adjusted Avg:", round(squad["adjusted_avg"].sum(), 2))
print("Total Projected Price Change:", f"${total_price_change:,.0f}")
# ------------------------
# SAVE FOR SEASON ENGINE
# ------------------------

squad_out = squad[[
    "player_id",
    "name",
    "team",
    "position",
    "price",
    "bye",
]].copy()

squad_out.to_csv("AFLSupercoach2026_Squad.csv", index=False)

print("\n💾 Starting squad saved to AFLSupercoach2026_Squad.csv")