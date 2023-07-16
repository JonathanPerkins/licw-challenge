#!/usr/bin/python3

'''
#************************************************
# Program to read an ADIF logfile and
# calculate the score for the LICW challenge.
#************************************************
'''

import argparse
import textwrap
import re
from collections import deque
from datetime import datetime, date
from enum import Enum, auto

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
    '2XF2F': 10
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

class ChallengeException(Exception):
    ''' Exception for script errors '''
    def __init__(self, value, additional='', context=''):
        self._context = context
        self._additional = additional
        super(Exception, self).__init__(value)

    def add_context(self, context_str):
        ''' Add a further context string to the exception arguments '''
        if not self._context:
            self._context = context_str
        else:
            self._context = f"{context_str}: {self._context}"

    @property
    def context(self):
        ''' Getter for context '''
        return self._context

    @property
    def additional(self):
        ''' Getter for additional info '''
        return self._additional

class Qso():
    ''' Class representing a QSO '''

    def __init__(self, qso_fields=None):
        ''' Constructor '''
        # These are the minimum fields required for a valid QSO
        # to be scored for the LICW challenge
        self._date = None
        self._band = None
        self._callsign = None
        self._name = None
        self._spc = None
        self._mode = None
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
        return self._band and self._callsign and self._name and self._spc and self._licw_nr and self._date and self._mode and self._mode.upper() == 'CW'

    @property
    def callsign(self):
        ''' Getter for callsign '''
        return self._callsign

    @property
    def band(self):
        ''' Getter for band '''
        return self._band

    @property
    def date(self):
        ''' Getter for date '''
        return self._date

    @property
    def spc(self):
        ''' Getter for SPC '''
        return self._spc

    @property
    def mode(self):
        """ Getter for Mode """
        return self._mode

    @property
    def name(self):
        ''' Getter for name '''
        return self._name

    @property
    def licw_nr(self):
        ''' Getter for LICW number '''
        return self._licw_nr

    @property
    def bonus_letters(self):
        ''' Getter for bonus letters '''
        return self._bonus_letters

    @property
    def points(self):
        ''' Getter for base points '''
        return self._points

    @property
    def bonus(self):
        ''' Getter for bonus points '''
        return self._bonus

    @property
    def total(self):
        ''' Getter for total points '''
        return self._points + self._bonus

    def load_qso(self, qso_fields):
        ''' Load required QSO data fields from the given
            dictionary of QSO elements extracted from log file.
        '''
        # Invalidate any previous data
        self._licw_nr = None
        self._bonus_letters = None
        self._date = None
        self._mode = None
        if 'BAND' in qso_fields:
            self._band = qso_fields['BAND']
        if 'CALL' in qso_fields:
            self._callsign = qso_fields['CALL']
        if 'NAME' in qso_fields:
            self._name = qso_fields['NAME']
        if 'QSO_DATE' in qso_fields:
            try:
                self._date = int(qso_fields['QSO_DATE'])
            except ValueError:
                pass
        if 'MODE' in qso_fields:
            self._mode = qso_fields['MODE']

        # The SPC and LICW number should be found in the comment field,
        # formatted with optional bonus letters and optional 3rd
        # field list as: LICW[SPC:1234is:FIRST,F2F]
        extras_list = []
        if 'COMMENT' in qso_fields:
            match = re.search(r'LICW\[(.+)\]', qso_fields['COMMENT'].upper())
            if match:
                # Parse out the LICW data
                licw = match[1].split(':')
                if len(licw) > 1:
                    self._spc = licw[0]
                    # Parse the LICW number into number and bonus letters
                    nr_match = re.match(r'(\d+)([a-zA-Z]*)', licw[1])
                    if nr_match:
                        self._licw_nr = nr_match[1]
                        if nr_match.lastindex > 1:
                            self._bonus_letters = nr_match[2]
                    # Optional 3rd field present?
                    if len(licw) == 3:
                        extras_list = licw[2].split(',')
                else:
                    raise ChallengeException("invalid LICW field:", licw)
        # A LICW challenge QSO?
        if self._licw_nr:
            # Calculate the base points - only one entry from POINTS
            # allowed, choose the one with the highest value
            self._points = 1
            if self._callsign in POINTS:
                self._points = POINTS[self._callsign]
            for letter in self._bonus_letters:
                if letter in POINTS:
                    if POINTS[letter] > self._points:
                        self._points = POINTS[letter]
            for extra in extras_list:
                if extra in POINTS:
                    if POINTS[extra] > self._points:
                        self._points = POINTS[extra]
            # Calculate optional bonus points
            self._bonus = 0
            for letter in self._bonus_letters:
                if letter in BONUS:
                    self._bonus += BONUS[letter]
            for extra in extras_list:
                if extra in BONUS:
                    self._bonus += BONUS[extra]
            # DX contact?
            if len(self._spc) == 3 or self._spc.upper() == 'DX':
                self._bonus += BONUS['DX']

# *******************************************************************
#  ADIF parser
# *******************************************************************

class AdiDataSpecifierParser():
    ''' Class to parse an ADI Data Specifier, character by character.
        Specifiers are of the form:
            <F:L:T>D
        Where:
            F = case independant field name
            L = data length (optional, zero if not present)
            T = data type inicator (optional, text if not present)
            D = data of length L
    '''
    class State(Enum):
        ''' Enum for parser state '''
        WAIT_START = auto(),
        WAIT_END = auto(),
        DONE_TAG = auto(),
        TEXT = auto(),
        DONE_TEXT = auto()

    def __init__(self):
        ''' Constructor '''
        self._buffer = ''
        self._length = 0
        self._name = ''
        self._state = self.State.WAIT_START

    @property
    def name(self):
        ''' Getter for field name, converted to uppercase  '''
        return self._name.upper()

    @property
    def length(self):
        ''' Getter for data length (may be zero) '''
        return self._length

    @property
    def data(self):
        ''' Getter for the optional data '''
        return self._buffer

    def _reset_buffer_for_tag(self):
        ''' Resets the buffer start building a <ADIF:n> style tag '''
        self._buffer = ''
        self._length = 0
        self._state = self.State.WAIT_START

    def _reset_buffer_for_string(self, required_length):
        ''' Resets the buffer for reading a text string '''
        self._buffer = ''
        self._length = required_length
        self._state = self.State.TEXT

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
            if len(self._buffer) == self._length:
                self._state = self.State.DONE_TEXT

    def reset(self):
        ''' Reset the parser, ready to find another ADI data specifier '''
        self._buffer = ''
        self._length = 0
        self._name = ''
        self._state = self.State.WAIT_START

    def parse_char(self, char):
        ''' Parse another character.
            Returns True if a complete ADI data specifier is
            now available, False otherwise. After the caller
            has finsihed accessing the data, reset() must be called
            to start parsing for a new data specifier.
        '''
        self._update_buffer(char)
        if self._state == self.State.DONE_TAG:
            # Split tag into fields
            fields = self._buffer.split(':')
            # Name always present
            self._name = fields[0]
            if len(fields) > 1:
                try:
                    data_length = int(fields[1])
                    if data_length > 0:
                        self._reset_buffer_for_string(data_length)
                except ValueError:
                    raise ChallengeException("invalid ADI length field: ", self._buffer) from None
                # TODO add support for types? Not actually needed for this application
            else:
                # Name only, no data
                self._length = 0
        return self._state in (self.State.DONE_TAG, self.State.DONE_TEXT)

class AdifParser():
    ''' Class to parse an ADIF file

        The ADIF spec (www.adif.org) doesn't seem to restrict a
        data specifier to be completely defined on one line,
        so this implements a char-by-char stream parser.

        A data specifier is of the form:
             <fieldname:length:optional type>data

        An optional header is present if the first character is not a '<'.
    '''

    def __init__(self, qsos_deque):
        ''' Constructor '''
        self._started = False
        self._header_done = False
        self._adi_parser = AdiDataSpecifierParser()
        self._qsos = qsos_deque
        self._current_qso = {}
        # A count of all QSO records seen, regardless
        # of whether a challenge QSO or not. Helpful
        # for indicating where an error has occured.
        self._all_qso_count = 1

    def _get_key_qso_parts(self):
        ''' Internal helper function to dump to a string
            key QSO parts that might help identify a bad record
            in the log file
        '''
        info = ''
        if 'CALL' in self._current_qso:
            info += f"{self._current_qso['CALL']} "
        if 'QSO_DATE' in self._current_qso:
            info += f"on {date_formatter(self._current_qso['QSO_DATE'])} "
        if 'TIME_ON' in self._current_qso:
            info += f"at {self._current_qso['TIME_ON']} "
        return info.strip()

    def reset_parser(self):
        ''' Reset the parser '''
        self._started = False
        self._header_done = False
        self._all_qso_count = 1

    def parse(self, string):
        ''' Incremental string parser - normally this function
            would be called for each line read from the ADIF file
        '''
        for char in string:
            # Is this the first call to parse a file?
            if not self._started:
                # Determine if a header is present by examing the first
                # character. ADIF spec says header present if not a '<'.
                if char == '<':
                    self._header_done = True
                self._started = True
            # Pass the character into the ADI data specifier parser
            try:
                if self._adi_parser.parse_char(char):
                    # Parsing header?
                    if not self._header_done:
                        # Skip header contents until <EOH> is found
                        if self._adi_parser.name == 'EOH':
                            self._header_done = True
                    else:
                        # Each QSO record is complete on 'EOR'
                        if self._adi_parser.name == 'EOR':
                            # Create a QSO object and if valid place on queue
                            qso = Qso(self._current_qso)
                            if qso.is_valid:
                                self._qsos.append(qso)
                            self._current_qso.clear()
                            self._all_qso_count += 1
                        elif self._adi_parser.length > 0:
                            self._current_qso[self._adi_parser.name] = self._adi_parser.data
                    # ADI specifier complete, start on next one
                    self._adi_parser.reset()
            except ChallengeException as err:
                err.add_context(f"In QSO record #{self._all_qso_count} with {self._get_key_qso_parts()}")
                raise

# *******************************************************************
#  Challenge scorer
# *******************************************************************

class LicwChallenge():
    ''' Class representing a LICW challenge '''

    def __init__(self, start_date, end_date):
        ''' Constructor '''
        # Dictionary of valid QSO objects
        self._qso_list = {}
        # Start and end date filters (integers, YYYYMMDD)
        # Either may be None to disable that check.
        self._start_date = start_date
        self._end_date = end_date
        # Calculated scores
        self._num_qsos = 0
        self._total_score = 0
        self._num_spc = 0

    @property
    def num_qsos(self):
        ''' Getter for number of QSOs '''
        return self._num_qsos

    @property
    def num_spc(self):
        ''' Getter for number of unique SPCs '''
        return self._num_spc

    @property
    def total_score(self):
        ''' Getter for total score '''
        return self._total_score

    @property
    def validated_qsos(self):
        ''' Getter for a list of validated QSOs '''
        return self._qso_list.values()

    def add_qsos(self, qsos):
        ''' Add one or more QSOs to the challenge
        '''
        for qso in qsos:
            # Optional date filters
            if self._start_date:
                if qso.date < self._start_date:
                    continue
            if self._end_date:
                if qso.date > self._end_date:
                    continue
            # The callsign+band tuple must be unique
            callsign_band = (qso.callsign, qso.band)
            # Already worked this station on this band?
            if callsign_band in self._qso_list:
                # Choose the QSO with the highest score
                if qso.total > self._qso_list[callsign_band].total:
                    self._qso_list[callsign_band] = qso
            else:
                self._qso_list[callsign_band] = qso

    def calculate_score(self):
        ''' Calculate the challenge score '''
        self._total_score = 0
        spc = {}
        for qso in self._qso_list.values():
            self._total_score += qso.total
            spc[qso.spc] = True
        self._num_spc = len(spc)
        self._num_qsos = len(self._qso_list)
        # Plus one point per SPC
        self._total_score += self._num_spc

# *******************************************************************
#  Functions
# *******************************************************************

def date_formatter(numeric_date):
    ''' Convert date from integer YYYYMMDD to a user readable string '''
    day = f"{numeric_date}"
    # Convert string to ISO YYYY-MM-DD format for date function.
    day = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
    return date.fromisoformat(day).strftime('%d %b %y')

def determine_date_range(quarter):
    ''' Function to determine start and end dates for a given quater.
        The quater definition may be of 2 formats:
            now           - the current quarter
            [1..4]:[year] - quarter number and 2 or 4 digit year
        Dates are formatted as integers in the format YYYYMMDD
    '''
    start = None
    end = None
    start_mmdd = [101, 401, 701, 1001]
    end_mmdd = [331, 630, 930, 1231]
    # An undefined quarter will remove any date restriction
    if quarter:
        if quarter == 'now':
            # internally we number quarters from zero
            qnum = int((datetime.now().month - 1) / 3)
            year = datetime.now().year
        else:
            try:
                qnum, year = quarter.split(':')
                qnum = int(qnum)
                if qnum < 1 or qnum > 4:
                    raise ChallengeException(f"invalid quarter {qnum}:", quarter)
                # qnum numbers from zero
                qnum -= 1
                year = int(year)
                if year < 100:
                    year += 2000
            except ValueError as err:
                raise ChallengeException(f"invalid quarter {quarter}:", err) from None
        # Calculate start and end dates for the quarter, YYYYMMDD
        start = (year * 10000) + start_mmdd[qnum]
        end = (year * 10000) + end_mmdd[qnum]
    return start, end

def parse_logfile(filenames, quarter):
    ''' Parse the given ADIF log file(s) '''
    qsos = deque()
    adif = AdifParser(qsos)

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

    # Determine optional date filters
    start_date, end_date = determine_date_range(quarter)

    challenge = LicwChallenge(start_date, end_date)

    # Pass the queue of valid LICW challenge QSOs to the challenge
    # which will apply the cross QSO rules including handling duplicates
    challenge.add_qsos(qsos)

    # And calculate the total score
    challenge.calculate_score()

    # Display a list of the validated QSOs
    if quarter:
        print(f"\nFor the quarter from {date_formatter(start_date)} to {date_formatter(end_date)}:")
    print("\n--------------------------------------------------------------------")
    for qso in challenge.validated_qsos:
        number = qso.licw_nr
        if qso.bonus_letters:
            number += qso.bonus_letters.lower()
        if qso.bonus > 0:
            points = f"{qso.points} plus {qso.bonus} bonus"
        else:
            points = f"{qso.points} point"
            if qso.total > 1:
                points += 's'
        print(f"{date_formatter(qso.date)}   {qso.callsign:10} {qso.name:10}"
              f"{qso.spc:>3} {number:>8} {qso.band:>5}  {points}")
    print("--------------------------------------------------------------------")
    print(f"\nTotal of {challenge.num_qsos} QSOs with {challenge.num_spc} unique SPCs")
    print(f"Total score = {challenge.total_score}\n")


# *******************************************************************
#  Main
# *******************************************************************

ARG_PARSER = argparse.ArgumentParser(description=textwrap.dedent('''\
    Script to parse an ADIF file and calculate a LICW challenge score.

    See https://github.com/JonathanPerkins/licw-challenge for full
    instructions.
    '''),
    formatter_class=argparse.RawTextHelpFormatter)

# At least one input file required
ARG_PARSER.add_argument('log_files', metavar='<ADIF log file>', nargs='+')

# Optional arguments
ARG_PARSER.add_argument('-q', '--quarter',
                        dest='quarter', default=None,
                        metavar='<now|[1..4]:[year]>',
                        help="specify which year quarter to extract QSOs from (default no date limit)")

ARGS = ARG_PARSER.parse_args()

try:
    # Process log file
    parse_logfile(ARGS.log_files, ARGS.quarter)
except ChallengeException as ex:
    print(f"Error: {ex.context}: {ex} {ex.additional}")
