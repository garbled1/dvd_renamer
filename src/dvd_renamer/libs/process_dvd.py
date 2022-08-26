"""
process_dvd that performs processing of a dvd

Contains:
    - Gather_DVD
"""
import os
import re
from pymediainfo import MediaInfo


class Gather_DVD:
    """Documentation of GatherDVD."""
    dir_to_process = None
    mkv_data = []

    def __init__(self, directory):
        """Initiatlizes class."""
        if directory[-1] == '/':
            self.dir_to_process = directory[:-1]
        else:
            self.dir_to_process = directory
        return

    def process_dir(self, imf, title_files):
        """ Process a directory."""
        for (root, dirs, files) in os.walk(self.dir_to_process, topdown=True):
            if imf and root == self.dir_to_process:
                continue
            for file in files:
                if title_files and 'title_' not in file:
                    continue
                data = dict()
                data['filename'] = root + '/' + file

                media_info = MediaInfo.parse(data['filename'])
                duration = 0.0
                for track in media_info.tracks:
                    if track.track_type == "Video":
                        duration = duration + float(track.duration)
                data['duration'] = duration

                seconds = int((duration/1000)%60)
                minutes = int((duration/(1000*60))%60)
                hours = int((duration/(1000*60*60))%24)

                data['minutes'] = hours * 60 + minutes
                data['seconds'] = seconds

                self.mkv_data.append(data)

    def get_mkv_data(self):
        """ Return the collected mkv data."""
        return self.mkv_data

    def guess_name(self):
        """ Try to guess the name of the movie."""
        chunks = self.dir_to_process.split('/')
        name = chunks[-1]
        pattern = r' \([0-9]*\)'
        name = re.sub(pattern, '', name)
        name = re.sub(re.compile('^The '), '', name)
        return name

    def guess_year(self):
        """ Try to guess the year of the movie."""
        year = None
        chunks = self.dir_to_process.split('/')

        if chunks[-1][-6] == '(' and chunks[-1][-1] == ')':
            year_str = chunks[-1][-5:-1]
            if year_str.isdigit():
                year = int(year_str)

        return year
