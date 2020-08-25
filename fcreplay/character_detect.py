import cv2
import numpy as np
import datetime
import sys
import pkg_resources
import json
import logging

from fcreplay.config import Config

config = Config().config

with open(pkg_resources.resource_filename('fcreplay', 'data/character_detect.json'), "r") as json_data_file:
    character_dict = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)


def process_img(frame_rgb, character_images, count, game):
    # We only need a video frame ever two seconds
    if not count % 120 == 0:
        return

    # We only care about certain row of the video frame, so crop the video frame
    x_len = frame_rgb.shape[1]
    cropped_frame = frame_rgb[character_dict[game]['location']['y1']:character_dict[game]['location']['y'], 0:x_len, :]

    # Convert the cropped frame grayscale
    frame_gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

    p1_character_score = {}
    p2_character_score = {}

    # Loop over every character
    for character in character_images:
        # Loop over every character image
        for image in character_images[character]['images']:
            # Get the dimensions of the current character image from the configuration file
            w, h = image.shape[::-1]
            character_images[character]['w'] = w
            character_images[character]['h'] = h

            # Compare the cropped frame against the character image
            res = cv2.matchTemplate(frame_gray, image, cv2.TM_CCOEFF_NORMED)

            # Adjust the detection threshold
            threshold = 0.85

            # Find a the most likely location of the character image in the frame, based on a threshold
            loc = np.where(res >= threshold)
            
            # This is the tricky bit. The loc contains the possible location of the character
            # found in the croped frame. Since the video file will have compression artifacts, 
            # multiple images are used to generate dict containing a list of characters and
            # their score. 
            for pt in zip(*loc[::-1]):
                # Find P1
                if pt[0] < 256:
                    if character not in p1_character_score:
                        p1_character_score[character] = 1
                    else:
                        p1_character_score[character] += 1
                
                # Fine P2
                else:
                    if character not in p2_character_score:
                        p2_character_score[character] = 1
                    else:
                        p2_character_score[character] += 1

    if p1_character_score and p2_character_score:
        # Return the p1 and p2 characters with the highest score
        return [max(p1_character_score), max(p2_character_score)]
    else:
        return False, False


def character_detect(game, videofile):
    """Detects characters

    Args:
        videofile (String): Path to video

    Returns:
        List: [[p1,p2,time][p1,p2,time]...]
    """
    vidcap = cv2.VideoCapture(videofile)

    characters = character_dict[game]['characters']

    # Load all character images
    character_images = {}
    charnames_dir = pkg_resources.resource_filename('fcreplay', 'data/charnames/')
    for character in characters:
        for i in range(1, 10):
            if character not in character_images:
                character_images[character] = {'images': []}
            character_images[character]['images'].append(cv2.imread(f'{charnames_dir}/{game}/{character}{i}.png', 0))
    count = 0

    # [ p1, p2, start-time ]
    times = []

    while True:
        # Read each video frame until the end of file. Seeking isn't supported in cv2.VideoCapture (afaik)
        success, image = vidcap.read()
        if not success:
            break # Exit when finish reading the video file
        
        # Set what frame we are on
        count += 1

        # Look for the characters every 120 seconds
        match = process_img(image, character_images, count, game)

        # If any characters are returned:
        if match is not None:
            p1 = match[0]
            p2 = match[1]

            # Only update if both characters are detected. This further reduces the chance of incorrect image
            # dectection. Then, only add a new detection to the *times* array if the current detection is
            # different to the previous detection. The most likely cause of this is due to characters changing,
            # however it is possible that incorrect characters could be detected. This could be fixed by
            # comparing against more more than just the previous result.
            if p1 is not False and p2 is not False:
                # Always add the first detection:
                if len(times) == 0:
                    times.append([p1, p2, str(datetime.timedelta(seconds=int(count/60)))])

                # If the detection is different, then add a new time 
                elif p1 not in times[-1][0] or p2 not in times[-1][1]:
                    times.append([p1, p2, str(datetime.timedelta(seconds=int(count/60)))])

    logging.debug(f'Video: {videofile}')
    video_chars = []
    for i in times:
        # Log the times detected
        logging.info(f'P1: {i[0]}, P2: {i[1]}, Time: {i[2]}')

    # Return all the times the p1 and p2 characters were detected:
    # times = [[p1_char,p2_char,time][p1_char,p2_char,time]....]
    return times


if __name__ == "__main__":
    character_detect(sys.argv[1], sys.argv[2])
