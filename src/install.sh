#!/usr/bin/env bash
#set -euxo pipefail

# install .mpy and .png files on target

echo "Making directories"
for i in apps drivers utils fonts images clocks
do
    mpremote a0 fs mkdir $i
done

mpremote a0 fs mkdir images/weather

echo "Loading mpy files"
for i in ./*.mpy  clocks/*.mpy apps/*.mpy drivers/*.mpy utils/*.mpy fonts/*.mpy
do
    # For V3, don't copy the apps that need GPS
    if [[ $(grep -Rl 'VERSION = 3' config.py) == "config.py" ]]
    then
        if [[ $i != "apps/position.mpy" ]] && [[ $i != "apps/maps.mpy" ]] && [[ $i != "./micropyGPS.mpy" ]] && [[ $i != "apps/openstreetmap.mpy" ]]
        then
            echo "COPYING $i"
            mpremote a0 fs cp "$i" :"$i"
        else
            echo "WILL NOT COPY $i"
        fi
    else
        mpremote a0 fs cp "$i" :"$i"
    fi
done

echo "Loading image files"
for i in images/*.png images/weather/*.png
do
    mpremote a0 fs cp "$i" :"$i"
done

echo "Write Location file"
mpremote a0 fs cp location.json :location.json

echo "Write Boot file"
mpremote a0 fs rm :boot.mpy
mpremote a0 fs rm :boot.py
echo "deleted"
mpremote a0 fs cp boot.mpy :boot.mpy
mpremote a0 fs cp boot.py :boot.py
echo "copied"

echo "Reset"
mpremote a0 soft-reset

exit 0
