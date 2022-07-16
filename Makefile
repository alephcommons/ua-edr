
build: data/export/edr.json

data/export/edr.json: data/sorted.json
	mkdir -p data/export
	ftm sorted-aggregate -i data/sorted.json -o data/export/edr.json

data/sorted.json: data/fragments.json
	sort -S 2G -o data/sorted.json data/fragments.json

data/fragments.json:
	python parse.py
