#!/bin/sh

. ./pyenv.sh

pip -q install pylint

OK=0

for DIR in src/*; do
  [ -d "$DIR" ] || continue
  git check-ignore -q "$DIR" && continue
  pylint "$DIR" --ignore-patterns="test_.*" -d C0111 -d W0511 || OK=1
  [ -d "$DIR/tests" ] || continue
  ( cd src && pylint "../$DIR/tests" -d C0111 -d W0511 -d W0614 -d W0621 ) || OK=1
done

exit "$OK"
