#!/usr/bin/env python3
# A simple Python manager for "Turing Smart Screen" 3.5" IPS USB-C display
# https://github.com/mathoudebine/turing-smart-screen-python

import json
import os
import signal
import sys
import time
from datetime import date, datetime, timedelta

import bs4
import requests
# Import only the modules for LCD communication
from library.lcd_comm_rev_a import LcdCommRevA, Orientation
from library.lcd_comm_rev_b import LcdCommRevB
from library.lcd_simulated import LcdSimulated
from library.log import logger
from PIL import Image, ImageDraw, ImageFont

# Set your COM port e.g. COM3 for Windows, /dev/ttyACM0 for Linux, etc. or "AUTO" for auto-discovery
# COM_PORT = "/dev/ttyACM0"
# COM_PORT = "COM5"
COM_PORT = "AUTO"

# Display revision: A or B (for "flagship" version, use B) or SIMU for simulated LCD (image written in screencap.png)
# To identify your revision: https://github.com/mathoudebine/turing-smart-screen-python/wiki/Hardware-revisions
REVISION = "A"


def main():
    icon_id = 'CID_843_Athena_Commando_M_HightowerTomato_Casual'
    background = 'res/backgrounds/example_landscape.png'
    button = 'res/backgrounds/button.png'
    username = 'Fast0n'.replace(' ', '%20')
    custom_font = 'res/fonts/burbankSmall-black/BurbankSmall-Black.ttf'
    custom_font_italic = 'res/fonts/burbankSmall-black/BurbankSmall-BlackItalic.ttf'

    '''







    '''

    # default value
    season = 20
    stats = json.loads(
        '{ "minutes":"999", "matches":"999", "name":"'+username+'", "level":"999","wins":"999","kills":"999","deaths":"1"     }')

    def get_season():
        response = requests.get("https://fortnite.gg/season-countdown")
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        h1 = soup.find("div", {"class": "season-countdown"}).h1.text
        date_finish = str(datetime.fromtimestamp(int(soup.find("div", {
            "class": "season-countdown"}).div.attrs["data-target"][:-3]))).split(' ')[0]

        now = str(date.today())

        # convert string to date object
        d1 = datetime.strptime(now, "%Y-%m-%d")
        d2 = datetime.strptime(date_finish, "%Y-%m-%d")

        delta = (d2 + timedelta(days=1)) - d1
        date_finish = str(delta.days)

        new_season = f"UNTIL C{h1.split(' ')[4]} S{int(h1.split(' ')[6])+1}"

        return new_season, date_finish

    def get_json_stats():
        url_original = f"https://fortnite.gg/stats?player={username}"
        response = requests.get(url_original)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")
        script = scripts[-3].text

        value = (script.split(';')[2].split('=')[1])
        season = (script.split(';')[1])
        season = season.replace('Season=', '')
        stats = json.loads(value)

        return season, stats

    try:
        season, stats = get_json_stats()
    except:
        pass

    season_name, date_finish = get_season()
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

        try:
            avg = int(stats['minutes'])/int(stats['matches'])
        except ZeroDivisionError:
            avg = 0
        minute = timedelta(minutes=avg)
        minute = str(minute)
        avg = f'{minute.split(":")[1]}H {str(int(float(minute.split(":")[2])))}M'

        background_image = Image.open(background, "r")

        draw = ImageDraw.Draw(background_image)
        font_name = ImageFont.truetype(str(custom_font_italic), 110)
        font_days = ImageFont.truetype(str(custom_font), 80)
        font_days_title = ImageFont.truetype(str(custom_font), 50)
        font_username = ImageFont.truetype(str(custom_font), 60)
        font_username_italic = ImageFont.truetype(str(custom_font_italic), 55)

        # title and level
        draw.text((780, 59), 'Last update: '.upper(),
                  colorA, font=font_username_italic)

        draw.text((1240, 770), 'THERE’S ONLY',
                  colorA, font=font_days_title)

        draw.text((1250, 835), f'     DAYS', colorA, font=font_days)
        draw.text((1260, 920), season_name,
                  colorA, font=font_days_title)

        draw.text(
            (100, 160), stats['name'].capitalize(), color, font=font_name)
        draw.text((300, 300), str(stats['level']), colorA, font=font_username)

        # first row
        draw.text((270, 540), str(stats['wins']),
                  fill=(colorA), anchor="md", font=font_username)
        try:
            win_rate = str(
                int(int(stats['wins'])/int(stats['matches'])*100))+'%'
        except ZeroDivisionError:
            win_rate = '0%'
        draw.text((635, 540), win_rate,
                  fill=(colorA), anchor="md", font=font_username)

        draw.text((1000, 540), str(stats['matches']),
                  fill=(colorA), anchor="md", font=font_username)

        # second row
        try:
            kill_dead = str(round(int(stats['kills'])/int(stats['deaths']), 2))
        except ZeroDivisionError:
            kill_dead = '0'
        draw.text((270, 750), kill_dead,
                  fill=(colorA), anchor="md", font=font_username)

        try:
            kill_match = str(
                round(int(stats['kills'])/int(stats['matches']), 2))
        except ZeroDivisionError:
            kill_match = '0'
        draw.text((635, 750), kill_match,
                  fill=(colorA), anchor="md", font=font_username)

        draw.text((1000, 750), str(stats['kills']),
                  fill=(colorA), anchor="md", font=font_username)

        # final row

        draw.text((360, 970), time_played,
                  fill=(colorA), anchor="md", font=font_username)

        draw.text((900, 970), avg,
                  fill=(colorA), anchor="md", font=font_username)

        background_image.save(background)
        im2 = Image.open(button)
        back_im = background_image.copy()
        back_im.paste(im2, (1215, 980))
        back_im.save(background)

        img = Image.open(requests.get(
            f'https://fortnite-api.com/images/cosmetics/br/{icon_id}/icon.png', stream=True).raw)

        img = img.resize((img.width // 2, img.height // 2))

        background_image.paste(img, (1280, 480),  img.convert('RGBA'))
        im2 = Image.open(button)
        background_image.paste(im2, (1215, 980))
        background_image.save(background)

        img = Image.open(background)  # image extension *.png,*.jpg
        new_width = 569
        new_height = 320
        img = img.resize((new_width, new_height),
                         Image.Resampling.LANCZOS)
        im1 = img.crop((0, 0, 480, 320))
        im1.save(background, quality=100)

    make_bg("white", (255, 255, 255))
    '''







    '''
    # Display sample picture
    lcd_comm.DisplayBitmap(background)

    times = str(datetime.now().time()).split(':')
    lcd_comm.DisplayText(f'{times[0]}:{times[1]}', 345, 18,
                         font="burbankSmall-black/BurbankSmall-BlackItalic.ttf",
                         font_size=16,
                         font_color=(255, 255, 255),
                         background_image=background)

    lcd_comm.DisplayText(f'{date_finish}', 368, 247,
                         font="burbankSmall-black/BurbankSmall-Black.ttf",
                         font_size=24,
                         font_color=(255, 255, 255),
                         background_image=background)

    time.sleep(60 * 5)  # wait 5 minute


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
    mytime = time.localtime()
    if mytime.tm_hour < 6 or mytime.tm_hour > 18:
        lcd_comm.SetBrightness(level=5)
    else:
        lcd_comm.SetBrightness(level=25)

    # Set orientation (screen starts in Portrait)
    orientation = Orientation.REVERSE_LANDSCAPE
    lcd_comm.SetOrientation(orientation=orientation)

    while not stop:
        main()

    # Close
