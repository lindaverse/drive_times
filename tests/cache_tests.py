import tempfile
import shutil
from nose.tools import eq_
from drive_times.drive_time_cache import DriveTimeCache
from drive_times.drive_time_client import DrivingInfo


def test_insert_value_and_retreive():
    temp_dir = tempfile.mkdtemp()
    try:
        cache = DriveTimeCache(cache_directory=temp_dir)
        value = DrivingInfo("EH75EZ", "FK82DT", 1234, "24 hours", 4321, "500 miles", "OK")
        cache.set(value)
        eq_(cache.get("EH75EZ", "FK82DT"), DrivingInfo(*value[:6], status="CACHED"))
    finally:
        shutil.rmtree(temp_dir)

def test_retreive_missing_value():
    temp_dir = tempfile.mkdtemp()
    try:
        cache = DriveTimeCache(cache_directory=temp_dir)
        eq_(cache.get("EH7 5EZ", "FK8 2DT"), None)
    finally:
        shutil.rmtree(temp_dir)


