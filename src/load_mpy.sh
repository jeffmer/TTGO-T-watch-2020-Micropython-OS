echo "Loading mpy files" 
for i in ./*.mpy  clocks/*.mpy apps/*.mpy drivers/*.mpy utils/*.mpy fonts/*.mpy
do
mpremote u0 fs cp $i :$i
done
