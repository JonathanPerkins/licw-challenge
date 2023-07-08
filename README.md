# licw-challenge
Python script to parse an ADIF log file and calculate the score for the LICW Challenge

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

## TODO

Required before first public release:

* Add support for F2F, 2xF2F and first QSOs
* Add one QSO per band validation (use highest score if duplicates)
* Add better error handling

Not essential, but possibly nice to have:

* Allow user to specify valid date range, so a larger ADIF log file can be parsed.
* Only allow QSOs on valid bands
* Support for VBand QSOs? How would this be done?

