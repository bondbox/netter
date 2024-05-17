MAKEFLAGS += --always-make

all: build install test
clean: build-clean test-clean


build: build-clean
	xpip-build --debug setup --all
build-clean:
	xpip-build --debug setup --clean


upload:
	xpip-upload --config-file .pypirc dist/*


install:
	pip3 install --force-reinstall --no-deps dist/*.whl
uninstall:
	pip3 uninstall -y netter
reinstall: uninstall install


pylint:
	pylint $$(git ls-files netter/*.py test/*.py example/*.py)

flake8:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

pytest:
	pytest
pytest-clean:
	rm -rf .pytest_cache

prepare-test:
	pip3 install --upgrade pylint flake8 pytest
test: prepare-test pylint flake8 pytest
test-clean: pytest-clean


query-public-ip:
	echo "$$(date '+%F %T') public ip $$(netter public-ip --all --verbose --debug --log log/netter.log)" >> log/public-ip.log
