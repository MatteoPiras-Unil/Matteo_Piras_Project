# 📈 Momentum Strategy on the MSCI World Index

## Overview
This project aim to analyze the **Momentum Effect** in the global equity markets using data from the **MSCI World Index** dataset, composed of 1465 stocks.
The goal is to test if stocks that have performed well in the past continue to do so in the short term. These stocks's performance are then compared to the benchmark using equal-weighted momentum portfolios. 

## Motivation
The **Momentum Effect** is one of the most persistent market anomalies. 
Firstly documented by **Jegadeesh and Titman (1993)**, it shows how stocks with strong past performances tend to keep this trend in the future.

On this idea, the project aims to:
- Measure the momentum's strenght along all stocks
- Build and evaluate whether momentum-based portfolios can outperform a passive benchmark (iShares in this case)
- Compare portfolios on theirs lookback periods.

## Data
- **Dataset**: MSCI World Index[1]
- **Period**: from 31.12.2018 to 30.09.2025
- **Frequency**: monthly prices converted to monthly returns
- **Variables used**:
    - Stock ticker
    - Monthly closing prices
    - Market capitalization

## Methodology
1. **Compute Momentum**
    - For each stock *i* at time *t*:
    $$
    M_{i,t} = \frac{P_{i,t-1}}{P_{i,t-k-1}} - 1
    $$
    where *k* is the lookback period (1,3,6,12)
2. **Rank Stocks**
    - At each period *t*, rank all stocks by $M_{i,t}$.
    - Define the winner as the **best 10, 20, 30, 40, 50** stocks by momentum.
3. **Form Portfolio**
    - Build equally weighted portfolios including only the best ones according to momentum
    - Compare the performance of portfolios to the benchmark.
4. **Rebalance**
    - Every month, the portfolio is rebalanced with the new top ***N*** stocks.
5. **Backtest performance**
    - Compute monthly returns of portfolios and benchmark.
    - Performance metrics: mean return, aggregated/annual return, volatility, Sharpe ratio, to help the analysis.
    - Build comparative chart and summary statistics for each horizon.

## Results Summary
- Equally weighted portfolios outperformed the benchmark in most of the horizon considered.
- Momentum effect persisted more on smaller-sized portfolios but this comes with an higher volatility (the bigger the return, the bigger the volatility)
- The use of equal weighted portfolio rather than market-cap weighting helps to have a clearer exposure to the pure momentum effect, which tends to be more dominated by bigger stocks and may reflects fundamentals rather than a clean momentum effect[2].

## Repository Structure
```
Matteo_Piras_Project/
│
├── .venv/ # Virtual environment
├── .vscode/ # VS Code settings
│
├── config/ # Configuration files
├── data/ # Datasets (raw and cleaned)
├── results/ # Output: figures, tables, results
├── scripts/ # Helper or setup scripts
├── src/ # Core source code
├── tests/ # Unit tests
│
├── .env # Environment variables
├── .gitignore # Git ignore file
├── Proposal.md # Project proposal
├── README.md # Documentation
├── requirements.txt # Python dependencies
└── run_all.py # Main pipeline runner
```

## Installation & Usage
1. **Clone the repository**
```
git clone https://github.com/MatteoPiras-Unil/Matteo_Piras_Project
cd /files/Matteo_Piras_Project
```
2. **Create and activate virtual environment**
```
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```
3. **Install dependencies**
```
pip install -r requirements.txt
```
4. **Run pipeline**
```
python run_all.py
```

This line will:
- Compute momentum scores
- Select top ***N*** stocks for each rebalance date
- Build equally weighted portfolio
- Calculate portfolios and benchmark returns
- Output all summary statistics and chart in the folder ```results/```

## Example Output
![Momentum vs Benchmark](results/portfolio_vs_benchmark_12m.png)


## Note
If libraries are outdated or are not imported correctly, please run this block:
```
pip freeze --local > requirements.txt
pip install -r requirements.txt
```
This should ensure that every library used in the environment is listed in ```requirements.txt``` and therefore installed.



## Bibliography
-[1]: MSCI World Index. (n.d.). https://www.msci.com/indexes/index/990100

-[2]: Swade, A., Sandra, N., Shackleton, M. B., & Lohre, H. (2022, November 18). Why do equally weighted portfolios beat Value-Weighted ones? https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4280394