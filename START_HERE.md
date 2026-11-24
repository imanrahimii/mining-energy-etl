# Mining Energy ETL and Forecasting

Build a daily electricity cost report for two simulated mining sites, then use the processed data to forecast electricity consumption in Azure Databricks.

## 1. Know the workflow

- **Extract:** Read meter readings and site tariffs from CSV files in a Unity Catalog volume.
- **Transform:** Remove duplicates, record invalid rows with their rejection reasons, calculate cost in cents, and aggregate by date and site.
- **Load:** Write the clean readings, rejected rows, and daily cost report to Delta tables.
- **Machine learning:** Join the daily usage table with operating plans. Train and evaluate a Random Forest, then forecast electricity use for the next five days.

## 2. Import the notebooks

Extract the ZIP on your computer. In your existing Azure Databricks workspace, open **Workspace**, create a personal project folder, and use its **Import** menu to import both files from the **notebooks** folder individually. Open **01_mining_energy_etl** and select **Serverless** in its compute selector.

Check the **CATALOG** setting in the first code cell. The supplied value is **dbw_sales_iman01**. Use the same writable Unity Catalog catalog in both notebooks. Run only the first code cell in notebook 01. It creates the **iman_energy_etl_lab** schema and the **incoming** volume, then prints the volume path. You need permission to create the schema and volume.

## 3. Run the small ETL example

In **Catalog**, open your catalog, then **iman_energy_etl_lab → incoming**. Use **Upload files to a volume** and upload **data/meter_readings.csv** and **data/tariffs.csv** directly into that volume. Alternatively, use **File → Upload files to volume** from a notebook and select the printed path.

Keep **USE_HISTORY = False** and run the remaining cells of notebook 01 in order. Check the result at each stage.

| Stage | Expected result |
|---|---|
| Extract | 10 meter readings and 2 site tariffs |
| Transform | 6 accepted readings, 3 rejected readings, 1 duplicate removed |
| Load | 6 rows in silver_energy_readings, 3 in rejected_energy_readings, 4 in gold_daily_energy_cost |

For November 1 at NORTH, the 100 and 200 kWh readings total 300 kWh. At 20 cents per kWh, the cost is 6,000 cents or AUD 60. The four report rows sum to 1,300 kWh and AUD 320. Compare them with **data/expected_daily.csv**, which stores costs in cents.

## 4. Prepare the historical data

Upload **data/meter_history.csv**, **data/historical_plans.csv**, and **data/future_plans.csv** to the same volume. Keep the original **tariffs.csv** there. Set **USE_HISTORY = True** in notebook 01 and run it from the top.

The historical extract contains 226 readings. Expect 224 accepted readings, 1 rejection, and 1 duplicate removed. The resulting **gold_daily_energy_cost** table contains 112 rows, one for each site and date. Each run replaces the three ETL output tables in the practice schema. To restore the four-row report, switch back to sample mode and rerun notebook 01.

## 5. Train, evaluate, and forecast

Open **02_energy_forecast** and attach Serverless. Run the first cell to install the pinned scikit-learn version. The environment needs Python 3.11 or later. If the install succeeds but the new package cannot be imported, restart Python in a fresh cell using **dbutils.library.restartPython()** and continue with the configuration cell. Run the remaining cells in order.

The notebook matches the historical plans and actual usage by date and site. Model inputs are site, planned operating hours, load index, and forecast temperature. The target is daily electricity consumption in kWh. The October records train the model. The subsequent observed records evaluate it.

| Checkpoint | Expected result |
|---|---|
| Training and evaluation | 62 training rows and 50 test rows |
| Mean absolute error on test data | About 66 kWh for Random Forest and 296 kWh using each site's October mean |
| Forecast | 10 rows in gold_energy_forecast, covering two sites over five days |

MAE is the average size of the prediction error in kWh. The numbers above are from a local run on synthetic data. The future rows have no observed consumption, so the displayed MAE is calculated from the historical test period.

## 6. Find your results

Open **Catalog → your catalog → iman_energy_etl_lab → Tables**. The table **gold_daily_energy_cost** shows recorded consumption and calculated cost. **gold_energy_forecast** shows predicted consumption. The final output cell in each notebook also displays its report.

If you see a missing file error, confirm the filename and volume path. If notebook 02 asks for history mode, run notebook 01 with USE_HISTORY set to True and check for 112 daily rows before retrying.

Continue with [CI_GUIDE.html](CI_GUIDE.html) to run the automated checks in GitHub Actions.

References: [Import notebooks](https://learn.microsoft.com/en-us/azure/databricks/notebooks/notebook-export-import) · [Upload volume files](https://learn.microsoft.com/en-us/azure/databricks/volumes/volume-files) · [Notebook Python libraries](https://learn.microsoft.com/en-us/azure/databricks/libraries/notebooks-python-libraries)
