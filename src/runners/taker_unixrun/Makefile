.PHONY: install build clean prebuild

build: prebuild
	cd build && cmake ..
	cd build && $(MAKE)

prebuild:
	mkdir -p build/

clean:
	rm -rf build

install: prebuild
	cd build && cmake .. -DCMAKE_INSTALL_PREFIX="$(PREFIX)"
	cd build && $(MAKE)
	cd build && $(MAKE) install
