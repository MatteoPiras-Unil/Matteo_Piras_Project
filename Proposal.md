# Short-Term Momentum Strategy on Global Stocks (2020–2025)
### Category: Data Analysis & Financial Modeling

## Motivation

*"**Momentum** is the observation that financial assets trending strongly in a certain direction will continue to move in that direction. The concept of momentum is based on similar theories in physics, where an object in motion tends to stay in motion unless disrupted by an external force."*
- [CorporateFinanceInstitute](https://corporatefinanceinstitute.com/resources/career-map/sell-side/capital-markets/momentum/)

The first research on the momentum effect was conducted by **Jegadeesh and Titman (1993)**[1], who discovered that stocks with strong past performance tend to do better than stocks with poor past performance and the overall market over medium/long term horizons. This study contradict the **Efficient Market Hypothesis** that states that it's impossible to perform better than the market, reveiling that the human factor, such as investors over/under reacting to certain news, allows financial trends to persist beyond what the theory would justify.

While the momentum definition seems simple, financial experts classify the momentum effect as a **market anomaly**. With this project, I want to analyse, using the **MSCI World Index**, wether this momentum effect remains present in recent years (2020-2025) and especially if this trend can be observed even within such a short time window.

Understanding the presence of this effect in today's environment seems relevant, where financial market are more connected than ever and events like the **COVID-19 pandemic**, rising incertitude and geopolitical tension. If the momentum effect still shows up under these conditions, it would suggests that strctural inefficiencies are still embedded in nowadays's financial market.

The goal of this project is to construt a portfolio with a subset of the best stocks (relative to momentum) and see if it actually outperform the general index. In addiction, to better validate the results, a similar portfolio but with the worst stocks will also be built to offer a comparison on returns differentials between winners and losers.

## Approach
1. **Data Preparation**
   - Load and explore dataset.
   - Clean and keep only relevant datas.
2. **Finance analysis**
   - Compute monthly momentum for each stock.
   - Define winners/losers subset with fixed entities for each month and create graphical results.
   - Compute monthly returns for each stock to create comparative graphs.
   - Other metrics to support momentum theory like **Sharpe Ratio**, **volatility**, **mean returns**.
3. **Graphic Visualization**
   - Create various graphs and charts to visualize the results (Momentum graphs, return graphs,...).

## Challenges
   - **Data completeness:** missing data may occur or multiple currency values that could distort results.
   - **Computational load:** processing computation for a large number of stock can be slow if the code is not well optimized.

## Success if...
The project will be successfull if I can demonstrate that the **Momentum Theory** is supported by data analysis and be clearly shown via visualization.
In other words, if the portfolio with the best momentum stocks performs better than the benchmark (and viceversa for the worst momentum stocks).

## Stretch Goals
   - Geographic-level analysis.
   - Different time approach (3 months, 6 months,...).

## Data Source
MSCI World Index's datas are retrieved from **Reuters DataStream** and, which is a subscription website and therefore no link is avaiable but the dataset will be uploaded on GitHub. It consists of the stocks present in this index with their market capitalization, end of the month stock price from 2018 to september 2025 and other informations about the stock. 

## Bibliography
[1]: Jegadeesh, Narasimhan, and Sheridan Titman. “Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.” The Journal of Finance, vol. 48, no. 1, 1993, pp. 65–91. JSTOR, https://doi.org/10.2307/2328882. Accessed 15 Oct. 2025.