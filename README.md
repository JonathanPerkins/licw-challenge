# LICW Challenge scoring
Python script to parse an ADIF log file and calculate the score for the LICW Challenge (see https://licwchallenge.org for furtrher details)

## Log entry requirements

In order to add the extra LICW Challenge data, it is necessary when logging a challenge QSO
that the special text is added into the QSO note/comment field in your logging program.

The format of this special text string is:

```
LICW[SPC:1234xx]
```

Where:

* SPC = 2 or 3 character state/province/country code
* 1234 = the LICW membership number received from the other station
* xx = optional one or more bonus letters received from the otehr station

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

Example:

```
jonathan@Mac-mini licw-challenge % ./challenge_score.py test/g4ivv_apr_23.adif

--------------------------------------------------------------------
IZ5CNC     Mark       ITA     2524  20m  1 plus 2 bonus points
W2ITT      Rob         NY    263is  20m  2 plus 3 bonus points
K2GV       Jerry       NY     004i  15m  2 points
KB4QQJ     Randy       NC   1086is  15m  2 plus 3 bonus points
WB2UZE     Howard      NY       2a  15m  2 points
KB4QQJ     Randy       NC   1086is  20m  2 plus 3 bonus points
KB4QQJ     Randy       NC   1086is  17m  2 plus 3 bonus points
K2GV       Jerry       NY     004i  20m  2 points
WA2AKV     Hal         NY      77i  15m  2 points
G0POT      Michael    ENG    1071i  40m  2 plus 2 bonus points
W4CMG      Cathy       TN    899is  20m  2 plus 3 bonus points
W4EMB      Ed          TN   3459is  20m  2 plus 3 bonus points
KD2YMM     Kasey       NY    3405a  20m  2 points
M0MCL      Kevin      ENG     4375  40m  1 plus 2 bonus points
K9EI       Matt        IN     2467  20m  1 point
N2WBJ      Rich        NY      890  20m  1 point
--------------------------------------------------------------------

Number of unique SPCs worked = 6
Total score = 58
```

## TODO

Required before first public release:

* Add support for F2F, 2xF2F and first QSOs
* Add better error handling

Not essential, but possibly nice to have:

* Allow user to specify valid date range, so a larger ADIF log file can be parsed.
* Only allow QSOs on valid bands
* Support for VBand QSOs? How would this be done?

