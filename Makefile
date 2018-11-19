.PHONY: help venv build clean venv_install test

help:
	@echo Usage:
	@echo
	@echo help - show this help
	@echo clean - purge the directory
	@echo venv - rebuild venv
	@echo build - build the egg
	@echo venv_install - install into venv
	@echo test - run tests

.PHONY: make_targets

make_targets:
	mkdir -p .make_targets

venv: .make_targets/venv
.make_targets/venv: make_targets
	rm -rf venv/
	python3 -m venv venv

build: venv
	bash -c '. pyenv.sh && python setup.py build'

clean:
	rm -rf venv/ build/ dist/
	rm -rf *.egg-info/

venv_install: venv
	bash -c '. pyenv.sh && python setup.py install'

test: venv_install
	bash -c '. pyenv.sh && pytest'
