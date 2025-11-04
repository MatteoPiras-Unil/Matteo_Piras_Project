"""This script reads a CSV file containing metrics summary and generates a pretty table as a PNG image."""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/metrics_summary.csv", index_col=0)
fig, ax = plt.subplots(figsize=(8, 2 + 0.4*len(df)))
ax.axis("off")
tbl = ax.table(
    cellText=df.round(3).values,
    colLabels=df.columns,
    rowLabels=df.index,
    loc="center",
    cellLoc="center"
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
plt.tight_layout()
plt.savefig("results/metrics_table.png", dpi=300)
