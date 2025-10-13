# Momentum Strategy
### Category: Data Analysis & Financial Modeling

## Motivation

*"In finance, **momentum** is the empirically observed tendency for rising asset prices or securities return to rise further, and falling prices to keep falling."*
- [Wikipedia](https://en.wikipedia.org/wiki/Momentum_(finance))

While the definition of momentum seems simple, financial experts categorize it as a **market anomaly**. This project aims to analize, using the **MSCI World Index**, wether the assumption behind financial momentum is supported by data during the recent years (2020-2025). The goal is to see if, by filtering a subset of the best momentum stocks, we can outperform the passive benchmark index. 

To prove the effectivness of a momentum strategy, I will compare to the benchmark index both a subset of stocks with the **lowest momentum values** and one with the **highest momentum values**, by constructing a portfolio for each and assuming equal weighting.

## Approach
1. **Data Preparation**
   - Load and explore dataset.
   - Clean and keep only relevant datas.
2. **Finance analysis**
   - Compute monthly momentum for each stock.
   - Define top-bottom 10% for each month and create graphical results.
   - Compute monthly returns for each stock to create comparative graphs.
   - Other metrics to support momentum theory like **Sharpe Ratio**, **volatility**, **mean returns**.
3. **Graphic Visualization**
   - Create various graphs and charts to visualize the results:
             - Momentum graphs
             - Returns graphs

## Challenges
   - **Data completeness:** missing data may occur or multiple currency values that could distort results.
   - **Computational load:** processing computation for a large number of stock can be slow if the code is not well optimized.

## Success if...
The project will be successfull if I can demonstrate that the **Momentum Theory** is supported by data analysis and be clearly shown via visualization.
In other words, if the portfolio with the best momentum stocks performs better than the benchmark (and viceversa for the worst momentum stocks).

## Stretch Goals
   - Geographic-level analysis.
   - Different time approach (3 months, 6 months,...).