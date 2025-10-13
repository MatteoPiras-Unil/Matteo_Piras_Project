# Momentum Strategy
### Category: Data Analysis & Financial Modeling

## Motivation

*"In finance, **momentum** is the empirically observed tendency for rising asset prices or securities return to rise further, and falling prices to keep falling."*
- [Wikipedia](https://en.wikipedia.org/wiki/Momentum_(finance))

While the definition of momentum seems simple, financial experts categorizes this as a market anomaly. This project aim to analize, using the MSCI World Index, if the simple assumption on financial momentum is supported by data during the last years (2020-2025). The goal is to see if, by filtering a subset of the best momentum stocks, we can out-perform the passive benchmark index. 
To prove the effectivness of a momentum strategy, I will compare to the benchmark index a subset of stocks with the lowest momentum values and one with the highest momentum values.

## Approach
1. **Data Preparation**
   - Load and explore dataset.
   - Clean and keep only relevant datas.
2. **Finance analysis**
   - Compute monthly momentum for each stock.
   - Define top-bottom 10% for each month and create graphical results.
   - Compute monthly returns for each stock to create confrontational graph.
   - Other metrics to support momentum theory.

## Challenges
   - **Data completeness:** missing data may occur, or multiple currency values that can give falsified results
   - **Computational load:** python's run can be long if not well structured code.

## Success if...
The project will be successfull if I can show that the Momentum Theory can be proven by data analysis and be clear via visualization. In other words, if the portfolio with the best momentum stocks performs better than the benchmark (and viceversa for the worst momentum stocks).

