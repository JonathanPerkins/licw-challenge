#!/usr/bin/python3

#************************************************
# Program to read an ADIF logfile and
# calculate the score for the LICW challenge.
#************************************************

import argparse
import textwrap
import re
from enum import Enum

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

class AdifParser():
    ''' Class to parse an ADIF file '''

    def __init__(self):
        ''' Constructor '''
        self._started = False
        self._header_done = False
        # For parsing individual elements
        self._buffer = ''
        self._required_length = 0
        self._string_name = ''
        self.State = Enum('State', ['WAIT_START', 'WAIT_END', 'DONE_TAG', 'TEXT', 'DONE_TEXT'])
        self._state = self.State.WAIT_START

    def _update_buffer(self, char):
        ''' Process the next character '''
        if self._state == self.State.WAIT_START:
            # Skipping characters, waiting for a '<'
            if char == '<':
                self._state = self.State.WAIT_END
        elif self._state == self.State.WAIT_END:
            # Appending to the buffer, waiting for a '>'
            if char == '>':
                self._state = self.State.DONE_TAG
            else:
                self._buffer += char
        elif self._state == self.State.TEXT:
            # Building a string of required length
            self._buffer += char
            if len(self._buffer) == self._required_length:
                self._state = self.State.DONE_TEXT

    def _reset_buffer_for_tag(self):
        ''' Resets the buffer start building a <ADIF:n> style tag '''
        self._buffer = ''
        self._state = self.State.WAIT_START

    def _reset_buffer_for_string(self, required_length, name):
        ''' Resets the buffer for reading a text string '''
        self._buffer = ''
        self._required_length = required_length
        self._string_name = name
        self._state = self.State.TEXT
    
    def reset_parser(self):
        ''' Reset the parser '''
        self._started = False
        self._header_done = False

    def parse(self, string):
        ''' Incremental string parser - normally this function 
            would be called for each line read from the ADIF file
        '''
        for char in string.upper():
            # Is this the first call to parse a file?
            if not self._started:
                # Determine if a header is present by examing the first
                # character. ADIF spec says header present if not a '<'.
                if char == '<':
                    self._header_done = True
                self._started = True
            # Parsing header?
            if not self._header_done:
                # Skip header contents until <EOH> is found
                self._update_buffer(char)
                if self._state == self.State.DONE_TAG:
                    # Found EOH?
                    if self._buffer == 'EOH':
                        self._header_done = True
                    # Search for another tag
                    # TODO may need to handle '<' in text? Use length param to skip?
                    self._reset_buffer_for_tag()
            else:
                # Parsing the body of the ADIF - each record ends in <EOR>
                self._update_buffer(char)
                if self._state == self.State.DONE_TAG:
                    # Found EOH?
                    if self._buffer == 'EOR':
                        print('end of record')
                    else:
                        # Split tag into NAME:LENGTH pairs
                        tag = self._buffer.split(':')
                        if len(tag) == 2:
                            try:
                                field_length = int(tag[1])
                                self._reset_buffer_for_string(field_length, tag[0])
                            except ValueError:
                                print("tag[1] did not contain a number!")
                        else:    
                            print(f"unknown tag: {self._buffer}")
                    if self._state == self.State.DONE_TAG:
                        self._reset_buffer_for_tag()
                elif self._state == self.State.DONE_TEXT:
                    print(f"{self._string_name}: {self._buffer}")
                    self._reset_buffer_for_tag()



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

    challenge = LicwChallenge()
    adif = AdifParser()

    # Parsing strategy: read file one line at a time, stripping
    # trailing newlines and then pass those to my stream parser.
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as logfile:
            while True:
                line = logfile.readline()
                if not line:
                    break
                # Strip any trailing newline and pass to parser
                adif.parse(line.rstrip('\n'))

    challenge.calculate_score()


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
