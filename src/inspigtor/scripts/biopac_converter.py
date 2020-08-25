#!/usr/bin/env python

import argparse
import collections
import datetime
import logging
import os
import pprint
import re
import sys

import numpy as np

import bioread


class UnmatchingPropertySetError(Exception):
    """Error raised when a mismatch is found between properties or if no valid properties is found.
    """


def glob_re(pattern, strings):
    """Filter a set of path using a given pattern.

    Returns:
        filter object: the filtered paths
    """

    return filter(re.compile(pattern).match, strings)


def check_biopac_properties(biopac_dir, acq_files, props):
    """Check that a list of properties are valid and can be treated alltogether.

    Args:
        biopac_dir (str): the biopac base directory which contains the biopac files
        acq_files (list of str): the biopac acq files
        props (list of str): the list of properties to check

    Returns:
        list of str: the list of valid properties
    """

    first = True
    for data_file in acq_files:

        # Reading the headers is enough for getting general informations about the properties
        data = bioread.read_headers(os.path.join(biopac_dir, data_file))

        if props is None:
            current_props = set(data.named_channels.keys())
        else:
            current_props = set(data.named_channels.keys()).intersection(props)

        if not current_props:
            raise UnmatchingPropertySetError('No valid properties selected for output')

        # properties must have the same sampling rate
        if len(set([data.named_channels[v].samples_per_second for v in current_props])) != 1:
            raise UnmatchingPropertySetError('Different samplings found for the properties selected for output')

        # properties must have the same points count
        if len(set([data.named_channels[v].point_count for v in current_props])) != 1:
            raise UnmatchingPropertySetError('Different points counts found for the properties selected for output')

        if first:
            initial_props = current_props
            first = False
        else:
            if initial_props != current_props:
                raise UnmatchingPropertySetError('The data files do not have matching property selected for output')

    props = list(initial_props)

    return props


def subsample(biopac_dir, acq_files, props, subsample_time):
    """Performs a subsampling on a set of of biopac acq files.

    Args:
        biopac_dir (str): the biopac base directory which contains the biopac files
        acq_files (list of str): the biopac acq files
        props (list of str): the list of properties to subsample
        subsampling_time (float): the subsampling time in seconds

    Returns:
        list: a nested list whose elements are of the form (time,subsampled prop 1, subsampled prop 2 ...)
    """

    props = check_biopac_properties(biopac_dir, acq_files, props)

    # The first nested list will contain the times, while the others will contain the subsampled data for each property
    sampled_data = [[]]
    for i in range(len(props)):
        sampled_data.append([])

    # Loop over the data files
    for data_file in acq_files:

        logging.info('Processing {} file ... '.format(data_file))

        # Fetch the starting time from the filename as stated y convention of biopac files
        starting_time = re.findall(r'.*[0-9]{4}-[0-9]{2}-[0-9]{2}T([0-9]{2}_[0-9]{2}_[0-9]{2}).acq', data_file)[0]

        starting_time = datetime.datetime.strptime(starting_time, '%H_%M_%S')

        # Actually read the data
        data = bioread.read_file(os.path.join(biopac_dir, data_file))

        samples_per_second = data.named_channels[props[0]].samples_per_second

        n_points_per_block = subsample_time*samples_per_second

        if not n_points_per_block.is_integer():
            subsample_time = int(n_points_per_block)/samples_per_second
            logging.warning('The sampling time does not allow the gathering of n values where n is an integer. Will use a sampling time of {} instead.'.format(subsample_time))

        n_points_per_block = int(subsample_time*samples_per_second)
        n_points = data.named_channels[props[0]].point_count
        n_blocks = int(n_points/n_points_per_block)

        #  Build the time axis
        for i in range(n_blocks):

            time = str(starting_time + datetime.timedelta(seconds=i*subsample_time)).split(' ')[1]
            sampled_data[0].append(time)

        for idx, prop in enumerate(props):

            channel = data.named_channels[prop]

            # Performs the subsampling for the running property
            for i in range(n_blocks):

                start = i*n_points_per_block
                end = (i+1)*n_points_per_block
                average_data = np.mean(channel.data[start:end])
                sampled_data[idx+1].append(average_data)

    # Transpose the subsampled_data nested lists
    sampled_data = list(zip(*sampled_data))

    return props, sampled_data


def find_biopac_directories(root_dir):
    """Find all directories storing valid biopac acq files.

    To be valid an acq filename must have the following format .*[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}_[0-9]{2}_[0-9]{2}.acq.

    Returns:
        list of str: the biopac directories

    """

    biopac_dirs = []
    for root, dirs, _ in os.walk(root_dir):
        if dirs:
            continue
        biopac_files = sorted(glob_re(r'.*[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}_[0-9]{2}_[0-9]{2}.acq', os.listdir(root)))
        if not biopac_files:
            continue
        else:
            biopac_dirs.append(root)

    return sorted(biopac_dirs)


def parse_args():
    """Returns the argument namespace after command-line parsing.
    """

    parser = argparse.ArgumentParser(description="This is biopac_converter: a program for converting from biopac acq files to PiCCO2 csv files")
    parser.add_argument("--sampling-time", "-s", dest="sampling_time", default="10", help="sampling time (in seconds)")
    parser.add_argument("--properties", "-p", dest="properties", nargs="*", default=None, help="selected properties")
    parser.add_argument("--root", "-r", dest="root_dir", help="root directories")
    parser.add_argument("--info", "-i", dest="info", help="get information about a given acq file")
    args = parser.parse_args()

    return args


def biopac_info(biopac_file):
    """Print information about the properties stored in a biopac acq file.

    Args:
        biopac_file (str): the biopac file to scan
    """

    header = bioread.read_headers(biopac_file)
    pprint.pprint(header.named_channels)


def main():

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    args = parse_args()

    if args.info is not None:
        biopac_info(args.info)
        sys.exit(0)

    root_dir = args.root_dir

    subsample_time = int(args.sampling_time)

    properties = args.properties

    biopac_dirs = find_biopac_directories(root_dir)

    for biopac_dir in biopac_dirs:

        logging.info('Scanning {} directory'.format(biopac_dir))

        data_files = sorted(glob_re(r'.*[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}_[0-9]{2}_[0-9]{2}.acq', os.listdir(biopac_dir)))

        properties, sampled_data = subsample(biopac_dir, data_files, properties, subsample_time)

        biopac_csv = open(os.path.join(biopac_dir, 'biopac.csv'), 'w')
        biopac_csv.write('PiCCO2;C108500156;V3.1.0.8 A\n')
        biopac_csv.write('Weight;Height;Age;Gender;category;TD cath;BSA;PBW;PBSA;t_initial;t_final\n')
        biopac_csv.write(';;;;;;;;;;\n')
        biopac_csv.write('ID;Name\n')
        biopac_csv.write(';\n')
        biopac_csv.write(';\n')
        biopac_csv.write(';\n')

        csv_props = ['Time'] + properties
        biopac_csv.write(';'.join(csv_props))
        biopac_csv.write('\n')

        # Write the subsampled data to the csv output file
        for d in sampled_data:
            biopac_csv.write(';'.join([str(v) for v in d]))
            biopac_csv.write('\n')

        biopac_csv.close()


if __name__ == '__main__':
    main()
