from youtube_dl import YoutubeDL
import json
import re
from searx import logger

logger = logger.getChild('video_links')


class YoutubeDLParser(object):

    def __init__(self, extensions):
        self.preferred = []
        self.filtered = []
        self._extensions = extensions
        self._res_re = re.compile('\d{3,}x\d{3,}', re.IGNORECASE)

    def debug(self, msg):
        # process youtube-dl output one line at a time
        try:
            # try to parse the output as a JSON string
            data = json.loads(msg)
        except ValueError:
            # if parsing fails, it is one of the status strings,
            # we can safely skip it
            return

        formats = data.get('formats', [])
        if len(formats) == 0:
            logger.debug('youtube-dl returned empty result')
            return

        fields = {'ext': 'ext',
                  'url': 'url',
                  'name': 'format',
                  'resolution': 'resolution',
                  'note': 'format_note',
                  'ac': 'acodec',
                  'vc': 'vcodec'}

        for fmt in formats:
            info = {}
            for k, v in fields.iteritems():
                info[k] = fmt.get(v, '').strip()

            # try to extract resolution information from format field
            if len(info['resolution']) == 0:
                matches = self._res_re.findall(info['name'])
                if len(matches) > 0:
                    info['resolution'] = matches[0]

            if info['ext'] in self._extensions:
                self.preferred.append(info)
            else:
                if info['ext'] not in default_extensions():
                    logger.warning('unknown extension ' + info['ext'])
                self.filtered.append(info)

    def warning(self, msg):
        logger.warning('youtube-dl warning: ' + msg)

    def error(self, msg):
        logger.error('youtube-dl error: ' + msg)


# default video extension list, copied from https://goo.gl/MOU3QH
def default_extensions():
    return ['mp4', 'flv', 'webm', '3gp', 'm4a', 'mp3', 'ogg', 'aac', 'wav']


def extract_video_links(url, extensions):
    if not url:
        return [], []

    parser = YoutubeDLParser(extensions)

    # youtube-dl options
    options = {
        # force JSON output to facilitate parsing
        'forcejson': True,

        # do not download anything, just return the links and information
        'skip_download': True,

        # object used to process youtube-dl output
        'logger': parser
    }

    try:
        with YoutubeDL(options) as ydl:
            ydl.download([str(url)])
    except Exception as e:
        logger.error('youtube-dl exception: ' + str(e))

    return parser.preferred, parser.filtered
