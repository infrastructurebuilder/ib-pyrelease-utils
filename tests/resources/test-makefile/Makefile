# Fixture project driven by `make`.
#
# Exercises the build-tool contract release_perform depends on: a `clean`
# target and a `build` target. `build` records which tool ran so a test can
# tell this fixture apart from the Justfile one.

MARKER := build.marker

.PHONY: clean build

clean:
	rm -f $(MARKER)

build:
	echo "make" > $(MARKER)
