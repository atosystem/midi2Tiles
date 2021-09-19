"""pianoTileCreator

Author: Ian Shih
Email: yjshih23@gmail.com
Date: 2021/09/19

"""
from tqdm import tqdm, trange
import matplotlib.animation as manimation
import matplotlib.pyplot as plt
from miditoolkit.midi import parser as midi_parser

import numpy as np
import matplotlib
matplotlib.use("Agg")


class KB_key():
    def __init__(self, midi_num, rect, video_height, kb_top, tile_velocity, ticks_per_sec, key_color="green", showKeyVelocity=False, isSharp=False, notes=None):
        """Initialize Key objects

        Args:
            midi_num (int): the corressponding midi number of the piano key
            rect (matplotlib patch): the rectangle for representing piano key
            video_height (int): the height of the output video
            kb_top (int): the upper boundary of the piano keyboard
            tile_velocity (int): the velocity of the falling tiles
            ticks_per_sec (float): ticks per second
            key_color (str, optional): the color of tiles. Defaults to "green".
            showKeyVelocity (bool, optional): if True, the velocity of midi notes will affect the opacity of tiles. Defaults to False.
            isSharp (bool, optional): whether this key is sharp. Defaults to False.
            notes (list, optional): list of miditoolkit notes. Defaults to None.
        """
        self._midi_num = midi_num
        self._rect = rect
        self._notes = notes
        self._current_tick = 0
        self._isSharp = isSharp
        self._tiles = []
        self._kbtop = kb_top
        self._key_color = key_color
        self._showKeyVelocity = showKeyVelocity
        self._tile_velocity = tile_velocity
        self._ticks_per_sec = ticks_per_sec
        self._video_height = video_height
        self.createTiles()

    def createTiles(self):
        """create tiles
        """
        self._tiles = []
        for n in self._notes:
            start_y_pos = n.start / self._ticks_per_sec * self._tile_velocity + self._kbtop
            end_y_pos = n.end / self._ticks_per_sec * self._tile_velocity + self._kbtop
            if self._showKeyVelocity:
                alpha = n.velocity / 127
            else:
                alpha = 1
            _rect = plt.Rectangle((self._rect.get_x(), start_y_pos),
                                  self._rect.get_width(), end_y_pos-start_y_pos,
                                  facecolor=self._key_color, alpha=alpha)

            # state 0(not appeared)->1(present)->2(done)
            self._tiles.append(
                {"state": 0, "rect": _rect, "start_y_pos": start_y_pos, "initial_w": end_y_pos-start_y_pos})

    def update(self, tick):
        """update the animation
        Called every frame

        Args:
            tick (int): the current midi tick
        """
        # update piano tiles
        for t in range(len(self._tiles)):
            # move position
            if self._tiles[t]["state"] <= 1:
                if self._tiles[t]["rect"].get_y() <= self._kbtop:
                    self._tiles[t]["rect"].set_height(max(
                        0, self._tiles[t]["initial_w"] - self._kbtop + self._tiles[t]["start_y_pos"] - self._tile_velocity * tick / self._ticks_per_sec))
                else:
                    self._tiles[t]["rect"].set_y(
                        self._tiles[t]["start_y_pos"] - self._tile_velocity * tick / self._ticks_per_sec)

            # state transitiion
            if self._tiles[t]["state"] == 1:
                if self._tiles[t]["rect"].get_height() <= 0:
                    self._tiles[t]["rect"].remove()
                    self._tiles[t]["state"] = 2
            elif self._tiles[t]["state"] == 0:
                if self._tiles[t]["rect"].get_y() <= self._video_height:
                    plt.gca().add_patch(self._tiles[t]["rect"])
                    self._tiles[t]["state"] = 1

        # update piano display
        current_note = list(
            filter(lambda n: n.start <= tick and n.end > tick, self._notes))
        if len(current_note):
            self._rect.set_facecolor(self._key_color)
            if self._showKeyVelocity:
                self._rect.set_alpha(current_note[0].velocity / 127)
        else:
            if self._showKeyVelocity:
                self._rect.set_alpha(1)
            if self._isSharp:
                self._rect.set_facecolor("black")
            else:
                self._rect.set_facecolor("white")


class PianoTileCreator():
    def __init__(self, video_width, video_height, video_dpi, video_fps, KB_ratio, tile_velocity, key_color, showKeyVelocity):
        """piano tile creator

        Args:
            video_width (int): the width of the output video (px)
            video_height (int): the height of the output video (px)
            video_dpi (int): the dpi of the output video (px)
            video_fps (int): the fps of the output video (px)
            KB_ratio (float): the proportion of the piano keyboard display. This value should be in [0,1)
            tile_velocity (int): the velocity of the falling tiles
            key_color (string): the color of the tiles
            showKeyVelocity (bool): if True, the velocity of midi notes will affect the opacity of the tiles

        Raises:
            ValueError: KB_ratio not in [0,1)
        """
        self.FFMpegWriter = manimation.writers['ffmpeg']
        metadata = dict(title='', artist='',
                        comment='By piano tile creator')
        self.writer = self.FFMpegWriter(
            fps=video_fps, metadata=metadata, bitrate=video_dpi)

        self.fig = plt.figure(
            figsize=(video_width/video_dpi, video_height/video_dpi), dpi=video_dpi)

        self.vid_width = video_width
        self.vid_height = video_height
        self.vid_dpi = video_dpi
        self.vid_fps = video_fps

        self.key_color = key_color
        if KB_ratio >= 0 and KB_ratio < 1:
            self.kb_top = KB_ratio * self.vid_height
        else:
            raise ValueError(
                "KB_ratio is expected to be in [0,1), {} found".format(KB_ratio))
        self.tile_velocity = tile_velocity
        self.showKeyVelocity = showKeyVelocity

        self.all_key_objs = []

    def init_fig(self):
        """initialize figure settings
        """
        # remove margins
        self.fig.subplots_adjust(
            left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)

        # set up position
        self.ax = plt.axes(xlim=(0, self.vid_width), ylim=(0, self.vid_height))

        # hide axis
        self.ax.axis('off')
        self.init_keys()

    def init_keys(self):
        """initialize keyboard
        """
        # draw keyboard
        # draw top line
        kb_top_line = plt.Line2D(
            (0, self.vid_width), (self.kb_top, self.kb_top), lw=1)
        plt.gca().add_line(kb_top_line)

        all_key_rects = []
        # whitekeys
        white_key_width = float(self.vid_width) / 52
        self.white_key_width = white_key_width
        for x in range(52):
            _rect = plt.Rectangle((x * white_key_width, 0), white_key_width,
                                  self.kb_top, facecolor="white", edgecolor="black", lw=0.1)
            plt.gca().add_patch(_rect)
            all_key_rects.append(_rect)
        # black keys
        black_key_pattern = [16.69, 0, 13.97, 16.79, 0, 12.83, 14.76]
        black_key_pattern = [x / 22.15 *
                             white_key_width for x in black_key_pattern]
        black_key_height = self.kb_top * 80 / 126.27
        black_key_width = white_key_width * 11 / 22.15
        for x in range(51):
            if black_key_pattern[x % len(black_key_pattern)]:
                black_key_offset = black_key_pattern[x % len(
                    black_key_pattern)]
                _rect = plt.Rectangle((x * white_key_width + black_key_offset, self.kb_top -
                                      black_key_height), black_key_width, black_key_height, facecolor="black", lw=None)
                plt.gca().add_patch(_rect)
                all_key_rects.append(_rect)

        all_key_rects = sorted(all_key_rects, key=lambda k: k.get_x())

        self.all_key_objs = [KB_key(midi_num=21+i,
                                    rect=k,
                                    video_height=self.vid_height,
                                    kb_top=self.kb_top,
                                    tile_velocity=self.tile_velocity,
                                    ticks_per_sec=self.ticks_per_sec,
                                    key_color=self.key_color,
                                    isSharp=k.get_width() < white_key_width,
                                    showKeyVelocity=self.showKeyVelocity,
                                    notes=[]
                                    )
                             for i, k in enumerate(all_key_rects)]

    def loadMidiFile(self, midiFilePath, verbose=False):
        """load midi file

        Args:
            midiFilePath (string): midi file path
            verbose (bool, optional): show message. Defaults to False.
        """
        # parse midi
        self.midi_obj = midi_parser.MidiFile(midiFilePath)
        if verbose:
            print("Midi file loaded : {}".format(midiFilePath))

        self.all_notes = []
        for ins in self.midi_obj.instruments:
            self.all_notes.extend(ins.notes)

        # sort notes
        self.all_notes = sorted(
            self.all_notes, key=lambda n: (n.start, -n.pitch))
        # total_duration (secs)
        self.ticks_per_sec = self.midi_obj.ticks_per_beat * \
            self.midi_obj.tempo_changes[0].tempo / 60
        self.total_duration = self.all_notes[-1].end / self.ticks_per_sec
        self.ticks_per_frame = self.ticks_per_sec / self.vid_fps

        if verbose:
            print("Estimated Video Total Duration {:.2f} secs".format(
                self.total_duration))

        self.init_fig()

        # distribute notes into keyboard keys
        for n in self.all_notes:
            # check pitch range
            if n.pitch >= 21 and n.pitch <= 108:
                self.all_key_objs[n.pitch-21]._notes.append(n)
        for x in self.all_key_objs:
            x.createTiles()

    def render(self, outputFilePath, verbose=False):
        """render piano tiles video to disk

        Args:
            outputFilePath (string): output video file path
            verbose (bool, optional): show message. Defaults to False.
        """
        if verbose:
            print("Start Rendering (total {} frames)".format(
                int(self.total_duration * self.vid_fps) + 2))
        with self.writer.saving(self.fig, outputFilePath, self.vid_dpi):
            for i in trange(0, int(self.total_duration * self.vid_fps) + 2):
                tick = i * self.ticks_per_frame
                for k in self.all_key_objs:
                    k.update(tick)
                self.writer.grab_frame()
        if verbose:
            print("Done rendering")
            print("File saved {}".format(outputFilePath))
