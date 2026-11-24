# Mining Energy ETL and Forecasting

An Azure Databricks practice project that turns synthetic electricity meter readings into Delta reports and forecasts daily consumption with Random Forest.

- [Start here](START_HERE.html) for the Databricks lab. [Markdown version](START_HERE.md).
- [CI guide](CI_GUIDE.html) for GitHub Actions and local tests. [Markdown version](CI_GUIDE.md).

Notebook 01 runs in sample mode by default, producing a four-row cost report totaling AUD 320. History mode produces 112 site-day rows for notebook 02, which trains, evaluates, and writes 10 forecasts. Both notebooks use the same Unity Catalog schema.
