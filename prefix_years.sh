#!/bin/bash
for year in 2000 2001 2002; do
  for f in HRW/$year/*; do
    filename=$(basename "$f")
    mv "$f" "HRW/$year/${year}_${filename}"
  done
done
