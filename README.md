tinymusic
=========

Maintains a clone of your music directory with FLAC converted to Vorbis. tinymusic saves space on your filesystem by using hard links for other files.

Usage
=====

```
usage: Maintain a directory of transcoded music, replacing FLAC files with Vorbis
       [-h] [-q QUALITY] [--dry-run] [--no-delete] SRC DST

positional arguments:
  SRC                   Source directory
  DST                   Source directory

optional arguments:
  -h, --help            show this help message and exit
  -q QUALITY, --quality QUALITY
                        Vorbis quality (default: 5)
  --dry-run             Take no action, only display what actions would be
                        performed
  --no-delete           Do not delete from the destination, only add and
                        replace.
```
