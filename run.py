#!/usr/bin/env python3
# A simple Python manager for "Turing Smart Screen" 3.5" IPS USB-C display
# https://github.com/mathoudebine/turing-smart-screen-python

import os
import signal
import sys
from datetime import datetime, timedelta
import time
import json
import requests
import bs4
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
# Import only the modules for LCD communication
from library.lcd_comm_rev_a import LcdCommRevA, Orientation
from library.lcd_comm_rev_b import LcdCommRevB
from library.lcd_simulated import LcdSimulated
from library.log import logger

# Set your COM port e.g. COM3 for Windows, /dev/ttyACM0 for Linux, etc. or "AUTO" for auto-discovery
# COM_PORT = "/dev/ttyACM0"
# COM_PORT = "COM5"
COM_PORT = "AUTO"

# Display revision: A or B (for "flagship" version, use B) or SIMU for simulated LCD (image written in screencap.png)
# To identify your revision: https://github.com/mathoudebine/turing-smart-screen-python/wiki/Hardware-revisions
REVISION = "A"


def main():

    background = 'example_landscape.png'
    username = 'Fast0n'.replace(' ', '%20')
    custom_font = 'res/fonts/burbankSmall-black/BurbankSmall-Black.otf'

    def get_json():
        url_original = f"https://fortnite.gg/stats?player={username}"
        response = requests.get(url_original)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")
        script = scripts[-3].text

        value = (script.split(';')[2].split('=')[1])
        season = (script.split(';')[1])
        season = season.replace('Season=', '')
        stats = json.loads(value)

        return(season, stats)

    season, stats = get_json()
    url = f"https://fortnite.gg/img/stats/bg-{season}.jpg"

    r = requests.get(url, stream=True)

    with open(background, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    def make_bg(color, colorA):

        time_played = int(stats['minutes'])
        hours = time_played // 60
        minutes = time_played % 60
        time_played = f'{str(hours)}H {str(minutes)}M'

        avg = int(stats['minutes'])/int(stats['matches'])
        minute = timedelta(minutes=avg)
        minute = str(minute)
        avg = f'{minute.split(":")[1]}H {str(int(float(minute.split(":")[2])))}M'

        background_image = Image.open(background, "r")

        draw = ImageDraw.Draw(background_image)
        font_name = ImageFont.truetype(str(custom_font), 110)
        font_username = ImageFont.truetype(str(custom_font), 60)

        # title and level
        draw.text((800, 55), 'Last update: ', colorA, font=font_username)
        draw.text(
            (100, 160), stats['name'], color, font=font_name)
        draw.text((300, 312), str(
            stats['level']), colorA, font=font_username)

        # first row
        draw.text((270, 540), str(stats['wins']),
                  fill=(colorA), anchor="md", font=font_username)

        win_rate = str(
            int(int(stats['wins'])/int(stats['matches'])*100))+'%'
        draw.text((635, 540), win_rate,
                  fill=(colorA), anchor="md", font=font_username)

        draw.text((1000, 540), str(stats['matches']),
                  fill=(colorA), anchor="md", font=font_username)

        # second row
        kill_dead = str(round(int(stats['kills'])/int(stats['deaths']), 2))
        draw.text((270, 750), kill_dead,
                  fill=(colorA), anchor="md", font=font_username)

        kill_match = str(
            round(int(stats['kills'])/int(stats['matches']), 2))
        draw.text((635, 750), kill_match,
                  fill=(colorA), anchor="md", font=font_username)

        draw.text((1000, 750), str(stats['kills']),
                  fill=(colorA), anchor="md", font=font_username)

        # final row

        draw.text((360, 970), time_played,
                  fill=(colorA), anchor="md", font=font_username)

        draw.text((900, 970), avg,
                  fill=(colorA), anchor="md", font=font_username)

        background.save(background)
        im2 = Image.open('button.png')
        back_im = background_image.copy()
        back_im.paste(im2, (1215, 980))
        back_im.save(background)

        img = Image.open(background)  # image extension *.png,*.jpg
        new_width = 569
        new_height = 320
        img = img.resize((new_width, new_height),
                         Image.Resampling.LANCZOS)
        im1 = img.crop((0, 0, 480, 320))
        im1.save(background, quality=100)

    make_bg("white", (255, 255, 255))

    # Display sample picture
    lcd_comm.DisplayBitmap(background)

    times = str(datetime.now().time()).split(':')
    lcd_comm.DisplayText(f'{times[0]}:{times[1]}', 350, 15,
                         font="burbankSmall-black/BurbankSmall-Black.otf",
                         font_size=18,
                         font_color=(255, 255, 255),
                         background_image=background)

    time.sleep(60 * 5)  # wait 2 hours


stop = False
if __name__ == "__main__":

    def sighandler(signum, frame):
        global stop
        stop = True

    # Set the signal handlers, to send a complete frame to the LCD before exit
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)
    is_posix = os.name == 'posix'
    if is_posix:
        signal.signal(signal.SIGQUIT, sighandler)

    # Build your LcdComm object based on the HW revision
    lcd_comm = None
    if REVISION == "A":
        logger.info("Selected Hardware Revision A (Turing Smart Screen)")
        lcd_comm = LcdCommRevA(com_port="AUTO",
                               display_width=320,
                               display_height=480)
    elif REVISION == "B":
        print("Selected Hardware Revision B (XuanFang screen version B / flagship)")
        lcd_comm = LcdCommRevB(com_port="AUTO",
                               display_width=320,
                               display_height=480)
    elif REVISION == "SIMU":
        print("Selected Simulated LCD")
        lcd_comm = LcdSimulated(display_width=320,
                                display_height=480)
    else:
        print("ERROR: Unknown revision")
        try:
            sys.exit(0)
        except:
            os._exit(0)

    # Reset screen in case it was in an unstable state (screen is also cleared)
    # lcd_comm.Reset()

    # Send initialization commands
    # lcd_comm.InitializeComm()

    # Set brightness in % (warning: screen can get very hot at high brightness!)
    lcd_comm.SetBrightness(level=25)

    # Set orientation (screen starts in Portrait)
    orientation = Orientation.REVERSE_LANDSCAPE
    lcd_comm.SetOrientation(orientation=orientation)

    while not stop:
        main()

    # Close serial connection at exit
    lcd_comm.closeSerial()
