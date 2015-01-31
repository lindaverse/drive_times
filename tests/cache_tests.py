import tempfile
import shutil
from nose.tools import eq_
from drive_times.drive_time_cache import DriveTimeCache


def test_insert_value_and_retreive():
    temp_dir = tempfile.mkdtemp()
    try:
        cache = DriveTimeCache(cache_directory=temp_dir)
        cache.set("EH7 5EZ", "FK8 2DT", "500 miles")
        eq_(cache.get("EH7 5EZ", "FK8 2DT"), "500 miles")
    finally:
        shutil.rmtree(temp_dir)

def test_retreive_missing_value():
    temp_dir = tempfile.mkdtemp()
    try:
        cache = DriveTimeCache(cache_directory=temp_dir)
        eq_(cache.get("EH7 5EZ", "FK8 2DT"), None)
    finally:
        shutil.rmtree(temp_dir)


