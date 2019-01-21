. pyenv.sh

pip -q install autopep8

for DIR in src/*; do
  [[ -d "$DIR" ]] || continue
  git check-ignore -q "$DIR" && continue
  autopep8 -ri "$DIR"
done
