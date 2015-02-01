import argparse
import csv
from drive_times.drive_time_cache import DriveTimeCache
from drive_times.drive_time_client import DriveTimeClient
import logging

def main(args):
    print args.target
    print args.input_file
    print args.output_file

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logging.getLogger("drive_times").addHandler(ch)

    postcodes = []
    with open(args.input_file, 'r') as input_postcodes:
        for line in input_postcodes.readlines():
            postcode = line.strip().replace(',', '').replace(" ", "").upper()
            if postcode:
                postcodes.append(postcode)

    cache = DriveTimeCache(cache_file=args.cache_file, cache_directory=args.cache_dir)
    client = DriveTimeClient(100, cache)
    results = client.get_drive_times(args.target, postcodes)

    with open(args.output_file, 'w') as output:
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(results.values())





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reads a file of postcodes and gives durations to a fixed postcode.')

    def uppercase_postcode(s):
        #TODO: maybe validate it's a valid postcode?
        return str(s).strip().replace(' ', '').upper()
    parser.add_argument(
        '-t',
        '--target',
        metavar='POSTCODE',
        type=uppercase_postcode,
        help='The target postcode',
        required=True,
    )

    parser.add_argument(
        '-i',
        '--input-file',
        metavar='FILE',
        type=str,
        help='A file containing postcodes, one per line.',
        required=True
    )

    parser.add_argument(
        '-o',
        '--output-file',
        metavar='FILE',
        type=str,
        help='A filename to save the result csv to.',
        required=True
    )

    parser.add_argument(
        '-d',
        '--cache-dir',
        metavar='DIR',
        type=str,
        help='The directory containing the postcode cache.',
        default='../data/'
    )

    parser.add_argument(
        '-c',
        '--cache-file',
        metavar='FILE',
        type=str,
        help='The filename of the postcode cache.',
        default='postcode_cache.db'
    )

    args = parser.parse_args()
    main(args)
