#!/usr/bin/env python
# plot and annotate lpcm wave files easily

# TODO;
# - consider moving sox coversion to be in this module so we can open
# arbitrarly formatted audio files into numpy arrays

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
# from scipy import signal
# from scipy import fftpack

import subprocess, os
import os.path as path

# abspath = lambda paths_itr : map(path.abspath, paths_itr)

class WavPack(object):
    def __init__(self, wave_file_list):
        self.flist = []
        self._vectors = {}
        self.fig = None
        self.add(wave_file_list)
        self.w, self.h = scr_dim()

    def _loadwav(self, index):
        try:
            # should use the wave module instead?
            (self.fs, sig) = wavfile.read(self.flist[index])
            sig = sig/max(sig)
            self._vectors[index] = sig
            print("loaded wave file : ",path.basename(self.flist[index]))
            print("|->",len(sig),"samples =",len(sig)/self.fs,"seconds @ ",self.fs," Hz")
        except:
            print("Failed to open wave file for plotting!\nEnsure that the wave file is in LPCM format!")

    @property
    def show(self):
        '''just a pretty printer for the internal path list'''
        print_table(map(path.basename, self.flist))

    @property
    def close_all_figs(self):
        plt.close('all')
        self.fig = None

    # @property
    # def close_fig(self):
    #     # plt.close(
    #     self.fig = None

    @property
    def free_cache(self):
        self._vectors.clear()

    def fullscreen(self):
        if self.mng:
            self.mng.full_screen_toggle()
        else:
            print("no figure handle exists?")

    def vector(self, index):
        # path exists and vector loaded
        if index in self._vectors.keys() and type(self._vectors[index]) == np.ndarray:
            # print("the file ", self.flist[index], "is already cached in _vectors dict!")
            return self._vectors[index]

        # path exists but vector no yet loaded
        elif self._vectors.get(index) == None:
            self._loadwav(index)
            return self._vectors[index]

        # request for an index which doesn't reference a path
        elif index not in self._vectors.keys():
        # if index + 1 > len(self.flist):
            print("Error: you requested an index out of range!")
            raise ValueError("no file path exists for index : " + str(index) + " see WavPack.show")
        else:
            raise ValueError("weird stuffs happening heres!")

    def add(self, paths):
        '''Add a wave file path to the WavPack.\n
        Can take a single path or a sequence of paths as input'''
        indices = []
        # could be a single path string
        if type(paths) == str:
            if path.exists(paths) and paths not in self.flist:
                self.flist.append(paths)
                return [self.flist.index(paths)]
            else:
                raise ValueError("path string not valid?!")
        # a sequence of paths? -> create a generator for returning indices
        else:
            for p in paths:
                if p not in self.flist:
                    self.flist.append(p)
                    self._vectors[self.flist.index(p)] = None
                else:
                    print(path.basename(p), "is already in our path list? -> see grapher.WavPack.show")

                # indices.append(self.flist.index(p))
            # return indices
                yield self.flist.index(p)

    def plot(self, *indices):
        self._plot(indices)

    def _plot(self, index_itr, start_time=0, samefig=True):
        axes = {}
        if type(index_itr) != 'list':
            indices = [i for i in index_itr]

        # create a new figure and format
        if not samefig or not self.fig:
            self.fig = plt.figure()
            self.mng = plt.get_current_fig_manager()

            # old way to adjust margins
            # h_margin_l = 0.12
            # h_margin_r = 1 - h_margin_l
            # v_margin_b = 0.12
            # v_margin_t = 1 - v_margin_b
            # self.fig.subplots_adjust(left=h_margin_l, right=h_margin_r, bottom=v_margin_b, top=v_margin_t)
        else:
            self.fig.clf()

        # set window to half screen size if only one signal to plot
        if len(indices) < 2:
            h = self.h/2
        else:
            h = self.h
        self.mng.resize(self.w, h)
            # self.fig.set_size_inches(10,2)

        # self.fig.tight_layout()

        for icount, i in enumerate(indices):

            t = np.arange(start_time, len(self.vector(i)) / self.fs, 1/self.fs)

            ax = self.fig.add_subplot(len(indices), 1, icount + 1)
            ax.plot(t, self.vector(i), figure=self.fig)
            ax.set_title(path.basename(self.flist[i]))
            ax.set_ylabel(i)
            ax.set_xlabel('Time (s)')
            axes[i] = ax

        # tighten up the margins
        self.fig.tight_layout(pad=1.03)
        return axes

    # @property
    # def figure():
    #     return self.fig

    def find_wavs(self, sdir):
        self.flist = file_scan('.*\.wav$', sdir)
        for i, path in enumerate(self.flist):
            self._vectors[i] = None
        print("found", len(self.flist), "files")

def red_vline(axes, time, label='this is a line?'):

    # add a vertical line
    axes.axvline(x=time, color='r')
    hfrac = float(time)
    # add a label to the line
    axes.annotate(label,
                  xy=(time, 1),
                  xycoords='data',
                  xytext=(5, -10),
                  textcoords='offset points')
                  # arrowprops=dict(facecolor='black', shrink=0.05),
                  # horizontalalignment='right', verticalalignment='bottom')
    return axes

def print_table(itr, field_header=['wave files'], delim='|'):

    itr = list(itr)
    max_width = max(len(field) for field in itr)
    widths = iter(lambda:max_width, 1) # an infinite width generator

    # print a field title header
    print('')
    print('index', delim, '',  end='')
    for f, w in zip(field_header, widths):
        print('{field:<{width}}'.format(field=f, width=w), delim, '', end='')
    print('\n')

    # print rows
    for row_index, row in enumerate(itr):
        # print index
        print('{0:5}'.format(str(row_index)), delim, '', end='')
        print('{r:<{width}}'.format(r=row, width=max_width), delim, '', end='')
        print()
        # # print columns
        # for col, w in zip(row, widths):
        #     print('{column:<{width}}'.format(column=col, width=w), delim, '', end='')
        # print()

def file_scan(re_literal, search_dir, method='find'):
    if method == 'find':
        try:
            found = subprocess.check_output(["find", search_dir, "-regex", re_literal])
            paths = found.splitlines()

            # if the returned values are 'bytes' then convert to strings
            str_paths = [path.abspath(b.decode()) for b in paths]
            return str_paths

        except subprocess.CalledProcessError as e:
            print("scanning logs using 'find' failed with output: " + e.output)

    elif method == 'walk':
        #TODO: os.walk method
        print("this should normally do an os.walk")
    else:
        print("no other logs scanning method currentlyl exists!")

def scr_dim():
    #TODO: find a more elegant way of doing this...say using
    # figure.get_size_inches()
    # figure.get_dpi()
    dn = path.dirname(path.realpath(__file__))
    bres = subprocess.check_output([dn + "/screen_size.sh"])
    dims = bres.decode().strip('\n').split(sep='x')  # left associative
    return tuple([i for i in map(int, dims)])

# pretty sure this doesn't work as the guy who wrote it is aweful at math
def adjustFigAspect(fig,aspect=1):
    '''
    Adjust the subplot parameters so that the figure has the correct aspect ratio.
    '''
    xsize,ysize = fig.get_size_inches()
    minsize = min(xsize,ysize)
    xlim = .4*minsize/xsize
    ylim = .4*minsize/ysize
    if aspect < 1:
        xlim *= aspect
    else:
        ylim /= aspect

    fig.subplots_adjust(left   = .5-xlim,
                        right  = .5+xlim,
                        bottom = .5-ylim,
                        top    = .5+ylim)

def test():
    wp = WavPack([])
    wp.find_wavs('/home/tyler/code/python/wavs/')
    wp.plot(0)
    return wp
