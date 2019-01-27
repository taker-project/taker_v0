. pyenv.sh

if pytest --help | grep -- --codestyle >/dev/null; then
  PYCODESTYLE_OPTION=--codestyle
else
  PYCODESTYLE_OPTION=--pep8
fi

pytest "${PYCODESTYLE_OPTION}"
