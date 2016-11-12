#!/usr/bin/python

import re
import sys
from easygui import multchoicebox as multichoice

def main():
    xyz
if len(sys.argv)>1:
    suitefile = sys.argv[1]

with open(suitefile) as f:
    suite = suitefile.read()

match_tc_section = re.search(r'(?is)[\n|^]\*+ ?test ?cases? ?\*+(.*?)(\n\*|$)', suite)
tc_section = match_tc_section and match_tc_section.group(1)

# read preselection from file