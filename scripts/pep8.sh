. pyenv.sh

pip -q install pycodestyle

for DIR in *; do
  [[ ! -d "$DIR" ||  "$DIR" == "." || "$DIR" == ".." ]] && continue
  git check-ignore -q "$DIR" && continue
  find "$DIR" -name "*.py" -exec pycodestyle '{}' + || exit 1
done

