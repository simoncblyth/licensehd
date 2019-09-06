#!/usr/bin/env python
# encoding: utf-8

import logging, os, sys, argparse, fnmatch
log = logging.getLogger(__name__)

from string import Template
from shutil import copyfile, copymode, copystat
from collections import OrderedDict as odict 

# third party external, which apparently handles encodings better than standard re
import regex as re

# local modules
from py2open import open
from filetypes import FileTypes

FT = FileTypes()

yearsPattern = re.compile(
    r"(?<=Copyright\s*(?:\(\s*[Cc©]\s*\)\s*))?([0-9][0-9][0-9][0-9](?:-[0-9][0-9]?[0-9]?[0-9]?)?)",
    re.IGNORECASE)
licensePattern = re.compile(r"license", re.IGNORECASE)
emptyPattern = re.compile(r'^\s*$')


class LicenseHD(object):
    headlines = 30
    def __init__(self, path, args):
        self.path = path
        self.args = args
        self.header = args.template(path)  # header text customized to file type 
         
        settings = FT(path)

        self.keep_first = settings.get("keepFirst")
        self.block_comment_start_pattern = settings.get("blockCommentStartPattern")
        self.block_comment_end_pattern = settings.get("blockCommentEndPattern")
        self.line_comment_start_pattern = settings.get("lineCommentStartPattern")

        with open(path, 'r', encoding=args.encoding) as f:
            self.lines = f.readlines()
        pass

        d = odict()
        d["path"] = path
        d["ftype"] = settings["ftype"]
        d["settings"] = settings
        d["skip"] = 0 
        d["headStart"] = None
        d["headEnd"] = None
        d["haveLicense"] = None
        d["yearsLine"] = None

        self.parse_head(d)  
        self.d = d 
        self.replace = d["headStart"] is not None and d["headEnd"] is not None and d["haveLicense"] 

    def parse_head(self, d):
        """
        Parse first lines of the file  
        #. on reaching something other than empty or comment, stop looking for header
        """ 
        rlines = self.lines[:self.headlines] 

        skip = 0 
        head_start = None
        i = 0
        nohead = False
        
        for line in rlines:
            if i == 0 and self.keep_first and self.keep_first.findall(line):
                skip = i + 1     # can only be 1  
            elif emptyPattern.findall(line):
                pass
            elif self.block_comment_start_pattern and self.block_comment_start_pattern.findall(line):
                head_start = i
                break
            elif self.line_comment_start_pattern and self.line_comment_start_pattern.findall(line):
                head_start = i
                break
            elif not self.block_comment_start_pattern and \
                    self.line_comment_start_pattern and \
                    self.line_comment_start_pattern.findall(line):
                head_start = i
                break
            else:
                nohead = True 
                break 
            pass
            i = i + 1
        pass

        if i == len(rlines): nohead = True

        if not nohead:      
            d["skip"] = skip
            d["headStart"] = head_start
            pass
            if self.block_comment_start_pattern:
                self.parse_block_comment(d, i, rlines)    
            else:
                self.parse_line_comment(d, i, rlines)    
            pass
        pass

    def parse_block_comment(self, d, i, rlines):
        have_license = None
        years_line = None
        head_end = None
        pass

        for j in range(i, len(rlines)):
            line = rlines[j]  
            if licensePattern.findall(line):
                have_license = True
            elif yearsPattern.findall(line):
                have_license = True
                years_line = j
            elif self.block_comment_end_pattern.findall(line):
                d["headEnd"] = j 
                d["haveLicense"] = have_license 
                d["yearsLine"] = years_line 
                break  
            pass 
        pass  

    def parse_line_comment(self, d, i, rlines):
        """
        # if we went through all the lines without finding the end of the block, it could be that the whole
        # file only consisted of the header, so lets return the last line index
        """
        if not self.line_comment_start_pattern: return

        have_license = None
        years_line = None
        ended = False

        for j in range(i, len(rlines)):
            line = rlines[j]  
            if self.line_comment_start_pattern.findall(line) and licensePattern.findall(line):
                have_license = True
            elif yearsPattern.findall(line):
                have_license = True
                years_line = j
            elif not self.line_comment_start_pattern.findall(line):
                d["headEnd"] = j - 1 
                d["haveLicense"] = have_license 
                d["yearsLine"] = years_line 
                ended = True 
            else:
                 pass
            pass 
        pass
        if not ended:
            d["headEnd"] = len(rlines) - 1  
            d["haveLicense"] = have_license 
            d["yearsLine"] = years_line 
        pass

    def __str__(self):
        return "\n".join(["%20s : %s " % (kv[0], kv[1]) for kv in self.d.items() ]) 

    def __repr__(self):
        return " hl:%(haveLicense)1d hs:%(headStart)2d he:%(headEnd)2d : %(path)30s " % self.d 

    head_start = property(lambda self:self.d["headStart"])
    head_end = property(lambda self:self.d["headEnd"])
    skip = property(lambda self:self.d["skip"])

    def write(self):
        p = self.path 
        ptmp = "%s.tmp" % p
        porig = "%s.orig" % p
 
        with open(ptmp, 'w', encoding=self.args.encoding) as fw:
            if self.replace:
                fw.writelines(self.lines[0:self.head_start])
                fw.writelines(self.header)
                fw.writelines(self.lines[self.head_end + 1:])
                print("\n[---\n"+"".join(lines[self.head_start:self.head_end+1])+"\n]---\n")  
            else:
                fw.writelines(self.lines[0:self.skip])
                fw.writelines(self.header)
                fw.writelines(self.lines[self.skip:])
            pass 
        pass
        if self.replace:
            copyfile( p, porig )
        pass
        copystat( p, ptmp )     

        # sanity check that the processing does not loose bits of the file
        chk0 = open(p, "r").readlines()
        chk  = open(ptmp, "r").readlines()

        if len(chk) < len(chk0):
            log.fatal("failed to process_header for %s %s %d %d " % (p, ptmp, len(chk), len(chk0) ))
        else:
            if os.path.isfile(p):
                os.remove(p) 
            pass
            copyfile( ptmp, p )
            copystat( ptmp, p )
      
            if os.path.isfile(ptmp):
                os.remove(ptmp) 
            pass
        pass  



def get_paths(fnpatterns, start_dir="."):
    """
    Retrieve files that match any of the glob patterns from the start_dir and below.
    :param fnpatterns: the file name patterns
    :param start_dir: directory where to start searching
    :return: generator that returns one path after the other
    """
    seen = set()
    for root, dirs, files in os.walk(start_dir):
        names = []
        for pattern in fnpatterns:
            names += fnmatch.filter(files, pattern)
        for name in names:
            path = os.path.join(root, name)
            if path in seen:
                continue
            seen.add(path)
            yield path

class LicenseTmpl(object):
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
        if header_end_line is not None:
            lines.append(header_end_line)
        pass 
        return lines

    def __str__(self):
        return "".join(self.lines) 


def parse_args():
    parser = argparse.ArgumentParser(description="License header updater")
    
    parser.add_argument("paths", nargs="*", default=[], help="File paths to process")
    parser.add_argument("--projdir", default=None, help="Directory to process")
    parser.add_argument("--tmpl", default="under-apache-2", help="Template name")
    parser.add_argument("--years", default="2019", help="Year or year range")
    parser.add_argument("--owner", default="Opticks Team", help="Name of copyright owner")
    parser.add_argument("--projname", default="Opticks", help="Name of project")
    parser.add_argument("--projurl", default="https://bitbucket.org/simoncblyth/opticks", help="Url of project")
    parser.add_argument("--enc", nargs=1, dest="encoding", default="utf-8",help="Encoding of program files")
    parser.add_argument("--level", default="info", help="logging level" )
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
    paths = args.paths if len(args.paths) > 0 else get_paths(FT.patterns, args.projdir)  
    for path in paths:
        lh = LicenseHD(path, args)
        print(repr(lh))
    pass 


