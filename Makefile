.PHONY: help venv build clean test autopep8

help:
	@echo Usage:
	@echo
	@echo help - show this help
	@echo clean - purge the directory
	@echo venv - rebuild venv
	@echo build - build and install into venv
	@echo test - run tests
	@echo autopep8 - apply autopep8 to the code

.make_targets/.dir:
	mkdir -p .make_targets
	touch .make_targets/.dir

venv: .make_targets/venv
.make_targets/venv: .make_targets/.dir
	rm -rf venv/
	python3 -m venv venv
	touch .make_targets/venv
	bash -c '. pyenv.sh && pip install -U pip'

clean:
	rm -rf venv/ build/ dist/
	rm -rf *.egg-info/
	rm -rf .make_targets

build: venv
	bash -c '. pyenv.sh && python setup.py install'

test: venv build
	bash -c '. pyenv.sh && pytest'

autopep8: venv
	scripts/autopep8.sh
