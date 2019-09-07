#!/usr/bin/env python
"""

::

    [blyth@localhost opticks]$ find . -name '*.py' -exec grep -H coding: {} \;
    ./notes/conf.py:# -*- coding: utf-8 -*-
    ./analytic/gdml2idmap.py:#-*- coding: utf-8 -*-
    ./conf.py:# -*- coding: utf-8 -*-

"""

import os
from collections import OrderedDict as odict 
import regex as re

class FileTypes(object):
    typeSettings = {
        "java": {
            "extensions": [".java", ".scala", ".groovy", ".jape", ".js"],
            "keepFirst": None,
            "blockCommentStartPattern": re.compile(r'^\s*/\*'),
            "blockCommentEndPattern": re.compile(r'\*/\s*$'),
            "lineCommentStartPattern": re.compile(r'\s*//'),
            "lineCommentEndPattern": None,
            "headerStartLine": "/*\n",
            "headerEndLine": " */\n",
            "headerLinePrefix": " * ",
            "headerLineSuffix": None
        },
        "script": {
            "extensions": [".sh", ".csh", ".pl", ".bash"],
            "keepFirst": re.compile(r'^#!|^# -\*-'),
            "blockCommentStartPattern": None,
            "blockCommentEndPattern": None,
            "lineCommentStartPattern": re.compile(r'\s*#'),
            "lineCommentEndPattern": None,
            "headerStartLine": "##\n",
            "headerEndLine": "##\n",
            "headerLinePrefix": "## ",
            "headerLineSuffix": None
        },
        "perl": {
            "extensions": [".pl"],
            "keepFirst": re.compile(r'^#!|^# -\*-'),
            "blockCommentStartPattern": None,
            "blockCommentEndPattern": None,
            "lineCommentStartPattern": re.compile(r'\s*#'),
            "lineCommentEndPattern": None,
            "headerStartLine": "##\n",
            "headerEndLine": "##\n",
            "headerLinePrefix": "## ",
            "headerLineSuffix": None
        },
        "python": {
            "extensions": [".py"],
            "keepFirst": re.compile(r'^#!|^# +pylint|^# +-\*-|^#-\*-|^# +coding|^# +encoding'),
            "blockCommentStartPattern": None,
            "blockCommentEndPattern": None,
            "lineCommentStartPattern": re.compile(r'\s*#'),
            "lineCommentEndPattern": None,
            "headerStartLine": "#\n",
            "headerEndLine": "#\n",
            "headerLinePrefix": "# ",
            "headerLineSuffix": None
        },
        "xml": {
            "extensions": [".xml"],
            "keepFirst": re.compile(r'^\s*<\?xml.*\?>'),
            "blockCommentStartPattern": re.compile(r'^\s*<!--'),
            "blockCommentEndPattern": re.compile(r'-->\s*$'),
            "lineCommentStartPattern": None,
            "lineCommentEndPattern": None,
            "headerStartLine": "<!--\n",
            "headerEndLine": "  -->\n",
            "headerLinePrefix": "-- ",
            "headerLineSuffix": None
        },
        "sql": {
            "extensions": [".sql"],
            "keepFirst": None,
            "blockCommentStartPattern": None,  # re.compile('^\s*/\*'),
            "blockCommentEndPattern": None,  # re.compile(r'\*/\s*$'),
            "lineCommentStartPattern": re.compile(r'\s*--'),
            "lineCommentEndPattern": None,
            "headerStartLine": "--\n",
            "headerEndLine": "--\n",
            "headerLinePrefix": "-- ",
            "headerLineSuffix": None
        },
        "c": {
            "extensions": [".c", ".cc", ".cpp", "c++", ".h", ".hpp", ".hh", ".cu", ".cuh", ".m", ".mm" ],
            "keepFirst": None,
            "blockCommentStartPattern": re.compile(r'^\s*/\*'),
            "blockCommentEndPattern": re.compile(r'\*/\s*$'),
            "lineCommentStartPattern": re.compile(r'\s*//'),
            "lineCommentEndPattern": None,
            "headerStartLine": "/*\n",
            "headerEndLine": " */\n",
            "headerLinePrefix": " * ",
            "headerLineSuffix": None
        },
        "glsl": {
            "extensions": [".glsl" ],
            "keepFirst": re.compile(r'^#version'),
            "blockCommentStartPattern": re.compile(r'^\s*/\*'),
            "blockCommentEndPattern": re.compile(r'\*/\s*$'),
            "lineCommentStartPattern": re.compile(r'\s*//'),
            "lineCommentEndPattern": None,
            "headerStartLine": "/*\n",
            "headerEndLine": " */\n",
            "headerLinePrefix": " * ",
            "headerLineSuffix": None
        },
        "ruby": {
            "extensions": [".rb"],
            "keepFirst": "^#!",
            "blockCommentStartPattern": re.compile('^=begin'),
            "blockCommentEndPattern": re.compile(r'^=end'),
            "lineCommentStartPattern": re.compile(r'\s*#'),
            "lineCommentEndPattern": None,
            "headerStartLine": "##\n",
            "headerEndLine": "##\n",
            "headerLinePrefix": "## ",
            "headerLineSuffix": None
        },
        "csharp": {
            "extensions": [".cs"],
            "keepFirst": None,
            "blockCommentStartPattern": None,
            "blockCommentEndPattern": None,
            "lineCommentStartPattern": re.compile(r'\s*//'),
            "lineCommentEndPattern": None,
            "headerStartLine": None,
            "headerEndLine": None,
            "headerLinePrefix": "// ",
            "headerLineSuffix": None
        },
        "vb": {
            "extensions": [".vb"],
            "keepFirst": None,
            "blockCommentStartPattern": None,
            "blockCommentEndPattern": None,
            "lineCommentStartPattern": re.compile(r"^\s*\'"),
            "lineCommentEndPattern": None,
            "headerStartLine": None,
            "headerEndLine": None,
            "headerLinePrefix": "' ",
            "headerLineSuffix": None
        },
        "erlang": {
            "extensions": [".erl", ".src", ".config", ".schema"],
            "keepFirst": None,
            "blockCommentStartPattern": None,
            "blockCommentEndPattern": None,
            "lineCommentStartPattern": None,
            "lineCommentEndPattern": None,
            "headerStartLine": "%% -*- erlang -*-\n%% %CopyrightBegin%\n%%\n",
            "headerEndLine": "%%\n%% %CopyrightEnd%\n\n",
            "headerLinePrefix": "%% ",
            "headerLineSuffix": None
        }
    }

    def __init__(self):
        ext2type = odict() 
        patterns = []
        for k in self.typeSettings:
            exts = self.typeSettings[k]["extensions"]
            for ext in exts:
                ext2type[ext] = k
                patterns.append("*" + ext)
            pass 
        pass
        self.ext2type = ext2type
        self.patterns = patterns

    def __call__(self, path):
        ext = os.path.splitext(path)[1]
        ftype = self.ext2type.get(ext)
        settings = self.typeSettings.get(ftype)
        settings["ftype"] = ftype 
        settings["path"] = path 
        return settings


if __name__ == '__main__':
   ft = FileTypes() 

   print(ft.ext2type)  

   for t in "a.py a.c a.h a.cpp a.bash".split():
       print(ft(t))


