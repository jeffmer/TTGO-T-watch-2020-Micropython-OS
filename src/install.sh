#!/usr/bin/env bash
#set -euxo pipefail

echo "Copying root files"
mpremote a0 fs cp bma_config.mpy :bma_config.mpy
mpremote a0 fs cp button.mpy :button.mpy
mpremote a0 fs cp config.mpy :config.mpy
mpremote a0 fs cp graphics.mpy :graphics.mpy
mpremote a0 fs cp itertools.mpy :itertools.mpy
mpremote a0 fs cp loader.mpy :loader.mpy
mpremote a0 fs cp png.mpy :png.mpy
mpremote a0 fs cp scheduler.mpy :scheduler.mpy
mpremote a0 fs cp tempos.mpy :tempos.mpy
mpremote a0 fs cp widgets.mpy :widgets.mpy
mpremote a0 fs cp wifi.mpy :wifi.mpy

echo "Copying clocks files"
mpremote a0 fs mkdir clocks
mpremote a0 fs cp clocks/braunclock.mpy :clocks/braunclock.mpy
mpremote a0 fs cp clocks/dialclock.mpy :clocks/dialclock.mpy
mpremote a0 fs cp clocks/digiclock.mpy :clocks/digiclock.mpy
mpremote a0 fs cp clocks/niftyclock.mpy :clocks/niftyclock.mpy
mpremote a0 fs cp clocks/numclock.mpy :clocks/numclock.mpy
mpremote a0 fs cp clocks/stepsdisp.mpy :clocks/stepsdisp.mpy

echo "Copying apps files"
mpremote a0 fs mkdir apps
mpremote a0 fs cp apps/calculator.mpy :apps/calculator.mpy
mpremote a0 fs cp apps/puzzle.mpy :apps/puzzle.mpy
mpremote a0 fs cp apps/weather.mpy :apps/weather.mpy

echo "Copying drivers files"
mpremote a0 fs mkdir drivers
mpremote a0 fs cp drivers/axp202.mpy :drivers/axp202.mpy
mpremote a0 fs cp drivers/bma423.mpy :drivers/bma423.mpy
mpremote a0 fs cp drivers/drv2605.mpy :drivers/drv2605.mpy
mpremote a0 fs cp drivers/ft6236.mpy :drivers/ft6236.mpy
mpremote a0 fs cp drivers/l67k.mpy :drivers/l67k.mpy
mpremote a0 fs cp drivers/pcf8563.mpy :drivers/pcf8563.mpy
mpremote a0 fs cp drivers/st7789.mpy :drivers/st7789.mpy


echo "Copying utils files"
mpremote a0 fs mkdir utils
mpremote a0 fs cp utils/alarm.mpy :utils/alarm.mpy
mpremote a0 fs cp utils/batdisp.mpy :utils/batdisp.mpy
mpremote a0 fs cp utils/buzzcon.mpy :utils/buzzcon.mpy
mpremote a0 fs cp utils/display.mpy :utils/display.mpy
mpremote a0 fs cp utils/timeman.mpy :utils/timeman.mpy
mpremote a0 fs cp utils/torch.mpy :utils/torch.mpy

echo "Copying fonts files"
mpremote a0 fs mkdir fonts
mpremote a0 fs cp fonts/bignumfont.mpy :fonts/bignumfont.mpy
mpremote a0 fs cp fonts/glcdfont.mpy :fonts/glcdfont.mpy
mpremote a0 fs cp fonts/hugefont.mpy :fonts/hugefont.mpy
mpremote a0 fs cp fonts/roboto18.mpy :fonts/roboto18.mpy
mpremote a0 fs cp fonts/roboto24.mpy :fonts/roboto24.mpy
mpremote a0 fs cp fonts/roboto36.mpy :fonts/roboto36.mpy

echo "Copying weather image files"
mpremote a0 fs mkdir images
mpremote a0 fs mkdir images/weather
for i in images/*.png images/weather/*.png
do
    mpremote a0 fs cp "$i" :"$i"
done

if [[ ! $(grep -Rl 'VERSION = 3' config.py) == "config.py" ]]
then
    echo "Copying files related to GPS"
    mpremote a0 fs cp micropyGPS.mpy :micropyGPS.mpy
    mpremote a0 fs cp apps/maps.mpy :apps/maps.mpy
    mpremote a0 fs cp apps/openstreetmap.mpy :apps/openstreetmap.mpy
    mpremote a0 fs cp apps/position.mpy :apps/position.mpy
    mpremote a0 fs cp pngtile.mpy :pngtile.mpy
fi

echo "Write Location file"
mpremote a0 fs cp location.json :location.json

echo "Write Boot file"
mpremote a0 fs rm :boot.mpy
mpremote a0 fs rm :boot.py
mpremote a0 fs cp boot.mpy :boot.mpy
mpremote a0 fs cp boot.py :boot.py

echo "Resetting watch"
mpremote a0 soft-reset

exit 0
