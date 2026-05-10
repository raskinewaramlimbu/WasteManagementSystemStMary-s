"""Chart generation using matplotlib; saves PNG files to /charts/."""
import os
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for CLI use
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


def _save(filename: str):
    path = os.path.join(CHARTS_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    return path


def plot_completion_rates(data: list[dict]) -> str:
    """Bar chart: collection completion rate per route."""
    if not data:
        return ""
    routes = [d["route"] for d in data]
    rates  = [d["rate_pct"] for d in data]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(routes, rates, color="#4CAF50", edgecolor="black")
    ax.axhline(100, color="red", linestyle="--", linewidth=0.8, label="100%")
    ax.set_ylabel("Completion Rate (%)")
    ax.set_title("Collection Completion Rate by Route")
    ax.set_ylim(0, 110)
    ax.set_xticklabels(routes, rotation=30, ha="right")
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{rate}%", ha="center", va="bottom", fontsize=8)
    return _save("completion_rates.png")


def plot_recycling_by_material(data: list[dict]) -> str:
    """Pie chart: recycled weight split by material type."""
    if not data:
        return ""
    labels  = [d["material"] for d in data]
    weights = [d["weight_kg"] for d in data]
    colours = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0", "#F44336", "#00BCD4"]

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(weights, labels=labels, autopct="%1.1f%%",
           colors=colours[:len(labels)], startangle=140)
    ax.set_title("Recycled Material Weight Distribution")
    return _save("recycling_materials.png")


def plot_contamination_by_material(data: list[dict]) -> str:
    """Bar chart: average contamination rate per material."""
    if not data:
        return ""
    labels = [d["material"] for d in data]
    rates  = [d["avg_contamination_pct"] for d in data]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(labels, rates, color="#F44336", edgecolor="black")
    ax.set_ylabel("Avg Contamination (%)")
    ax.set_title("Average Contamination Rate by Material Type")
    ax.set_ylim(0, max(rates) * 1.2 + 5 if rates else 10)
    return _save("contamination_by_material.png")


def plot_incident_types(data: list[dict]) -> str:
    """Horizontal bar chart: incident counts by type."""
    if not data:
        return ""
    from collections import defaultdict
    totals = defaultdict(int)
    for row in data:
        totals[row["type"]] += row["count"]

    types  = list(totals.keys())
    counts = [totals[t] for t in types]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(types, counts, color="#FF9800", edgecolor="black")
    ax.set_xlabel("Number of Incidents")
    ax.set_title("Incident Reports by Type")
    return _save("incident_types.png")


def plot_missed_collections(data: list[dict]) -> str:
    """Bar chart: missed collections by route."""
    if not data:
        return ""
    routes = [d["route"] for d in data]
    missed = [d["missed"] for d in data]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(routes, missed, color="#9C27B0", edgecolor="black")
    ax.set_ylabel("Missed Collections")
    ax.set_title("Missed Collections by Route")
    ax.set_xticklabels(routes, rotation=30, ha="right")
    return _save("missed_collections.png")
