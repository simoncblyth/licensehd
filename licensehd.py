#!/usr/bin/env python
# encoding: utf-8
"""
licensehd.py
==============

For high level usage see::

   env-;licensehd-;licensehd-vi 


::

   licensehd.py ~/opticks
   licensehd.py ~/opticks/okop/okop.bash  --level debug 


Python coding directives need to be on 1st or 2nd line ?

::

   find . -name '*.py' -exec grep -H coding {} \;



"""
import logging, os, sys, argparse, fnmatch
log = logging.getLogger(__name__)

from string import Template
from shutil import copyfile, copymode, copystat
from collections import OrderedDict as odict 

# import regex as re
# regex is a third party external, which apparently handles encodings better 
# than standard re but it seems to not be necessary in my usage 

import re

# local modules
from py2open import open
from filetypes import FileTypes

FT = FileTypes()

emptyPattern = re.compile(r'^\s*$')

        
class CopyrightLine(object):
    """
    Copyright Line must contain the "Copyright" and a year OR year range, eg  

       * Copyright (c) 2019 Opticks Team. All Rights Reserved.
       * Copyright (c) 2019-2020 Opticks Team. All Rights Reserved.

    """  
    pattern = re.compile("(?P<pre>.*?)(?P<yrs>[0-9]{4}(?:-[0-9][0-9]?[0-9]?[0-9]?)?)(?P<post>.*)$")

    def __init__(self, header):
        lines = filter( lambda l:l.find("Copyright") > -1, header )
        assert len(lines) > 0 
        line = lines[0] 
        m = self.pattern.match(line)
        assert m is not None, line 
        self.d = m.groupdict()

    def matches(self, line):
        """year range is excluded from match """
        return line.startswith(self.d["pre"]) and line.rstrip().endswith(self.d["post"]) 

    def __repr__(self):
        return " %(pre)s %(yr0)s %(yr1)s %(post)s " % self.d  
               


class LicenseTmpl(object):
    end_blank = True
    def __init__(self, path, args):
        with open(path, 'r') as f:
            lines = f.readlines()
        pass
        lines = [Template(line).substitute(args.d) for line in lines]
        self.lines = lines 

    def __call__(self, path):
        """
        :return template lines formatted for type of the path:
        """
        lines = []
        settings = FT(path)
        header_start_line = settings["headerStartLine"]
        header_end_line = settings["headerEndLine"]
        header_line_prefix = settings["headerLinePrefix"]
        header_line_suffix = settings["headerLineSuffix"]
        #header_spacer = settings["headerSpacer"]

        if header_start_line is not None:
            lines.append(header_start_line)
        for line in self.lines:
            tmp = line
            if header_line_prefix is not None and line == '\n':
                tmp = header_line_prefix.rstrip() + tmp
            elif header_line_prefix is not None:
                tmp = header_line_prefix + tmp
            pass  
            if header_line_suffix is not None:
                tmp = tmp + header_line_suffix
            pass
            lines.append(tmp)
        pass
        if header_end_line is not None:
            lines.append(header_end_line)
        pass
        if self.end_blank:
            lines.append("\n")
        pass
        return lines

    def __str__(self):
        return "".join(self.lines) 


class LicenseHD(object):
    headlines = 30

    def __init__(self, path, args):
        self.path = path
        self.ptmp = "%s.tmp" % path
        self.args = args

        header = args.template(path)  # header text customized to file type
        copyrightline = CopyrightLine(header)

        self.copyrightline = copyrightline
        self.header = header 

        settings = FT(path)

        self.keep_first = settings.get("keepFirst")
        self.block_comment_start_pattern = settings.get("blockCommentStartPattern")
        self.block_comment_end_pattern = settings.get("blockCommentEndPattern")
        self.line_comment_start_pattern = settings.get("lineCommentStartPattern")

        log.debug("\n".join(["settings"] + ["%25s : %r " % (kv[0], kv[1]) for kv in settings.items() ]))

        with open(path, 'r', encoding=args.encoding) as f:
            self.lines = f.readlines()
        pass

        d = odict()
        d["path"] = path
        d["ftype"] = settings["ftype"]
        d["settings"] = settings

        d["skip"] = 0 
        d["headStart"] = -1
        d["headEnd"] = -1
        d["copyrightLine"] = -1
        d["otherCopyrightLine"] = -1
        d["comment"] = ""

        self.parse_head(d)  
        self.d = d 

        has_header = d["headStart"] > -1 and d["headEnd"] > -1
        has_license = has_header and d["copyrightLine"] > -1 
        has_other_license = has_header and d["otherCopyrightLine"] > -1 

        self.has_header = has_header 
        self.has_license = has_license
        self.has_other_license = has_other_license

        self.d["msg"] = self.msg 


        if has_header:
            _header = self.lines[d["headStart"]:d["headEnd"]+1]   
        else:
            _header = None
        pass
        self._header = _header      

        if self.has_license:
            prehead = self.lines[0:self.d["headStart"]] 
            posthead = self.lines[self.d["headEnd"]+1:]
        else:
            prehead = self.lines[0:self.d["skip"]]
            posthead = self.lines[self.d["skip"]:]
        pass 

        #print("prehead\n" + "".join(prehead) )
        #print("posthead\n" + "".join(posthead) )

        self.prehead = prehead
        self.posthead = posthead


    def parse_head(self, d):
        rlines = self.lines[:self.headlines] 
        i = 0
        for line in rlines:
            log.debug(" i %d skip %d  line [%s]  " % ( i, d["skip"], line ))

            if (i == 0 or d["skip"] > 0) and self.keep_first and self.keep_first.findall(line):
                d["skip"] = i + 1      
                log.debug(" keep_first skip line [%s] " % line )
            elif emptyPattern.findall(line):
                pass
            elif self.block_comment_start_pattern and self.block_comment_start_pattern.findall(line):
                d["comment"] = "block" 
                d["headStart"] = i
                break
            elif self.line_comment_start_pattern and self.line_comment_start_pattern.findall(line):
                d["comment"] = "line" 
                d["headStart"] = i
                break
            elif not self.block_comment_start_pattern and self.line_comment_start_pattern and self.line_comment_start_pattern.findall(line):
                d["comment"] = "line" 
                d["headStart"] = i
                break
            else:
                break 
            pass
            i = i + 1
        pass

        log.debug("   i:%d rlines:%d skip:%d headStart:%d comment:%s " % ( i, len(rlines), d["skip"], d["headStart"], d["comment"] ))

        if d["headStart"] > -1:
            if d["comment"] == "block":
                self.parse_block_comment(d, i, rlines)    
            elif d["comment"] == "line":
                self.parse_line_comment(d, i, rlines)    
            pass
        pass

    def parse_block_comment(self, d, i, rlines):
        for j in range(i, len(rlines)):
            line = rlines[j]  
            if self.copyrightline.matches(line):
                d["copyrightLine"] = j
            elif line.find("Copyright") > -1:
                d["otherCopyrightLine"] = j
            elif self.block_comment_end_pattern.findall(line) and LicenseTmpl.end_blank == False:
                d["headEnd"] = j 
                log.debug("found block_comment pattern-end headEnd %d " % d["headEnd"])
                break  
            elif emptyPattern.findall(line) and LicenseTmpl.end_blank == True:
                d["headEnd"] = j 
                log.debug("found block_comment empty-end  headEnd %d " % d["headEnd"])
                break  
            pass 
        pass  

    def parse_line_comment(self, d, i, rlines):
        """
        When using LicenseTmpl.end_blank the blank line must be
        treated as a part of header to avoid file growing by a blank line
        on each update. 
        """  
        if not self.line_comment_start_pattern: return
        for j in range(i, len(rlines)):
            line = rlines[j]  
            log.debug(line)

            if self.line_comment_start_pattern.findall(line) and self.copyrightline.matches(line):
                d["copyrightLine"] = j
            elif line.find("Copyright") > -1:
                d["otherCopyrightLine"] = j
            elif not self.line_comment_start_pattern.findall(line):
                d["headEnd"] = j if LicenseTmpl.end_blank else j - 1  
                log.debug("found line_comment headEnd %d with line [%s] " % (d["headEnd"], line) )
                break
            pass 
        pass
        # hmm : below seems an arbitrary setting of headEnd depending on the headlines
        if d["headEnd"] == -1:
            d["headEnd"] = len(rlines) - 1  
        pass

    def __str__(self):
        return "\n".join(["%20s : %s " % (kv[0], kv[1]) for kv in self.d.items() ]) 

    def __repr__(self):
        return " sk:%(skip)1d cpl:%(copyrightLine)2d  ocpl:%(otherCopyrightLine)2d  hs:%(headStart)2d he:%(headEnd)2d : %(msg)-20s :  %(path)-30s     " % self.d 

    def _get_msg(self):
        if self.has_other_license:
            msg = "has_other_license"
        elif self.has_license:
            msg = "has_license"
        else:
            msg = "no_license"
        pass
        return msg 
    msg = property(_get_msg)

    def write_tmp(self):
        assert os.path.exists(self.path)
        with open(self.ptmp, 'w', encoding=self.args.encoding) as fw:
            fw.writelines(self.prehead)
            fw.writelines(self.header)
            fw.writelines(self.posthead)
        pass
        copystat( self.path, self.ptmp )     

    def check_tmp(self):
        """
        sanity check that the processing does not loose bits of the file
        """
        chk0 = open(self.path, "r").readlines()
        chk  = open(self.ptmp, "r").readlines()

        if self.has_license and len(chk) != len(chk0):
            log.fatal("has_license update would have unexpectedly changed file length %s %s %d %d " % (self.path, self.ptmp, len(chk), len(chk0) ))
            return False  
        pass
        if len(chk) < len(chk0):
            log.fatal("write would have decreased file length  %s %s %d %d " % (self.path, self.ptmp, len(chk), len(chk0) ))
            return False  
        pass
        return True 

    def adopt_tmp(self):
        p = self.path
        ptmp = self.ptmp

        if os.path.isfile(p):
            os.remove(p) 
        pass
        copyfile( ptmp, p )
        copystat( ptmp, p )
  
        if os.path.isfile(ptmp):
            os.remove(ptmp) 
        pass

    def write(self):
        """
        """
        self.write_tmp() 
        ok = self.check_tmp() 
        if not ok: return
        self.adopt_tmp()


def get_paths(fnpatterns, start_dir="."):
    """
    Retrieve files that match any of the glob patterns from the start_dir and below.
    :param fnpatterns: the file name patterns
    :param start_dir: directory where to start searching
    :return: generator that returns one path after the other
    """
    paths = []
    for root, dirs, files in os.walk(start_dir):
        names = []
        for pattern in fnpatterns:
            names += fnmatch.filter(files, pattern)
        pass 
        for name in names:
            path = os.path.join(root, name)
            if path in paths:
                continue
            paths.append(path)
        pass 
    pass 
    return paths 

def parse_args():
    parser = argparse.ArgumentParser(description="License header updater")
    
    parser.add_argument("paths", nargs="*", default=[], help="File paths to process")
    parser.add_argument("--projdir", default=None, help="Directory to process")
    parser.add_argument("--tmpl", default="under-apache-2", help="Template name")
    parser.add_argument("--years", default="2019-2019", help="Year range")
    parser.add_argument("--owner", default="Opticks Team", help="Name of copyright owner")
    parser.add_argument("--projname", default="Opticks", help="Name of project")
    parser.add_argument("--projurl", default="https://bitbucket.org/simoncblyth/opticks", help="Url of project")
    parser.add_argument("--enc", nargs=1, dest="encoding", default="utf-8",help="Encoding of program files")
    parser.add_argument("--level", default="info", help="logging level" )
    parser.add_argument("--update", action="store_true", default=False, help="Updating existing license, eg when changing to new year range" )
    
    args = parser.parse_args()
    fmt = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    #fmt = '[%(asctime)s] p%(process)s {%(lineno)d} %(levelname)s - %(message)s'
    level=getattr(logging,args.level.upper())
    logging.basicConfig(level=level, format=fmt)

    args.d = dict(years=args.years, owner=args.owner, projectname=args.projname, projecturl=args.projurl )  
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "%s.tmpl" % args.tmpl )
    args.template = LicenseTmpl( template_path, args )

    return args

def test_template(args):
    tmpl = args.template
    print(args.template)
    for a in "a.py a.c a.bash".split():
        print("".join([a+"\n"]+tmpl(a))) 

if __name__ == '__main__':

    args = parse_args()
    log.debug(" paths %d " % len(args.paths))
    pass
    if len(args.paths) == 1 and os.path.isdir(args.paths[0]):
        paths = get_paths(FT.patterns, args.paths[0])
    elif len(args.paths) > 0:
        paths = args.paths
    elif not args.projdir is None:  
        paths = get_paths(FT.patterns, args.projdir)  
    else:
        assert 0
    pass
    for path in paths:
        lh = LicenseHD(path, args)
        #print("%r" % lh )
        if lh.has_other_license:
            pass
        elif lh.has_license and args.update:  
            lh.write()
        else:
            lh.write()
        pass 
    pass 

