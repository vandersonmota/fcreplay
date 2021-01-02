from PIL import Image, ImageFont, ImageDraw, ImageOps
from fcreplay.config import Config
import logging
import cairosvg

log = logging.getLogger('fcreplay')


class UpdateThumbnail:
    def __init__(self):
        self.config = Config().config
        self.font_path = "/opt/droid-fonts/droid/DroidSans.ttf"
        self.flag_path = "/opt/flag-icon-css-3.5.0/flags/4x3"

    def _get_font_size(self, im, text, custom_width=None):
        fontsize = 1  # starting font size

        # portion of image width you want text width to be
        img_fraction = 0.95

        font = ImageFont.truetype(self.font_path, fontsize, layout_engine=ImageFont.LAYOUT_BASIC)

        if custom_width is not None:
            breakpoint = img_fraction * custom_width
        else:
            breakpoint = img_fraction * im.size[0]

        jumpsize = 75
        while True:
            if font.getsize(text)[0] < breakpoint:
                fontsize += jumpsize
            else:
                jumpsize = jumpsize // 2
                fontsize -= jumpsize
            font = ImageFont.truetype(self.font_path, fontsize, layout_engine=ImageFont.LAYOUT_BASIC)
            if jumpsize <= 1:
                break

        if fontsize > 107:
            return 107
        else:
            return fontsize

    def _add_flags(self, im, p1_country: str, p2_country: str, vs_font_height: int, p1_rank_length: int, p2_rank_length: int):
        p1_country = p1_country.lower()
        p2_country = p2_country.lower()

        try:
            with open(f"{self.flag_path}/{p1_country}.svg") as p1_svg:
                cairosvg.svg2png(file_obj=p1_svg, write_to='/tmp/p1_country.png', scale=0.2)
        except Exception:
            log.info(f"Unable to find flag svg for p1: {p1_country}")
            raise FileNotFoundError

        try:
            with open(f"/{self.flag_path}/{p2_country}.svg") as p2_svg:
                cairosvg.svg2png(file_obj=p2_svg, write_to='/tmp/p2_country.png', scale=0.2)
        except Exception:
            log.info(f"Unable to find flag svg for p1: {p2_country}")
            raise FileNotFoundError

        # Add border to flags
        p1_flag = Image.open('/tmp/p1_country.png')
        p2_flag = Image.open('/tmp/p2_country.png')

        p1_flag = ImageOps.expand(p1_flag, border=10, fill='black')
        p2_flag = ImageOps.expand(p2_flag, border=10, fill='black')

        y = (25 + vs_font_height + 25)
        p1_x = (15 + p1_rank_length + 15)
        p2_x = (im.size[0] - (p1_flag.size[0] + 15 + p2_rank_length + 15))

        im.paste(p1_flag, (p1_x, y))
        im.paste(p2_flag, (p2_x, y))
        return im

    def _add_rank_text(self, im, p1_rank, p2_rank, vs_font_height):
        ranks = {
            '0': {
                'text': '?',
                'color': '757575'
            },
            '1': {
                'text': 'E',
                'color': 'C27A3F'
            },
            '2': {
                'text': 'D',
                'color': 'B3B2B0'
            },
            '3': {
                'text': 'C',
                'color': 'F3C84A'
            },
            '4': {
                'text': 'B',
                'color': '00A9DA'
            },
            '5': {
                'text': 'A',
                'color': 'A047B2'
            },
            '6': {
                'text': 'S',
                'color': 'E54875'
            }
        }
        p1_rank_text = f"Rank {ranks[p1_rank]['text']}"
        p2_rank_text = f"Rank {ranks[p2_rank]['text']}"
        vs_fontsize = 90

        stroke_color = (0, 0, 0)

        rank_font = ImageFont.truetype(self.font_path, vs_fontsize, layout_engine=ImageFont.LAYOUT_BASIC)

        # Convert HEX to rgb color
        p1_rank_color = tuple(int(ranks[p1_rank]['color'][i: i + 2], 16) for i in (0, 2, 4))
        p2_rank_color = tuple(int(ranks[p2_rank]['color'][i: i + 2], 16) for i in (0, 2, 4))

        # Get p2_rank length
        p1_rank_length = rank_font.getsize(p2_rank_text)[0]
        p2_rank_length = rank_font.getsize(p2_rank_text)[0]

        y = (25 + vs_font_height + 25)
        p1_x = 15
        p2_x = (im.size[0] - p2_rank_length) - 15

        draw = ImageDraw.Draw(im)
        draw.text((p1_x, y), p1_rank_text, font=rank_font, fill=p1_rank_color, stroke_width=10, stroke_fill=stroke_color)
        draw.text((p2_x, y), p2_rank_text, font=rank_font, fill=p2_rank_color, stroke_width=10, stroke_fill=stroke_color)

        return [im, p1_rank_length, p2_rank_length]

    def _add_vs_text(self, im, p1_name, p2_name):
        draw = ImageDraw.Draw(im)
        fill_color = (255, 255, 255)
        stroke_color = (0, 0, 0)

        vs_text = f"{p1_name}  VS  {p2_name}"
        vs_fontsize = self._get_font_size(im, vs_text)

        vs_font = ImageFont.truetype(self.font_path, vs_fontsize, layout_engine=ImageFont.LAYOUT_BASIC)

        w = im.size[0]
        x = (w - vs_font.getsize(vs_text)[0]) / 2

        vs_font_height = vs_font.getsize(vs_text)[1]

        # put the text on the image
        draw.text((x, 25), vs_text, font=vs_font, fill=fill_color, stroke_width=10, stroke_fill=stroke_color)
        return [im, vs_font_height]

    def _resize_image(self, im):
        crop_y = 75
        im = im.crop((0, crop_y, 800, im.size[1] - crop_y))
        im = im.resize((1280, 720))
        return im

    def update_thumbnail(self, replay, thumbnail):
        log.info(f"Opening thumbnail: {str(thumbnail)}")
        im = Image.open(str(thumbnail))

        log.info("Resizing thumbnail")
        im = self._resize_image(im)

        log.info("Adding VS text to thumbnail")
        im, vs_font_height = self._add_vs_text(im, p1_name=replay.p1, p2_name=replay.p2)

        log.info("Adding rank text to thumbnail")
        im, p1_rank_width, p2_rank_width = self._add_rank_text(im, replay.p1_rank, replay.p2_rank, vs_font_height)

        log.info("Adding flags to thumbnail")
        im = self._add_flags(im, replay.p1_loc, replay.p2_loc, vs_font_height, p1_rank_width, p2_rank_width)

        im.save(thumbnail)
