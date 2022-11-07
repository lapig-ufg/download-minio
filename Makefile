.PHONY: install run pinstall pformat plint ptest psec

install:
	pip3 install poetry 
	poetry install
pformat:
	@poetry run isort .
	@poetry run blue .
plint:
	@poetry run blue . --check
	@poetry run isort . --check
	@poetry run prospector --with-tool pep257 --doc-warning
ptest:
	@poetry run pytest -v
run:
	sh start.sh
psec:
	@poetry run pip-audit