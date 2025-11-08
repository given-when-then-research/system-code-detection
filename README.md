# system-code-detection

Tool for **system code detection and linking** with **BDD artifacts (Cucumber/Gherkin)**, producing the final dataset **`GivenWhenThen.json`**.

---

## Requirements

* Python 3.10+
* (Optional) Virtual environment (`venv`)

---

## Input & Output

* **Input:**
  `../dataset/consolidated_dataset.json` (update the path if the filename includes a timestamp, e.g. `consolidated_dataset_20251029_154345.json`)

* **Repositories base path:**
  `/home/luciano/Documentos/repositories`
  (edit in the Makefile if needed)

* **Output:**
  The final dataset `GivenWhenThen.json` (generated automatically after running the script)

---

## Run

This command uses the paths defined in the **Makefile**.
Before running, **edit the Makefile** to match your environment:

* Update `REPOSITORIES_BASE_PATH` with the **absolute path** to your local repositories.
* Update `DATASET_PATH` with the **actual name and location** of your consolidated dataset (for example, `consolidated_dataset_20251029_154345.json`).

After adjusting these values, simply run:

```bash
make run
```

The process will generate the final dataset **`GivenWhenThen.json`**.