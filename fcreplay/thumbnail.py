"""Thumbnail generation.

This class is return a 'high entropy' thumbnail

The get_thumbnails function will generate thumbnails ever 10 seconds then
return the path to the thumbnail with the highest entroy
"""

from fcreplay.config import Config
from PIL import Image
import glob
import logging
import os
import subprocess

log = logging.getLogger('fcreplay')


class Thumbnail:
    def __init__(self):
        """Class initiliser."""
        self.config = Config().config

    def _create_thumbnails_fullframe(self, video_file_path):
        log.info("Generating thumbnails every 10 seconds")
        subprocess.run(
            [
                'ffmpeg',
                '-i', str(video_file_path),
                '-vf', 'fps=1/10',
                f"{self.config['fcadefbneo_path']}/avi/thumbnails-%06d.png"
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

    def _get_thumbnails(self):
        return glob.glob(f"{self.config['fcadefbneo_path']}/avi/thumbnails-*.png")

    def _get_image_entropy(self, image):
        im = Image.open(image)
        return im.entropy()

    def get_thumbnail(self, replay):
        """get_thumbnail.

        Args:
            replay ([sqlalchemy_object]): Sqlalchemy object for replay

        Returns:
            string: Full path to thumbnail
        """
        self._create_thumbnails_fullframe(f"{self.config['fcadefbneo_path']}/avi/{replay.id}.mp4")
        thumbnails = self._get_thumbnails()

        # Sort files by size. Assuming files that have the largest size have more entpoy
        thumbnails.sort(key=lambda f: os.stat(f).st_size, reverse=True)

        # Get the top 25% of the largest images
        i = int(len(thumbnails) * 0.25)
        if i < 1:
            i = len(thumbnails)

        thumbnails = thumbnails[:i]

        # From the top 25% find image entropy
        entropy_dict = {}
        for i in thumbnails:
            entropy_dict[i] = self._get_image_entropy(i)

        sorted_entroy = sorted(entropy_dict.items(), key=lambda x: x[1])

        # Return image with the highest entropy
        log.info(f"Using extracted thumbnail{sorted_entroy[-1][0]}")

        return sorted_entroy[-1][0]
