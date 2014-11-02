#!/usr/bin/env python

import sys
import os
import subprocess

import argparse

DEFAULT_VORBIS_QUALITY = 5
IGNORE_FILES=['.stfolder']

class TinyMusicSync:

    def __init__(self, src, dst, encoder, exceptions=None, test=True):
        self.src = src
        self.dst = dst
        self.encoder = encoder
        self.mapping = {}
        self.hardlink = True
        self.delete = True
        if exceptions is not None:
            self.exceptions = exceptions
        else:
            self.exceptions = []
        if test:
            self.file_action = self.file_test_action
            self.delete_action = self.delete_test_action
            self.dir_action = lambda x: None
        else:
            self.file_action = self.file_real_action
            self.delete_action = self.delete_real_action
            self.dir_action = self.dir_real_action

    def _walk(self, top, intypes=None, outtype='.ogg'):
        files = []
        dirs = []
        if intypes is None:
            intypes = []
        for (dirpath, dirnames, filenames) in os.walk(top):
            relpath = os.path.relpath(dirpath, top)
            if relpath != '.':
                dirs.append(relpath)
            else:
                relpath = ''
            for filename in filenames:
                filebase, fileext = os.path.splitext(filename)
                if fileext.lower() in intypes:
                    files.append(os.path.join(relpath, filebase+outtype))
                    self.mapping[os.path.join(relpath, filebase+outtype)] = \
                        os.path.join(relpath, filename)
                else:
                    files.append(os.path.join(relpath, filename))
        return dirs, list(set(files))

    def delete_test_action(self, dirs, files):
        if not self.delete:
            return
        files = map(lambda x: os.path.join(self.dst, x), files)
        dirs = map(lambda x: os.path.join(self.dst, x), dirs)
        dirs.reverse()
        print('\n'.join(map(lambda x: 'Will delete\n  {}'.format(x), files)))
        print('\n'.join(map(lambda x: 'Will delete\n  {}'.format(x), dirs)))

    def delete_real_action(self, dirs, files):
        if not self.delete:
            return
        files = map(lambda x: os.path.join(self.dst, x), files)
        dirs = map(lambda x: os.path.join(self.dst, x), dirs)
        dirs.reverse()
        for filename in files:
            print("Deleting\n  {}".format(filename))
            os.unlink(filename)
        for dirname in dirs:
            print("Deleting\n  {}".format(dirname))
            os.rmdir(dirname)

    def file_test_action(self, filename):
        dstfile = os.path.join(self.dst, filename)
        if filename in self.mapping:
            # file should be encoded
            srcfile = os.path.join(self.src, self.mapping[filename])
            if not os.path.exists(dstfile):
                print("Will encode\n  {} to\n  {}".format(srcfile, dstfile))
            return
        srcfile = os.path.join(self.src, filename)
        if os.path.exists(dstfile):
            if os.stat(dstfile)[1] == os.stat(srcfile)[1]:
                return  # everything looks good!
            print("Will delete\n  {}".format(dstfile))
        print("Will link\n  {} to\n  {}".format(dstfile, srcfile))

    def file_real_action(self, filename):
        dstfile = os.path.join(self.dst, filename)
        if filename in self.mapping:
            # file should be encoded
            srcfile = os.path.join(self.src, self.mapping[filename])
            if not os.path.exists(dstfile):
                print("Encoding\n  {}".format(dstfile))
                self.encoder(srcfile, dstfile)
            return
        srcfile = os.path.join(self.src, filename)
        if os.path.exists(dstfile):
            if os.stat(dstfile)[1] == os.stat(srcfile)[1]:
                return  # everything looks good!
            print("Deleting\n  {}".format(dstfile))
            os.unlink(dstfile)
        print("Linking\n  {} to\n  {}".format(dstfile, srcfile))
        os.link(srcfile, dstfile)

    def dir_real_action(self, dirs):
        for d in dirs:
            try:
                os.mkdir(os.path.join(self.dst, d))
            except OSError:
                pass

    def sync(self):
        # determine target
        targetdirs, targetfiles = self._walk(self.src, ['.flac'])

        # gather info about dst
        dstdirs, dstfiles = self._walk(self.dst)

        to_delete_files = [f for f in dstfiles if f not in targetfiles
                           and f not in self.exceptions]
        to_delete_dirs = [d for d in dstdirs if d not in targetdirs]
        self.delete_action(to_delete_dirs, to_delete_files)
        self.dir_action(targetdirs)
        for filename in targetfiles:
            self.file_action(filename)


def encode(src, dst, quality):
    cmd = ['/usr/bin/oggenc',
           '-q', str(quality),
           '-o', dst,
           src]
    try:
        subprocess.check_call(cmd)
    except KeyboardInterrupt:
        try:
            os.unlink(dst)
        except OSError:
            pass
        raise
    except:
        try:
            os.unlink(dst)
        except OSError:
            pass
        print "Encoding failed!"


def main():
    parser = argparse.ArgumentParser('Maintain a directory of transcoded '
                                     'music, replacing FLAC files with '
                                     'Vorbis')
    parser.add_argument('src', metavar='SRC', type=str,
                        help='Source directory')
    parser.add_argument('dst', metavar='DST', type=str,
                        help='Source directory')
    parser.add_argument('-q', '--quality', action='store', type=int,
                        default=DEFAULT_VORBIS_QUALITY,
                        help='Vorbis quality (default: {})'.format(
                            DEFAULT_VORBIS_QUALITY))
    parser.add_argument('--dry-run', action='store_const',
                        const=True, default=False,
                        help='Take no action, only display what '
                             'actions would be performed')
    parser.add_argument('--no-delete', action='store_const',
                        const=True, default=False,
                        help='Do not delete from the destination, only '
                             'add and replace.')
    args = parser.parse_args()
    tms = TinyMusicSync(args.src,
                        args.dst,
                        lambda s, d: encode(s, d, args.quality),
                        IGNORE_FILES,
                        test=args.dry_run)
    tms.delete = not args.no_delete
    tms.sync()

if __name__ == '__main__':
    main()
