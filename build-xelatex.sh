#!/bin/zsh

cd "/Users/admin/code/Thesis_MT" || exit 1

/Library/TeX/texbin/xelatex \
  -synctex=1 \
  -interaction=nonstopmode \
  -halt-on-error \
  -file-line-error \
  main.tex

status=$?

if [ "$status" -ne 0 ]; then
    rm -f main.aux main.out
    echo "Build failed. Removed corrupted auxiliary files."
fi

exit "$status"
