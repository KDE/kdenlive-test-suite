#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 Jean-Baptiste Mardelle <jb@kdenlive.org>
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL

import subprocess
import sys

import numpy

# seconds to sample audio file for
sample_time = 500  # number of points to scan cross correlation over
span = 150  # step size (in points) of cross correlation
step = 1  # minimum number of points that must overlap in cross correlation
# exception is raised if this cannot be met
min_overlap = 20  # report match when cross correlation has a peak exceeding threshold
threshold = 0.8


# calculate fingerprint
def calculate_fingerprints(filename):
    # Convert to wav
    tmpFile = "/tmp/out1.wav"
    # subprocess.getoutput('ffmpeg -y -i %s -filter:a "atempo=0.5" -vn %s' % (filename, tmpFile))
    subprocess.getoutput("ffmpeg -y -i %s -vn %s" % (filename, tmpFile))
    fpcalc_out = subprocess.getoutput(
        "fpcalc -raw -length %i %s" % (sample_time, tmpFile)
    )
    fingerprint_index = fpcalc_out.find("FINGERPRINT=") + 12
    # convert fingerprint to list of integers
    intlist = fpcalc_out[fingerprint_index:]
    fingerprints = list(map(int, intlist.split(",")))
    return fingerprints
    # returns correlation between lists


def correlation(listx, listy):
    if len(listx) == 0 or len(listy) == 0:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception("Empty lists cannot be correlated.")
    if len(listx) > len(listy):
        listx = listx[: len(listy)]
    elif len(listx) < len(listy):
        listy = listy[: len(listx)]

    covariance = 0
    for i in range(len(listx)):
        covariance += 32 - bin(listx[i] ^ listy[i]).count("1")
    covariance = covariance / float(len(listx))
    return covariance / 32
    # return cross correlation, with listy offset from listx


def cross_correlation(listx, listy, offset):
    if offset > 0:
        listx = listx[offset:]
        listy = listy[: len(listx)]
    elif offset < 0:
        offset = -offset
        listy = listy[offset:]
        listx = listx[: len(listy)]
    if min(len(listx), len(listy)) < min_overlap:
        # Error checking in main program should prevent us from ever being
        # able to get here.
        return
    # raise Exception('Overlap too small: %i' % min(len(listx), len(listy)))
    return correlation(listx, listy)
    # cross correlate listx and listy with offsets from -span to span


def compare(listx, listy, span, step):
    if span > min(len(listx), len(listy)):
        # Error checking in main program should prevent us from ever being
        # able to get here.
        raise Exception(
            "span >= sample size: %i >= %i\n" % (span, min(len(listx), len(listy)))
            + "Reduce span, reduce crop or increase sample_time."
        )

    corr_xy = []
    for offset in numpy.arange(-span, span + 1, step):
        corr_xy.append(cross_correlation(listx, listy, offset))
    return corr_xy
    # return index of maximum value in list


def max_index(listx):
    max_index = 0
    max_value = listx[0]
    for i, value in enumerate(listx):
        if value > max_value:
            max_value = value
            max_index = i
    return max_index


def get_max_corr(corr, source, target):
    max_corr_index = max_index(corr)
    max_corr_offset = -span + max_corr_index * step
    # print("max_corr_index = ", max_corr_index, "max_corr_offset = ", max_corr_offset)
    # report matches
    if corr[max_corr_index] > threshold:
        print(
            (
                "MATCH with correlation of %.4f at offset %i"
                % (corr[max_corr_index], max_corr_offset)
            )
        )
    else:
        print(
            (
                "NO MATCH (Correlation: %.4f at offset %i)"
                % (corr[max_corr_index], max_corr_offset)
            )
        )


def correlate(source, target):
    fingerprint_source = calculate_fingerprints(source)
    fingerprint_target = calculate_fingerprints(target)
    corr = compare(fingerprint_source, fingerprint_target, span, step)
    max_corr_offset = get_max_corr(corr, source, target)
    print(max_corr_offset)


if __name__ == "__main__":
    correlate(sys.argv[1], sys.argv[2])
