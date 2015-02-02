from time import sleep
import collections
import requests
import logging

logger = logging.getLogger("drive_times")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

DrivingInfo = collections.namedtuple(
    'DriveTimeInfo',
    ['target_postcode', 'postcode', 'duration_secs', 'duration_txt', 'distance_metres', 'distance_txt', 'status']
)

def empty_drive_info(target_postcode, postcode, status):
    return DrivingInfo(target_postcode, postcode, None, None, None, None, status)

class DriveTimeClient:
    URL = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={postcodes}&destinations={target_postcode}"

    def __init__(self, batch_size, drive_time_cache, get=requests.get):
        self.cache = drive_time_cache
        self.batch_size = batch_size
        self.get = get
        self.batches_over_query_limit = 0
        self.max_attempts = 3

    def get_drive_times(self, target_postcode, postcodes):
        results = {}
        uncached = []

        for postcode in postcodes:
            cached = self.cache.get(target_postcode, postcode)
            if cached:
                results[postcode] = cached
            else:
                uncached.append(postcode)


        for batch in self._batch(uncached):
            results.update(self._get_batch(target_postcode, batch))
        return results

    def _get_batch(self, target_postcode, postcodes):
        url = self.URL.format(target_postcode=target_postcode, postcodes='|'.join(postcodes))
        results = {}
        for postcode in postcodes:
            results[postcode] = empty_drive_info(target_postcode, postcode, "NOT_FETCHED")

        if self.batches_over_query_limit > 0:
            logger.warn('Skipping batch {} because we have hit our limit.'.format(','.join(postcodes)))
            return results


        attempts = 0
        while True:
            logger.debug('Fetching url {}'.format(url))
            response_json = self.get(url).json()

            response_status = response_json['status']
            logger.info('status = {} for url {}'.format(response_status, url))
            if response_status == 'OK':
                for postcode, row in zip(postcodes, response_json['rows']):
                    status = row['elements'][0]['status']
                    if status == 'OK':
                        drive_info = DrivingInfo(
                            target_postcode,
                            postcode,
                            row['elements'][0]['duration']['value'],
                            row['elements'][0]['duration']['text'],
                            row['elements'][0]['distance']['value'],
                            row['elements'][0]['distance']['text'],
                            status
                        )
                        results[postcode] = drive_info
                        self.cache.set(drive_info)
                    elif status in ['NOT_FOUND', 'ZERO_RESULTS']:
                        results[postcode] = empty_drive_info(target_postcode, postcode, status)
                        self.cache.set(empty_drive_info(target_postcode, postcode, status))
                    else:
                        results[postcode] = empty_drive_info(target_postcode, postcode, status)


                break
            elif response_status == "OVER_QUERY_LIMIT":
                if attempts >= self.max_attempts:
                    self.batches_over_query_limit += 1
                    logger.warn('Exceeded max attempts, giving up on this batch.')
                    break

                attempts += 1

                sleep_time = (attempts * 5) + 10

                logger.info('Over request limit, sleeping {} seconds! Attempt {} of {}.'.format(sleep_time, attempts, self.max_attempts))
                sleep(sleep_time)
                continue
            else:
                for postcode in postcodes:
                    results[postcode] = empty_drive_info(target_postcode, postcode, response_status)
        return results

    def _batch(self, postcodes):
        for i in xrange(0, len(postcodes), self.batch_size):
            yield postcodes[i:i+self.batch_size]






