#!/usr/bin/env bash
set -euxo pipefail

# Compile all py to mpy

CROSS="mpy-cross -march=xtensawin"
dir=$(dirname "$0")

for i in "$dir"/*.py "$dir"/clocks/*.py "$dir"/apps/*.py "$dir/"drivers/*.py "$dir"/utils/*.py "$dir"/fonts/*.py
do
  $CROSS "$i"
done

