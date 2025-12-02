# AI Tool Usage Disclosure
## Overview
This document explains how AI tools were used during the development of my Momentum Strategy on the MSCI World Index project.
It also acknowledges that this disclosure itself was drafted with the help of AI and then reviewed and adapted by me.

## Tools Used
- ChatGPT (GPT-5.1) — debugging, refactoring, clarifying concepts
- GitHub Copilot — inline code suggestions

## AI Contributions
1. **Portfolio Construction Logic**
AI tools provided structural guidance for:
- ```build_portfolio.py```
- the monthly rebalancing mechanism
- multi-horizon lookback support (1m, 3m, 6m, 12m)

I implemented the final logic, adapted it to the dataset, corrected errors, and validated all financial formulas (CAGR, annualized volatility, Sharpe, Sortino, HAC p-values).
2. Metrics Computation
I received help designing:

- ```metrics_table()``` in ```src/momentum/metrics.py```
- HAC (Newey–West) statistical testing structure

I verified the computations, ensured proper series alignment, and confirmed that the results were economically consistent.
3. Automated Pipeline
AI contributed to the initial structure of:

- ```main.py```
- command-line argument flow
- sequential execution of data → portfolios → metrics → plots

I completed the pipeline, ensured reproducibility, resolved environment issues, and confirmed correct behaviour on both Nuvolos and local execution.
4. Visualization
AI generated base templates for:

- ```summarize_results.py```
- ```pretty_table.py```

I refined the visualizations, fixed formatting, ensured consistency across horizons, and validated the accuracy of all plotted metrics.

## Learning Achievements
Working with AI improved my understanding of:

- HAC/Newey–West variance estimation
- time-series alignment principles
- modular project architecture
- best practices for handling financial return data
- reproducible research workflows

## Summary
AI tools assisted in generating ideas, examples, and explanations, but I maintained full control over all code, methodology, and interpretation.
Every analytical decision and final implementation reflects my own work.



