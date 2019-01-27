#!/bin/sh

. ./pyenv.sh

pip -q install pycodestyle

for DIR in src/*; do
  [ -d "$DIR" ] || continue
  git check-ignore -q "$DIR" && continue
  find "$DIR" -name "*.py" -exec pycodestyle '{}' + || exit 1
done

