from time import sleep
import requests
import logging

logger = logging.getLogger("drive_times")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

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

        if self.batches_over_query_limit > 0:
            logger.warn('Skipping batch {} because we have hit our limit.'.format(','.join(postcodes)))
            for postcode in postcodes:
                results[postcode] = None
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
                        duration = row['elements'][0]['duration']['text']
                        results[postcode] = duration
                        self.cache.set(target_postcode, postcode, duration)
                    elif status == 'NOT_FOUND':
                        results[postcode] = None
                        self.cache.set(target_postcode, postcode, None)
                    else:
                        results[postcode] = None
                break
            elif response_status == "OVER_QUERY_LIMIT":
                if attempts >= self.max_attempts:
                    self.batches_over_query_limit += 1
                    logger.warn('Exceeded max attempts, giving up on this batch.')
                    for postcode in postcodes:
                        results[postcode] = None
                    break

                attempts += 1

                sleep_time = (attempts * 5) + 10

                logger.info('Over request limit, sleeping {} seconds! Attempt {} of {}.'.format(sleep_time, attempts, self.max_attempts))
                sleep(sleep_time)
                continue
            else:
                for postcode in postcodes:
                    results[postcode] = None
                break
        return results

    def _batch(self, postcodes):
        for i in xrange(0, len(postcodes), self.batch_size):
            yield postcodes[i:i+self.batch_size]






