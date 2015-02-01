import os, sqlite3
from drive_times.drive_time_client import DrivingInfo

try:
    from thread import get_ident
except ImportError:
    from dummy_thread import get_ident

class DriveTimeCache:

    _create = (
            'CREATE TABLE IF NOT EXISTS postcode_duration_cache '
            '('
            '  target_postcode TEXT,'
            '  postcode TEXT,'
            '  duration_secs INTEGER,'
            '  duration TEXT,'
            '  distance_metres INTEGER,'
            '  distance TEXT,'
            '  PRIMARY KEY (target_postcode, postcode)'
            ')'
    )

    _get = 'SELECT target_postcode, postcode, duration_secs, duration, distance_metres, distance FROM postcode_duration_cache WHERE target_postcode = ? AND postcode = ?'

    _set = 'INSERT OR REPLACE INTO postcode_duration_cache (target_postcode, postcode, duration_secs, duration, distance_metres, distance) VALUES (?, ?, ?, ?, ?, ?)'

    def __init__(self, cache_file="postcode_cache.db", cache_directory="../data"):
        self.cache_path = os.path.join(cache_directory, cache_file)

        self._connection_cache = {}
        with self._get_conn() as conn:
            conn.execute(self._create)

    def _get_conn(self):
        id = get_ident()
        if id not in self._connection_cache:
            self._connection_cache[id] = sqlite3.Connection(self.cache_path, timeout=60)
        return self._connection_cache[id]

    def get(self, target_postcode, postcode):
        with self._get_conn() as conn:
            cursor = conn.execute(self._get, (target_postcode, postcode))
            row = cursor.fetchone()
            if row:
                return DrivingInfo(*row, status='CACHED')
            else:
                return None

    def set(self, drivetime_info):
        with self._get_conn() as conn:
            conn.execute(self._set, drivetime_info[:6])

