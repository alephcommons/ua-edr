
build: data/export/edr_uo.json

publish: data/export/edr_uo.json
	aws s3 sync --no-progress --cache-control "public, max-age=64600" --metadata-directive REPLACE --acl public-read data/export s3://data.opensanctions.org/contrib/ua_edr

data/export/edr_uo.json: data/sorted.json
	mkdir -p data/export
	ftm sorted-aggregate -i data/sorted.json -o data/export/edr_uo.json

data/sorted.json: data/fragments.json
	sort -S 2G -o data/sorted.json data/fragments.json

data/fragments.json:
	python parse.py
