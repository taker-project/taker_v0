. pyenv.sh

pip install autopep8

for DIR in *; do
  [[ ! -d "$DIR" ||  "$DIR" == "." || "$DIR" == ".." ]] && continue
  git check-ignore -q "$DIR" && continue
  autopep8 -ri "$DIR"
done
