.PHONY: help venv build build_runners clean clean_runners test_prepare test autopep8 pep8

help:
	@echo Usage:
	@echo
	@echo help - show this help
	@echo clean - purge the directory
	@echo venv - rebuild venv
	@echo build - build and install into venv
	@echo test - run tests
	@echo autopep8 - apply autopep8 to the code
	@echo pep8 - run code style analysis

.make_targets/.dir:
	mkdir -p .make_targets
	touch .make_targets/.dir

venv: .make_targets/venv
.make_targets/venv: .make_targets/.dir
	rm -rf venv/
	python3 -m venv venv
	touch .make_targets/venv
	bash -c '. pyenv.sh && pip install -U pip setuptools \
		&& pip install pytest'

clean_runners:
	cd runners && $(MAKE) clean

build_runners: venv
	cd runners && $(MAKE) PREFIX="$$(pwd)/../venv" install

clean: clean_runners
	rm -rf venv/ build/ dist/ .pytest_cache/
	rm -rf *.egg-info/
	rm -rf .make_targets

build: venv build_runners
	cd runners && $(MAKE) build
	bash -c '. pyenv.sh && python setup.py install'

test_prepare:
	cd runners && $(MAKE) test_prepare

test: venv build test_prepare
	bash -c '. pyenv.sh && pytest'

autopep8: venv
	bash -c 'scripts/autopep8.sh'

pep8: venv
	bash -c 'scripts/pep8.sh'
