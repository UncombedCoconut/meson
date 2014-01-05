#!/usr/bin/env python3

# Copyright 2014 Jussi Pakkanen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, os
import pickle
from optparse import OptionParser
import coredata
from meson import build_types

usage_info = '%prog [build dir] [set commands]'

parser = OptionParser(usage=usage_info, version=coredata.version)

parser.add_option('-D', action='append', default=[], dest='sets',
                  help='Set an option to the given value.')

class ConfException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Conf:
    def __init__(self, build_dir):
        self.build_dir = build_dir
        self.coredata_file = os.path.join(build_dir, 'meson-private/coredata.dat')
        self.build_file = os.path.join(build_dir, 'meson-private/build.dat')
        if not os.path.isfile(self.coredata_file) or not os.path.isfile(self.build_file):
            raise ConfException('Directory %s does not seem to be a Meson build directory.' % build_dir)
        self.coredata = pickle.load(open(self.coredata_file, 'rb'))
        self.build = pickle.load(open(self.build_file, 'rb'))
        if self.coredata.version != coredata.version:
            raise ConfException('Version mismatch (%s vs %s)' %
                                (coredata.version, self.coredata.version))

    def save(self):
        # Only called if something has changed so overwrite unconditionally.
        pickle.dump(self.coredata, open(self.coredata_file, 'wb'))

    def print_aligned(self, arr):
        longest = max((len(x[0]) for x in arr))
        for i in arr:
            name = i[0]
            value = i[1]
            padding = ' '*(longest - len(name))
            f = '%s:%s' % (name, padding)
            print(f, value)

    def tobool(self, thing):
        if thing.lower() == 'true':
            return True
        if thing.lower() == 'false':
            return False
        raise ConfException('Value %s is not boolean (true or false).' % thing)

    def set_options(self, options):
        for o in options:
            if '=' not in o:
                raise ConfException('Value "%s" not of type "a=b".' % o)
            (k, v) = o.split('=', 1)
            if k == 'type':
                if v not in build_types:
                    raise ConfException('Invalid build type %s.' % v)
                self.coredata.buildtype = v
            elif k == 'strip':
                self.coredata.strip = self.tobool(v)
            elif k == 'coverage':
                v = self.tobool(v)
                self.coredata.coverage = self.tobool(v)
            elif k == 'pch':
                self.coredata.use_pch = self.tobool(v)
            elif k == 'unity':
                self.coredata.unity = self.tobool(v)

    def print_conf(self):
        print('Core properties\n')
        print('Source dir:', self.build.environment.source_dir)
        print('Build dir: ', self.build.environment.build_dir)
        print('')
        print('Core options\n')
        carr = []
        carr.append(['Build type', self.coredata.buildtype])
        carr.append(['Strip on install', self.coredata.strip])
        carr.append(['Coverage', self.coredata.coverage])
        carr.append(['Precompiled headers', self.coredata.use_pch])
        carr.append(['Unity build', self.coredata.unity])
        self.print_aligned(carr)
        print('')
        print('Project options\n')
        options = self.coredata.user_options
        keys = list(options.keys())
        keys.sort()
        optarr = []
        for key in keys:
            opt = options[key]
            optarr.append([key, opt.value])
        self.print_aligned(optarr)

if __name__ == '__main__':
    (options, args) = parser.parse_args(sys.argv)
    if len(args) > 2:
        print(args)
        print('%s <build directory>' % sys.argv[0])
        print('If you omit the build directory, the current directory is substituted.')
        sys.exit(1)
    if len(args) == 1:
        builddir = os.getcwd()
    else:
        builddir = args[-1]
    try:
        c = Conf(builddir)
        if len(options.sets) > 0:
            c.set_options(options.sets)
            c.save()
        else:
            c.print_conf()
    except ConfException as e:
        print('Meson configurator encountered an error:\n')
        print(e)

