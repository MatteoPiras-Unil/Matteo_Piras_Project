# Short-Term Momentum Strategy on Global Stocks (2020–2025)
### Category: Data Analysis & Financial Modeling

## Motivation

*"**Momentum** is the observation that financial assets trending strongly in a certain direction will continue to move in that direction. The concept of momentum is based on similar theories in physics, where an object in motion tends to stay in motion unless disrupted by an external force."*
- [CorporateFinanceInstitute](https://corporatefinanceinstitute.com/resources/career-map/sell-side/capital-markets/momentum/)

The first research on the Momentum effect was conducted by **Jegadeesh and Titman (1993)**[1], who discovered that stocks with strong past performance tend to do better compared to stocks with poor past performance. Moreover, their study highlighted that such stocks outperformed the overall market over medium/long term horizons. This contradicts the **Efficient Market Hypothesis**[2] that states that it is impossible to perform better than the market. Thus, reveiling that the human factor, i.e. investors over/under reacting to certain news, allows financial trends to persist beyond what the historical financial theory would justify.

While the Momentum definition seems simple, financial experts classify the Momentum effect as a **market anomaly**. This project aims to analyse, using the **Morgan Stanley Capital International (MSCI) World Index**, wether this concept is present in recent years (2020-2025) and especially if this trend might be observed even within a short time frame.

In a world where financial market are more interconnected than ever and events, such as the **COVID-19 pandemic**, the growing uncertainty and the geopolitical tension, understanding the presence of the Momentum effect in today's environment is crucial. If the Momentum effect still shows up under these conditions, it would suggests that structural inefficiencies are still embedded in nowadays's financial market.

The goal of this project is to construt a portfolio with a subset of the best stocks (relative to Momentum) and see if it actually outperform the general index. In addiction, to better validate the results, a similar portfolio but with the worst stocks will also be built to offer a comparison on returns differentials between winners and losers.

## Approach
1. **Data Preparation**
   - Load and explore dataset.
   - Clean and keep only relevant data.
2. **Finance analysis**
   - Determination of Momentum Score, using MSCI Methodology[3] and assuming no risk free rate:
   `Momentum₆ₘ = (Pₜ₋₁ / Pₜ₋₇) - 1`
   - Define winners/losers subset for each month.
   - Compute monthly returns for each stock to create comparative graphs.
   - Other metrics to support momentum theory like **Sharpe Ratio**, **volatility**, **mean returns**.
3. **Graphic Visualization**
   - Create various graphs and charts to visualize the results (Momentum graphs, return graphs,...).

## Challenges
   - **Data completeness:** possibility of missing data or distort results due to the presence of multiple currencies.
   - **Computational power:** due to a large number of entries of the database, the computer might not be able to run the code. If that happens a random subset of the database is going to be selected.

## Success if...
The project is going to be successfull if it can demonstrate that the **Momentum Theory** is supported by data analysis and that it can be clearly demonstraded via visualization. In other words, the target is to prove that the portfolio with the best momentum stocks performs better than the benchmark (and viceversa for the worst momentum stocks).

## Stretch Goals
   - Continent-level analysis.
   - Different time frames (3 months, 6 months,...).

## Data Source
The MSCI World Index data has been retrieved from Refinitiv Datastream, a subscription-based financial database; therefore, a public access link is not available. However, the extracted dataset is going to be uploaded to the project’s GitHub repository. The dataset includes all constituent stocks of the MSCI World Index along with: their market capitalizations, end-of-month prices from 2018 to September 2025, and additional stock-level information. 

## Bibliography
- [1]: Jegadeesh, Narasimhan, and Sheridan Titman. “Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.” The Journal of Finance, vol. 48, no. 1, 1993, pp. 65–91. JSTOR, https://doi.org/10.2307/2328882. Accessed 15 Oct. 2025.
- [2]: Efficient-market hypothesis (EMH) | Research Starters | EBSCO Research. (n.d.). EBSCO. https://www.ebsco.com/research-starters/social-sciences-and-humanities/efficient-market-hypothesis-emh
- [3]: MSCI Inc. (2021). MSCI Momentum Indexes Methodology. In MSCI Momentum Indexes Methodology (pg. 4) (Report). https://www.msci.com/eqb/methodology/meth_docs/MSCI_Momentum_Indexes_Methodology_Aug2021.pdf