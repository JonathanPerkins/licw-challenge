# LICW Challenge scoring
This is a Python script to parse an ADIF log file and calculate the score for the LICW Challenge (see https://licwchallenge.org for more details)

## Log entry requirements

In order to add the extra LICW Challenge data, it is necessary when logging a challenge QSO
that a special text field is added into the QSO note/comment field in your logging program.
This can be added to any other notes you enter for this QSO and can be at any position in
the note field.

The format of this special text string is:

```
LICW[SPC:1234xx]
```

Where:

* SPC = 2 or 3 character state/province/country code
* 1234 = the LICW membership number received from the other station
* xx = optional one or more bonus letters received from the other station

The remaining data for calculating scores is obtained from the normal QSO ADIF records.

## Usage

The challenge scoring program is a command line script requiring Python 3 with its
default libraries; there should be no need to install anything extra.

On Linux/MacOS:

```
./challenge_score.py <adif log file name>
```

Or on Windows:

```
python challenge_score.py <adif log file name>
```

### Optional parameters

The program can optionally filter QSOs by challenge quarter, so that it can be given
a large ADIF file and just score the quarter of interest. You can either chose the
current quarter or specify which quarter you require, e.g:

Process score for the current quarter:

```
./challenge_score.py -q now all_qsos.adif
```

Or for the second quarter 2023:

```
./challenge_score.py -q 2:23 all_qsos.adif
```

### Example

```
jonathan@Mac-mini licw-challenge % ./challenge_score.py test/g4ivv_apr_23.adif

--------------------------------------------------------------------
01 Apr 23   IZ5CNC     Mark       ITA    2524   20m  1 plus 2 bonus
01 Apr 23   W2ITT      Rob         NY   263is   20m  2 plus 3 bonus
01 Apr 23   K2GV       Jerry       NY    004i   15m  2 points
01 Apr 23   KB4QQJ     Randy       NC  1086is   15m  2 plus 3 bonus
01 Apr 23   WB2UZE     Howard      NY      2a   15m  2 points
02 Apr 23   KB4QQJ     Randy       NC  1086is   20m  2 plus 3 bonus
02 Apr 23   KB4QQJ     Randy       NC  1086is   17m  2 plus 3 bonus
04 Apr 23   K2GV       Jerry       NY    004i   20m  2 points
10 Apr 23   WA2AKV     Hal         NY     77i   15m  2 points
12 Apr 23   G0POT      Michael    ENG   1071i   40m  2 plus 2 bonus
03 May 23   W4CMG      Cathy       TN   899is   20m  2 plus 3 bonus
03 May 23   W4EMB      Ed          TN  3459is   20m  2 plus 3 bonus
03 May 23   KD2YMM     Kasey       NY   3405a   20m  2 points
04 May 23   M0MCL      Kevin      ENG    4375   40m  1 plus 2 bonus
12 May 23   K9EI       Matt        IN    2467   20m  1 point
07 Jun 23   N2WBJ      Rich        NY     890   20m  1 point
--------------------------------------------------------------------

Total of 16 QSOs with 6 unique SPCs
Total score = 58
```

## TODO

Required before first public release:

* Add support for F2F, 2xF2F and first QSOs

Not essential, but possibly nice to have:

* Only allow QSOs on valid bands
* Support for VBand QSOs? How would this be done?

