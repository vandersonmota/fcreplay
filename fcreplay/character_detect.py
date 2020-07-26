import cv2
import numpy as np
import datetime
import sys
import pkg_resources
import json
import logging

with open("config.json", "r") as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)


def process_img(frame_rgb, character_images, count):
    # We only need a frame ever second
    if not count % 120 == 0:
        return

    # We only care about the areas with character names
    x_len = frame_rgb.shape[1]
    cropped_frame = frame_rgb[35:60, 0:x_len, :]

    # Convert to grayscale
    frame_gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

    p1_character_score = {}
    p2_character_score = {}
    for character in character_images:
        for image in character_images[character]['images']:
            w, h = image.shape[::-1]
            character_images[character]['w'] = w
            character_images[character]['h'] = h

            res = cv2.matchTemplate(frame_gray, image, cv2.TM_CCOEFF_NORMED)
            threshold = 0.85
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                if pt[0] < 200:
                    if character not in p1_character_score:
                        p1_character_score[character] = 1
                    else:
                        p1_character_score[character] += 1
                else:
                    if character not in p2_character_score:
                        p2_character_score[character] = 1
                    else:
                        p2_character_score[character] += 1
    if p1_character_score and p2_character_score:
        return [max(p1_character_score), max(p2_character_score)]
    else:
        return False, False


def character_detect(videofile):
    """Detects characters

    Args:
        videofile (String): Path to video

    Returns:
        List: [[p1,p2,time][p1,p2,time]...]
    """
    vidcap = cv2.VideoCapture(videofile)
    characters = [
        "alex",
        "akuma",
        "chunli",
        "dudley",
        "elena",
        "hugo",
        "ibuki",
        "ken",
        "makoto",
        "necro",
        "oro",
        "q",
        "remy",
        "ryu",
        "sean",
        "twelve",
        "urien",
        "yang",
        "yun"
    ]

    # Load all character images
    character_images = {}
    charnames_dir = pkg_resources.resource_filename('fcreplay', 'data/charnames')
    for character in characters:
        for i in range(1, 10):
            if character not in character_images:
                character_images[character] = {'images': []}
            character_images[character]['images'].append(cv2.imread(f'{charnames_dir}/{character}{i}.png', 0))
    count = 0

    # [ p1, p2, start-time ]
    times = []

    while True:
        success, image = vidcap.read()
        if not success:
            break         # loop and a half construct is useful
        count += 1
        match = process_img(image, character_images, count)
        if match is not None:
            p1 = match[0]
            p2 = match[1]
            if p1 is not False and p2 is not False:
                if len(times) == 0:
                    times.append([p1, p2, str(datetime.timedelta(seconds=int(count / 60)))])
                elif p1 not in times[-1][0] or p2 not in times[-1][1]:
                    times.append([p1, p2, str(datetime.timedelta(seconds=int(count/60)))])

    logging.debug(f'Video: {videofile}')
    video_chars = []
    for i in times:
        logging.info(f'P1: {i[0]}, P2: {i[1]}, Time: {i[2]}')
        video_chars.append([i[0], i[1], i[2]])
    return video_chars


if __name__ == "__main__":
    character_detect(sys.argv[1])