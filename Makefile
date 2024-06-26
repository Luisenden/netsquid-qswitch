PYTHON3      = python3
SOURCEDIR    = netsquid_qswitch
TESTDIR      = tests
EXAMPLES     = examples
RUNEXAMPLES  = ${EXAMPLES}/run_examples.py
PIP_FLAGS    = --extra-index-url=https://${NETSQUIDPYPI_USER}:${NETSQUIDPYPI_PWD}@pypi.netsquid.org
MINCOV       = 70

help:
	@echo "install           Installs the package (editable)."
	@echo "verify            Verifies the installation, runs the linter and tests."
	@echo "tests             Runs the tests."
	@echo "examples          Runs the examples and makes sure they work."
	@echo "open-cov-report   Creates and opens the coverage report."
	@echo "lint              Runs the linter."
	@echo "deploy-bdist      Builds and uploads the package to the netsquid pypi server."
	@echo "bdist             Builds the package."
	@echo "test-deps         Installs the requirements needed for running tests and linter."
	@echo "python-deps       Installs the requirements needed for using the package."
	@echo "docs              Creates the html documentation"
	@echo "clean             Removes all .pyc files."

test-deps:
	@$(PYTHON3) -m pip install -r test_requirements.txt

requirements python-deps:
	@$(PYTHON3) -m pip install "pip>=19.0"
	@$(PYTHON3) -m pip install -r requirements.txt ${PIP_FLAGS}

clean:
	@/usr/bin/find . -name '*.pyc' -delete

lint:
	@$(PYTHON3) -m flake8 --max-line-length=120 ${SOURCEDIR} ${TESTDIR} ${EXAMPLES}

tests:
	@$(PYTHON3) -m pytest --cov=${SOURCEDIR} --cov-fail-under=${MINCOV} tests

open-cov-report:
	@$(PYTHON3) -m pytest --cov=${SOURCEDIR} --cov-report html tests && open htmlcov/index.html

examples:
	@${PYTHON3} ${RUNEXAMPLES} > /dev/null && echo "Examples OK!"

docs html:
	@${MAKE} -C docs html

bdist:
	@$(PYTHON3) setup.py bdist_wheel

install: python-deps test-deps
	@$(PYTHON3) -m pip install -e . ${PIP_FLAGS}

_clean_dist:
	@/bin/rm -rf dist

deploy-bdist: _clean_dist bdist
	@$(PYTHON3) setup.py deploy

verify: clean test-deps python-deps lint tests examples _verified

_verified:
	@echo "The snippet is verified :)"

.PHONY: clean lint test-deps python-deps tests verify bdist deploy-bdist _clean_dist install open-cov-report examples _check_variables docs
