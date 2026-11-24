# GitHub Actions CI for Mining Energy ETL

CI checks the Python code and the sample results each time you push changes. Databricks runs the notebooks and writes the Delta tables.

## 1. Push the project with its folder structure

Create a new empty GitHub repository, for example **mining-energy-etl**. Leave the options to initialize it with a README, license or .gitignore unchecked. In VS Code open the extracted **mining_energy_etl** folder itself and select **Terminal → New Terminal**. Run the commands below, replacing YOUR-USERNAME with your GitHub username. Use Git on your computer and sign in when prompted.

```bash
git init -b main
git add .
git commit -m "Add mining energy ETL and forecasting project"
git remote add origin https://github.com/YOUR-USERNAME/mining-energy-etl.git
git push -u origin main
```

The GitHub root should display **data**, **notebooks**, **tests**, **etl_core.py**, and **ml_core.py**. Verify that **.github/workflows/ci.yml** is present. Keep the folder structure intact so the tests can locate **data/expected_daily.csv** and the other input files.

## 2. Inspect the run

Open the new repository's **Actions** tab and select **Mining energy ETL CI**. Open the latest run, then the **test** job. Expand **Test ETL and check notebook code** and look for **Ran 6 tests** and **OK**. A green check confirms the configured checks passed.

| Check | What GitHub verifies |
|---|---|
| ETL | The rejected IDs, duplicate count, and daily totals match the supplied example. Bad duplicate IDs or tariffs are caught. |
| Machine learning | Clean historical data flows into training, evaluation, and forecasting. The model beats the simple baseline on the exercise data and produces the expected forecast rows. |
| Notebook code | Python cells compile and contain the same shared logic as the tested modules. |

If a run fails, open the first failed step and read its error. A missing CSV usually means the file is absent or in the wrong folder. Commit and push the correction, then check the new run.

## 3. Make and test a change

Use **etl_core.py** or **ml_core.py** for shared logic edits. From the project root, regenerate the notebooks before committing. Run the local checks with Python 3.11.

```bash
python -m pip install -r requirements-ci.txt
python make_notebook.py
python -m unittest discover -s tests -v
```

The workflow runs on pushes and pull requests. After it exists on the default branch, you can also start it from **Actions → Mining energy ETL CI → Run workflow**.

References: [Upload an existing project with Git](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github?platform=windows)
