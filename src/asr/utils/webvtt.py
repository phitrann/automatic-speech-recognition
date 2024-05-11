# https://github.com/glut23/webvtt-py/tree/master
import re
import os
import codecs

TIMESTAMP_PATTERN = re.compile(r"(\d+)?:?(\d{2}):(\d{2})[.,](\d{3})")


class MalformedFileError(Exception):
    """Error raised when the file is not well formatted"""


class MalformedCaptionError(Exception):
    """Error raised when a caption is not well formatted"""


class MissingFilenameError(Exception):
    """Error raised when saving a file without filename."""


class TextBasedParser(object):
    """
    Parser for plain text caption files.
    This is a generic class, do not use directly.
    """

    TIMEFRAME_LINE_PATTERN = ""
    PARSER_OPTIONS = {}

    def __init__(self, parse_options=None):
        self.captions = []
        self.parse_options = parse_options or {}

    def read(self, file):
        """Reads the captions file."""
        content = self._get_content_from_file(file_path=file)
        self._validate(content)
        self._parse(content)

        return self

    def read_from_buffer(self, buffer):
        content = self._read_content_lines(buffer)
        self._validate(content)
        self._parse(content)

        return self

    def _get_content_from_file(self, file_path):
        encoding = self._read_file_encoding(file_path)
        with open(file_path, encoding=encoding) as f:
            return self._read_content_lines(f)

    def _read_file_encoding(self, file_path):
        first_bytes = min(32, os.path.getsize(file_path))
        with open(file_path, "rb") as f:
            raw = f.read(first_bytes)

        if raw.startswith(codecs.BOM_UTF8):
            return "utf-8-sig"
        else:
            return "utf-8"

    def _read_content_lines(self, file_obj):
        lines = [line.rstrip("\n\r") for line in file_obj.readlines()]

        if not lines:
            raise MalformedFileError("The file is empty.")

        return lines

    def _read_content(self, file):
        return self._get_content_from_file(file_path=file)

    def _parse_timeframe_line(self, line):
        """Parse timeframe line and return start and end timestamps."""
        tf = self._validate_timeframe_line(line)
        if not tf:
            raise MalformedCaptionError("Invalid time format")

        return tf.group(1), tf.group(2)

    def _validate_timeframe_line(self, line):
        return re.match(self.TIMEFRAME_LINE_PATTERN, line)

    def _is_timeframe_line(self, line):
        """
        This method returns True if the line contains the timeframes.
        To be implemented by child classes.
        """
        raise NotImplementedError

    def _validate(self, lines):
        """
        Validates the format of the parsed file.
        To be implemented by child classes.
        """
        raise NotImplementedError

    def _should_skip_line(self, line, index, caption):
        """
        This method returns True for a line that should be skipped.
        Implement in child classes if needed.
        """
        return False

    def _parse(self, lines):
        self.captions = []
        c = None

        for index, line in enumerate(lines):
            if self._is_timeframe_line(line):
                try:
                    start, end = self._parse_timeframe_line(line)
                except MalformedCaptionError as e:
                    raise MalformedCaptionError("{} in line {}".format(e, index + 1))
                c = Caption(start, end)
            elif self._should_skip_line(
                line, index, c
            ):  # allow child classes to skip lines based on the content
                continue
            elif line:
                if c is None:
                    raise MalformedCaptionError(
                        "Caption missing timeframe in line {}.".format(index + 1)
                    )
                else:
                    c.add_line(line)
            else:
                if c is None:
                    continue
                if not c.lines:
                    if self.PARSER_OPTIONS.get("ignore_empty_captions", False):
                        c = None
                        continue
                    raise MalformedCaptionError(
                        "Caption missing text in line {}.".format(index + 1)
                    )

                self.captions.append(c)
                c = None

        if c is not None and c.lines:
            self.captions.append(c)


class WebVTTParser(TextBasedParser):
    """
    WebVTT parser.
    """

    TIMEFRAME_LINE_PATTERN = re.compile(
        r"\s*((?:\d+:)?\d{2}:\d{2}.\d{3})\s*-->\s*((?:\d+:)?\d{2}:\d{2}.\d{3})"
    )
    COMMENT_PATTERN = re.compile(r"NOTE(?:\s.+|$)")
    STYLE_PATTERN = re.compile(r"STYLE[ \t]*$")

    def __init__(self):
        self.captions = []
        self.styles = []

    def _compute_blocks(self, lines):
        blocks = []

        for index, line in enumerate(lines, start=1):
            if line:
                if not blocks:
                    blocks.append(Block(index))
                if not blocks[-1].lines:
                    if not line.strip():
                        continue
                    blocks[-1].line_number = index
                blocks[-1].lines.append(line)
            else:
                blocks.append(Block(index))

        # filter out empty blocks and skip signature
        return list(filter(lambda x: x.lines, blocks))[1:]

    def _parse_cue_block(self, block):
        caption = Caption()
        cue_timings = None
        additional_blocks = None

        for line_number, line in enumerate(block.lines):
            if self._is_cue_timings_line(line):
                if cue_timings is None:
                    try:
                        cue_timings = self._parse_timeframe_line(line)
                    except MalformedCaptionError as e:
                        raise MalformedCaptionError(
                            "{} in line {}".format(e, block.line_number + line_number)
                        )
                else:
                    additional_blocks = self._compute_blocks(
                        ["WEBVTT", ""] + block.lines[line_number:]
                    )
                    break
            elif line_number == 0:
                caption.identifier = line
            else:
                caption.add_line(line)

        caption.start = cue_timings[0]
        caption.end = cue_timings[1]
        return caption, additional_blocks

    def _parse(self, lines):
        self.captions = []
        blocks = self._compute_blocks(lines)
        self._parse_blocks(blocks)

    def _is_empty(self, block):
        is_empty = True

        for line in block.lines:
            if line.strip() != "":
                is_empty = False

        return is_empty

    def _parse_blocks(self, blocks):
        for block in blocks:
            # skip empty blocks
            if self._is_empty(block):
                continue

            if self._is_cue_block(block):
                caption, additional_blocks = self._parse_cue_block(block)
                self.captions.append(caption)

                if additional_blocks:
                    self._parse_blocks(additional_blocks)

            elif self._is_comment_block(block):
                continue
            elif self._is_style_block(block):
                if self.captions:
                    raise MalformedFileError(
                        "Style block defined after the first cue in line {}.".format(
                            block.line_number
                        )
                    )
                style = Style()
                style.lines = block.lines[1:]
                self.styles.append(style)
            else:
                if len(block.lines) == 1:
                    raise MalformedCaptionError(
                        "Standalone cue identifier in line {}.".format(
                            block.line_number
                        )
                    )
                else:
                    raise MalformedCaptionError(
                        "Missing timing cue in line {}.".format(block.line_number + 1)
                    )

    def _validate(self, lines):
        if not re.match("WEBVTT", lines[0]):
            raise MalformedFileError("The file does not have a valid format")

    def _is_cue_timings_line(self, line):
        return "-->" in line

    def _is_cue_block(self, block):
        """Returns True if it is a cue block
        (one of the two first lines being a cue timing line)"""
        return any(map(self._is_cue_timings_line, block.lines[:2]))

    def _is_comment_block(self, block):
        """Returns True if it is a comment block"""
        return re.match(self.COMMENT_PATTERN, block.lines[0])

    def _is_style_block(self, block):
        """Returns True if it is a style block"""
        return re.match(self.STYLE_PATTERN, block.lines[0])


class Caption(object):
    CUE_TEXT_TAGS = re.compile("<.*?>")

    """
    Represents a caption.
    """

    def __init__(self, start="00:00:00.000", end="00:00:00.000", text=None):
        self.start = start
        self.end = end
        self.identifier = None

        # If lines is a string convert to a list
        if text and isinstance(text, str):
            text = text.splitlines()

        self._lines = text or []

    def __repr__(self):
        return "<%(cls)s start=%(start)s end=%(end)s text=%(text)s>" % {
            "cls": self.__class__.__name__,
            "start": self.start,
            "end": self.end,
            "text": self.text.replace("\n", "\\n"),
        }

    def __str__(self):
        return "%(start)s %(end)s %(text)s" % {
            "start": self.start,
            "end": self.end,
            "text": self.text.replace("\n", "\\n"),
        }

    def add_line(self, line):
        self.lines.append(line)

    def _to_seconds(self, hours, minutes, seconds, milliseconds):
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    def _parse_timestamp(self, timestamp):
        res = re.match(TIMESTAMP_PATTERN, timestamp)
        if not res:
            raise MalformedCaptionError("Invalid timestamp: {}".format(timestamp))

        values = list(map(lambda x: int(x) if x else 0, res.groups()))
        return self._to_seconds(*values)

    def _to_timestamp(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60 - hours * 60)
        seconds = total_seconds - hours * 3600 - minutes * 60
        return "{:02d}:{:02d}:{:06.3f}".format(hours, minutes, seconds)

    def _clean_cue_tags(self, text):
        return re.sub(self.CUE_TEXT_TAGS, "", text)

    @property
    def start_in_seconds(self):
        return self._start

    @property
    def end_in_seconds(self):
        return self._end

    @property
    def start(self):
        return self._to_timestamp(self._start)

    @start.setter
    def start(self, value):
        self._start = self._parse_timestamp(value)

    @property
    def end(self):
        return self._to_timestamp(self._end)

    @end.setter
    def end(self, value):
        self._end = self._parse_timestamp(value)

    @property
    def lines(self):
        return self._lines

    @property
    def text(self):
        """Returns the captions lines as a text (without cue tags)"""
        return self._clean_cue_tags(self.raw_text)

    @property
    def raw_text(self):
        """Returns the captions lines as a text (may include cue tags)"""
        return "\n".join(self.lines)

    @text.setter
    def text(self, value):
        if not isinstance(value, str):
            raise AttributeError(
                "String value expected but received {}.".format(type(value))
            )

        self._lines = value.splitlines()


class GenericBlock(object):
    """Generic class that defines a data structure holding an array of lines"""

    def __init__(self):
        self.lines = []


class Block(GenericBlock):
    def __init__(self, line_number):
        super().__init__()
        self.line_number = line_number


class Style(GenericBlock):
    @property
    def text(self):
        """Returns the style lines as a text"""
        return "".join(map(lambda x: x.strip(), self.lines))

    @text.setter
    def text(self, value):
        if not isinstance(value, str):
            raise TypeError("The text value must be a string.")
        self.lines = value.split("\n")


################################################################################################################################


class WebVTTWriter(object):
    def write(self, captions, f):
        f.write(self.webvtt_content(captions))

    def webvtt_content(self, captions):
        """
        Return captions content with webvtt formatting.
        """
        output = ["WEBVTT"]
        for caption in captions:
            output.append("")
            if caption.identifier:
                output.append(caption.identifier)
            output.append("{} --> {}".format(caption.start, caption.end))
            output.extend(caption.lines)
        return "\n".join(output)


class SRTWriter(object):
    def write(self, captions, f):
        for line_number, caption in enumerate(captions, start=1):
            f.write("{}\n".format(line_number))
            f.write(
                "{} --> {}\n".format(
                    self._to_srt_timestamp(caption.start_in_seconds),
                    self._to_srt_timestamp(caption.end_in_seconds),
                )
            )
            f.writelines(["{}\n".format(line) for line in caption.lines])
            f.write("\n")

    def _to_srt_timestamp(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60 - hours * 60)
        seconds = int(total_seconds - hours * 3600 - minutes * 60)
        milliseconds = round(
            (total_seconds - seconds - hours * 3600 - minutes * 60) * 1000
        )

        return "{:02d}:{:02d}:{:02d},{:03d}".format(
            hours, minutes, seconds, milliseconds
        )


class SBVWriter(object):
    pass


class WebVTT(object):
    """
    Parse captions in WebVTT format and also from other formats like SRT.

    To read WebVTT:

        WebVTT().read('captions.vtt')

    For other formats like SRT, use from_[format in lower case]:

        WebVTT().from_srt('captions.srt')

    A list of all supported formats is available calling list_formats().
    """

    def __init__(self, file="", captions=None, styles=None):
        self.file = file
        self._captions = captions or []
        self._styles = styles

    def __len__(self):
        return len(self._captions)

    def __getitem__(self, index):
        return self._captions[index]

    def __repr__(self):
        return "<%(cls)s file=%(file)s>" % {
            "cls": self.__class__.__name__,
            "file": self.file,
        }

    def __str__(self):
        return "\n".join([str(c) for c in self._captions])

    # @classmethod
    # def from_srt(cls, file):
    #     """Reads captions from a file in SubRip format."""
    #     parser = SRTParser().read(file)
    #     return cls(file=file, captions=parser.captions)

    # @classmethod
    # def from_sbv(cls, file):
    #     """Reads captions from a file in YouTube SBV format."""
    #     parser = SBVParser().read(file)
    #     return cls(file=file, captions=parser.captions)

    @classmethod
    def read(cls, file):
        """Reads a WebVTT captions file."""
        parser = WebVTTParser().read(file)
        return cls(file=file, captions=parser.captions, styles=parser.styles)

    @classmethod
    def read_buffer(cls, buffer):
        """Reads a WebVTT captions from a file-like object.
        Such file-like object may be the return of an io.open call,
        io.StringIO object, tempfile.TemporaryFile object, etc."""
        parser = WebVTTParser().read_from_buffer(buffer)
        return cls(captions=parser.captions, styles=parser.styles)

    def _get_output_file(self, output, extension="vtt"):
        if not output:
            if not self.file:
                raise MissingFilenameError
            # saving an original vtt file will overwrite the file
            # and for files read from other formats will save as vtt
            # with the same name and location
            return os.path.splitext(self.file)[0] + "." + extension
        else:
            target = os.path.join(os.getcwd(), output)
            if os.path.isdir(target):
                # if an output is provided and it is a directory
                # the file will be saved in that location with the same name
                filename = os.path.splitext(os.path.basename(self.file))[0]
                return os.path.join(target, "{}.{}".format(filename, extension))
            else:
                if target[-3:].lower() != extension:
                    target += "." + extension
                # otherwise the file will be written in the specified location
                return target

    def save(self, output=""):
        """Save the document.
        If no output is provided the file will be saved in the same location. Otherwise output
        can determine a target directory or file.
        """
        self.file = self._get_output_file(output)
        with open(self.file, "w", encoding="utf-8") as f:
            self.write(f)

    def save_as_srt(self, output=""):
        self.file = self._get_output_file(output, extension="srt")
        with open(self.file, "w", encoding="utf-8") as f:
            self.write(f, format="srt")

    def write(self, f, format="vtt"):
        if format == "vtt":
            WebVTTWriter().write(self._captions, f)
        # elif format == 'srt':
        #     SRTWriter().write(self._captions, f)

    #    elif output_format == OutputFormat.SBV:
    #        SBVWriter().write(self._captions, f)

    @staticmethod
    def list_formats():
        """Provides a list of supported formats that this class can read from."""
        return ("WebVTT (.vtt)", "SubRip (.srt)", "YouTube SBV (.sbv)")

    @property
    def captions(self):
        """Returns the list of captions."""
        return self._captions

    @property
    def total_length(self):
        """Returns the total length of the captions."""
        if not self._captions:
            return 0
        return int(self._captions[-1].end_in_seconds) - int(
            self._captions[0].start_in_seconds
        )

    @property
    def styles(self):
        return self._styles

    @property
    def content(self):
        """
        Return webvtt content with webvtt formatting.

        This property is useful in cases where the webvtt content is needed
        but no file saving on the system is required.
        """
        return WebVTTWriter().webvtt_content(self._captions)
