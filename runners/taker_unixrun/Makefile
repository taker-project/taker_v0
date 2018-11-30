.PHONY: install build clean prebuild

prebuild:
	mkdir -p build/

build: prebuild
	cd build && cmake ..
	cd build && $(MAKE)

clean:
	rm -rf build

install: prebuild
	cd build && cmake .. -DCMAKE_INSTALL_PREFIX="$(PREFIX)"
	cd build && $(MAKE)
	cd build && $(MAKE) install
