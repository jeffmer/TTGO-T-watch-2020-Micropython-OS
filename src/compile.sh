# Compile all py to mpy

CROSS="/home/jeff/pico/micropython/mpy-cross/build/mpy-cross -march=xtensawin"
dir=`pwd`

for i in $dir/*.py $dir/clocks/*.py $dir/apps/*.py $dir/drivers/*.py $dir/utils/*.py $dir/fonts/*.py 
do
$CROSS $i
done


