
# install .mpy and .png files on target

echo "Making directories" 
for i in apps drivers utils fonts images clocks
do
mpremote u0 fs mkdir $i
done

mpremote u0 fs mkdir images/weather

echo "Loading mpy files" 
for i in ./*.mpy  clocks/*.mpy apps/*.mpy drivers/*.mpy utils/*.mpy fonts/*.mpy
do
mpremote u0 fs cp $i :$i
done

echo "Loading image files" 
for i in images/*.png images/weather/*.png
do
mpremote u0 fs cp $i :$i
done

echo "Write Boot file" 
mpremote u0 fs rm :boot.mpy
mpremote u0 fs cp boot.py :boot.py

echo "Write Location file" 
mpremote u0 fs cp location.json :location.json

echo "Reset"
mpremote u0 soft-reset
