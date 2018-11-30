.PHONY: build clean test_prepare install

build:
	cd taker_unixrun && $(MAKE) build

clean:
	cd tests && $(MAKE) clean
	cd taker_unixrun && $(MAKE) clean

test_prepare:
	cd tests && $(MAKE) build

install:
	cd taker_unixrun && $(MAKE) install
