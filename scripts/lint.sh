. pyenv.sh

pip -q install pycodestyle

OK=0

for DIR in *; do
  [[ ! -d "$DIR" ||  "$DIR" == "." || "$DIR" == ".." ]] && continue
  git check-ignore -q "$DIR" && continue
  pylint "$DIR" -d C0111 -d W0511 || OK=1
  [[ -d "$DIR/tests" ]] || continue
  pylint "$DIR/tests" -d C0111 -d W0511 -d W0614 -d W0621 || OK=1
done

exit "$OK"
