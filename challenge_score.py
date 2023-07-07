#!/usr/bin/python3

#************************************************
# Program to read an ADIF logfile and
# calculate the score for the LICW challenge.
#************************************************

import argparse
import textwrap
import re

# Basic points letters/callsigns/ids (1 point if not in this list)
# N.B: only one from this list allowed per QSO
POINTS = {
    'W2LCW': 3,
    'K2LCW': 5,
    'K': 4,
    'I': 2,
    'M': 2,
    'A': 2,
    'F2F': 5,
    '2xF2F': 10
}

# Bonus letters/identifiers and their points
# More than one per QSO allowed
BONUS = {
    'S': 3,
    'DX': 2,
    'FIRST': 10
}

# *******************************************************************
#  Classes
# *******************************************************************

class Qso():
    ''' Class representing a QSO '''

    def __init__(self, qso_fields=None):
        ''' Constructor '''
        # These are the minimum fields required for a valid QSO
        # to be scored for the LICW challenge
        self._band = None
        self._callsign = None
        self._name = None
        self._spc = None
        self._licw_nr = None
        # Base points for QSO
        self._points = 0
        # Optional bonus points
        self._bonus_letters = None
        self._bonus = 0
        # Parse the optional QSO fields
        if qso_fields:
            self.load_qso(qso_fields)
        
    @property
    def is_valid(self):
        ''' Getter to determine if the QSO is valid '''
        # Need all the required fields
        return self._band and self._callsign and self._name and self._spc and self._licw_nr
    
    @property
    def callsign(self):
        ''' Getter for callsign '''
        return self._callsign

    @property
    def band(self):
        ''' Getter for band '''
        return self._band

    @property
    def spc(self):
        ''' Getter for SPC '''
        return self._spc

    @property
    def points(self):
        ''' Getter for base points '''
        return self._points

    @property
    def bonus(self):
        ''' Getter for bonus points '''
        return self._bonus

    def load_qso(self, qso_fields):
        ''' Load required QSO data fields from the given 
            dictionary of QSO elements extracted from log file.
        '''
        # Invalidate any previous data
        self._licw_nr = None
        self._bonus_letters = None
        if qso_fields['band']:
            self._callsign = qso_fields['band']
        if qso_fields['callsign']:
            self._callsign = qso_fields['callsign']
        if qso_fields['name']:
            self._name = qso_fields['name']
        if qso_fields['spc']:
            self._callsign = qso_fields['spc']
        # The SPC and LICW number should be found in the comment field,
        # formatted with optional bonus letters as: LICW[SPC:1234is]
        if qso_fields['comment']:
            match = re.search(r'LICW\[(.+)\]', qso_fields['comment'])
            if match:
                print(match.group(1))
                # Parse out the LICW data
                licw = match[1].split(':')
                if len(licw) == 2:
                    self._spc = licw[0]
                    # Parse the LICW number into number and bonus letters
                    nr_match = re.match(r'(\d+)([a-zA-Z]*)', licw[1])
                    if nr_match:
                        self._licw_nr = nr_match[1]
                        if nr_match.lastindex > 1:
                            self._bonus_letters = nr_match[2]
        # Calculate the base points - only one entry from POINTS
        # allowed, choose the one with the highest value
        self._points = 1
        if self._callsign in POINTS:
            self._points = POINTS[self._callsign]
        for letter in self._bonus_letters:
            if letter in POINTS:
                if POINTS[letter] > self._points:
                    self._points = POINTS[letter]
        # TODO add support for F2F
        # Calculate optional bonus points
        self._bonus = 0
        for letter in self._bonus_letters:
            if letter in BONUS:
                self._bonus += BONUS[letter]
        # DX contact?
        if len(self._spc) == 3:
            self._bonus += BONUS['DX']
        # TODO add support for first QSO


class LicwChallenge():
    ''' Class representing a LICW challenge '''

    def __init__(self):
        ''' Constructor '''
        # Array of valid QSO objects
        self._qso_list = []
        # Calculated scores
        self._num_qsos = 0
        self._total_score = 0

    @property
    def num_qsos(self):
        ''' Getter for number of QSOs '''
        return self._num_qsos

    @property
    def total_score(self):
        ''' Getter for total score '''
        return self._total_score

    def add_qso(self, qso):
        ''' Add a QSO to the challenge '''
        self._qso_list.append(qso)

    def calculate_score(self):
        ''' Calculate the challenge score '''
        self._total_score = 0
        spc = {}
        for qso in self._qso_list:
            self._total_score += qso.points
            self._total_score += qso.bonus
            spc[qso.spc] = True
        # Plus one point per SPC    
        self._total_score += len(spc)
        print(f"num SPCs={len(spc)} total={self._total_score}")

# *******************************************************************
#  Methods
# *******************************************************************

def parse_logfile(filenames):
    ''' Parse the given ADIF log file(s) '''
    # The ADIF spec (www.adif.org) doesn't seem to restrict a
    # data specifier to be completely defined on one line.
    # A data specifier is of the form:
    #   <fieldname:length:optional type>data
    # Optional header is present if the first character is not a '<'.

    # Parsing strategy: read file one line at a time, stripping
    # trailing newlines and then pass those to my stream parser.
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as logfile:
            while True:
                line = logfile.readline()
                if not line:
                    break
                # Strip any trailing newline and pass to parser
                print(line.rstrip('\n'))


# *******************************************************************
#  Main
# *******************************************************************

ARG_PARSER = argparse.ArgumentParser(description=textwrap.dedent('''\
    Script to parse an ADIF file and calculate a LICW challenge score
    '''),
                                 formatter_class=argparse.RawTextHelpFormatter)

# At least one input file required
ARG_PARSER.add_argument('log_files', metavar='<ADIF log file>', nargs='+')

ARGS = ARG_PARSER.parse_args()

# Process log file
parse_logfile(ARGS.log_files)
