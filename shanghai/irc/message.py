
from collections import namedtuple
from typing import Dict, List

from .server_reply import ServerReply
from ..logging import get_default_logger


_ESCAPE_SEQUENCES = {
    'n': '\n',
    'r': '\r',
    's': ' ',
    '\\': '\\',
    ':': ';',
}


class Prefix(namedtuple("_Prefix", "name ident host")):

    __slots__ = ()

    @classmethod
    def from_string(cls, prefix: str) -> 'Prefix':
        name = prefix.lstrip(':')
        ident = None
        host = None
        if '@' in name:
            name, host = name.split('@', 1)
            if '!' in name:
                name, ident = name.split('!', 1)
        return cls(name, ident, host)

    def __str__(self) -> str:
        ret = self.name
        if self.host:
            if self.ident:
                ret += f"!{self.ident}"
            ret += f"@{self.host}"
        return ret


class Message:

    def __init__(self, command: str, *,
                 prefix: Prefix = None,
                 params: List[str] = None,
                 tags: Dict[str, str] = None,
                 raw_line: str = None):
        self.command = command
        self.prefix = prefix
        self.params = params if params is not None else []
        self.tags = tags if tags is not None else {}
        self.raw_line = raw_line

    @staticmethod
    def escape(value: str) -> str:
        out_value = ''
        sequences = {v: k for k, v in _ESCAPE_SEQUENCES.items()}
        for char in value:
            if char in sequences:
                out_value += '\\' + sequences.get(char)
            else:
                out_value += char
        return out_value

    @staticmethod
    def unescape(value: str) -> str:
        out_value = ''
        escape = False
        for char in value:
            if escape:
                out_value += _ESCAPE_SEQUENCES.get(char, char)
                escape = False
            else:
                if char == '\\':
                    escape = True
                else:
                    out_value += char
        return out_value

    @classmethod
    def from_line(cls, line) -> 'Message':
        # https://tools.ietf.org/html/rfc2812#section-2.3.1
        # http://ircv3.net/specs/core/message-tags-3.2.html
        raw_line = line
        tags = {}
        prefix = None

        if line.startswith('@'):
            # irc tag
            tag_string, line = line.split(None, 1)
            for tag in tag_string[1:].split(';'):
                if '=' in tag:
                    key, value = tag.split('=', 1)
                    value = cls.unescape(value)
                else:
                    key, value = tag, True
                tags[key] = value

        if line.startswith(':'):
            prefix_str, line = line.split(None, 1)
            prefix = Prefix.from_string(prefix_str)

        command, *line = line.split(None, 1)
        command = command.upper()  # TODO check if really case-insensitive
        if command.isdigit():
            try:
                command = ServerReply(command)
            except ValueError:
                get_default_logger().warning(f"unknown server reply code {command}; {raw_line}")

        params = []
        if line:
            line = line[0]
            while line:
                if line.startswith(':'):
                    params.append(line[1:])
                    line = ''
                else:
                    param, *line = line.split(None, 1)
                    params.append(param)
                    if line:
                        line = line[0]

        return cls(command, prefix=prefix, params=params, tags=tags,
                   raw_line=raw_line)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}({self.command!r}, prefix={self.prefix!r},"
                f" params={self.params!r}, tags={self.tags!r})")
