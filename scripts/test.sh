#!/bin/sh

. ./pyenv.sh

if pytest --help | grep -- --codestyle >/dev/null; then
  PYCODESTYLE_OPTION=--codestyle
else
  PYCODESTYLE_OPTION=--pep8
fi

COV_OPTIONS=""

if [ -n "${COVERAGE}" ]; then
  for DIR in src/*; do
    [ -d "$DIR" ] || continue
    [ -f "$DIR/__init__.py" ] || continue
    git check-ignore -q "$DIR" && continue
    COV_OPTIONS="${COV_OPTIONS} --cov=$(echo "$DIR" | sed 's#^src/##')"
  done
fi

# shellcheck disable=SC2086
pytest "${PYCODESTYLE_OPTION}" ${COV_OPTIONS} src/*/
