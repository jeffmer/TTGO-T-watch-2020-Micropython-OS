#!/usr/bin/env bash
#set -euxo pipefail

echo "Copying root files"
mpremote u0 fs cp bma_config.mpy :bma_config.mpy
mpremote u0 fs cp button.mpy :button.mpy
mpremote u0 fs cp config.mpy :config.mpy
mpremote u0 fs cp graphics.mpy :graphics.mpy
mpremote u0 fs cp itertools.mpy :itertools.mpy
mpremote u0 fs cp loader.mpy :loader.mpy
mpremote u0 fs cp png.mpy :png.mpy
mpremote u0 fs cp scheduler.mpy :scheduler.mpy
mpremote u0 fs cp tempos.mpy :tempos.mpy
mpremote u0 fs cp widgets.mpy :widgets.mpy
mpremote u0 fs cp wifi.mpy :wifi.mpy

echo "Copying clocks files"
mpremote u0 fs mkdir clocks
mpremote u0 fs cp clocks/braunclock.mpy :clocks/braunclock.mpy
mpremote u0 fs cp clocks/dialclock.mpy :clocks/dialclock.mpy
mpremote u0 fs cp clocks/digiclock.mpy :clocks/digiclock.mpy
mpremote u0 fs cp clocks/niftyclock.mpy :clocks/niftyclock.mpy
mpremote u0 fs cp clocks/numclock.mpy :clocks/numclock.mpy
mpremote u0 fs cp clocks/stepsdisp.mpy :clocks/stepsdisp.mpy

echo "Copying apps files"
mpremote u0 fs mkdir apps
mpremote u0 fs cp apps/calculator.mpy :apps/calculator.mpy
mpremote u0 fs cp apps/puzzle.mpy :apps/puzzle.mpy
mpremote u0 fs cp apps/weather.mpy :apps/weather.mpy

echo "Copying drivers files"
mpremote u0 fs mkdir drivers
mpremote u0 fs cp drivers/axp202.mpy :drivers/axp202.mpy
mpremote u0 fs cp drivers/bma423.mpy :drivers/bma423.mpy
mpremote u0 fs cp drivers/drv2605.mpy :drivers/drv2605.mpy
mpremote u0 fs cp drivers/ft6236.mpy :drivers/ft6236.mpy
mpremote u0 fs cp drivers/l67k.mpy :drivers/l67k.mpy
mpremote u0 fs cp drivers/pcf8563.mpy :drivers/pcf8563.mpy
mpremote u0 fs cp drivers/st7789.mpy :drivers/st7789.mpy


echo "Copying utils files"
mpremote u0 fs mkdir utils
mpremote u0 fs cp utils/alarm.mpy :utils/alarm.mpy
mpremote u0 fs cp utils/batdisp.mpy :utils/batdisp.mpy
mpremote u0 fs cp utils/buzzcon.mpy :utils/buzzcon.mpy
mpremote u0 fs cp utils/display.mpy :utils/display.mpy
mpremote u0 fs cp utils/timeman.mpy :utils/timeman.mpy
mpremote u0 fs cp utils/torch.mpy :utils/torch.mpy

echo "Copying fonts files"
mpremote u0 fs mkdir fonts
mpremote u0 fs cp fonts/bignumfont.mpy :fonts/bignumfont.mpy
mpremote u0 fs cp fonts/glcdfont.mpy :fonts/glcdfont.mpy
mpremote u0 fs cp fonts/hugefont.mpy :fonts/hugefont.mpy
mpremote u0 fs cp fonts/roboto18.mpy :fonts/roboto18.mpy
mpremote u0 fs cp fonts/roboto24.mpy :fonts/roboto24.mpy
mpremote u0 fs cp fonts/roboto36.mpy :fonts/roboto36.mpy

echo "Copying weather image files"
mpremote u0 fs mkdir images
mpremote u0 fs mkdir images/weather
for i in images/*.png images/weather/*.png
do
    mpremote u0 fs cp "$i" :"$i"
done

if [[ ! $(grep -Rl 'VERSION = 3' config.py) == "config.py" ]]
then
    echo "Copying files related to GPS"
    mpremote u0 fs cp micropyGPS.mpy :micropyGPS.mpy
    mpremote u0 fs cp apps/maps.mpy :apps/maps.mpy
    mpremote u0 fs cp apps/openstreetmap.mpy :apps/openstreetmap.mpy
    mpremote u0 fs cp apps/position.mpy :apps/position.mpy
    mpremote u0 fs cp pngtile.mpy :pngtile.mpy
fi

echo "Write Location file"
mpremote u0 fs cp location.json :location.json

echo "Write Boot file"
mpremote u0 fs rm :boot.mpy
mpremote u0 fs rm :boot.py
mpremote u0 fs cp boot.mpy :boot.mpy
mpremote u0 fs cp boot.py :boot.py

echo "Resetting watch"
mpremote u0 soft-reset

exit 0
