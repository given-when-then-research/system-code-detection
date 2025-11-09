PYTHON       := python3
SCRIPT       := src/main.py
REPOSITORIES_BASE_PATH    := /home/luciano/Documentos/Github/given-when-then-research/repositories
DATASET_PATH := ../dataset/consolidated_dataset.json

.PHONY: run
run:
	$(PYTHON) -B $(SCRIPT) --base $(REPOSITORIES_BASE_PATH) --dataset $(DATASET_PATH)


.PHONY: clean
clean:
	rm -rf __pycache__ logs
	echo "🧹 Cleaned temporary files!"
