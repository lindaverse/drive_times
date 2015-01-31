from behave import *
from faker import Factory
import mock
from drive_times.drive_time_client import DriveTimeClient
from mock import Mock, call

def random_postcode(number_of_postcodes):
    fake = Factory.create('en_GB')
    return [fake.postcode() for n in range(number_of_postcodes)]

def fake_google_response(num_postcodes, invalid=False):
    mock_response = Mock()
    mock_response.json.return_value = {
        'rows': [fake_google_response_row(invalid) for _ in range(num_postcodes)],
        'status': 'OK'
    }
    return mock_response

def fake_google_response_row(invalid=False):
    return {
        'elements': [
            {
                'duration': {
                    'text': '500 miles'
                },
                'status': 'OK' if not invalid else 'NOT_FOUND'
            }
        ]
    }


@Given('10 postcodes and a batch size of 5')
@mock.patch('requests.get', return_value=fake_google_response(5))
def step_impl(context, mock_requests):
    context.mock_requests = mock_requests
    context.target_postcode = "EH7 5EZ"
    context.postcodes = random_postcode(10)
    context.drive_time_cache = Mock()
    context.drive_time_cache.get.return_value = None
    context.client = DriveTimeClient(batch_size=5, drive_time_cache=context.drive_time_cache, get=context.mock_requests)


@When('we get drive times')
def step_impl(context):
    context.return_value = context.client.get_drive_times(context.target_postcode, context.postcodes)


@Then('we only call Google twice')
def step_impl(context):
    assert context.mock_requests.call_count == 2, "requests was called {} times should have been 2".format(context.mock_requests.call_count)


@Then('we cache the results')
def step_impl(context):
    for postcode in context.postcodes:
        context.drive_time_cache.set.assert_any_call(context.target_postcode, postcode, '500 miles')

@Given('an invalid postcode')
@mock.patch('requests.get', return_value=fake_google_response(1, invalid=True))
def step_impl(context, mock_requests):
    context.mock_requests = mock_requests
    context.target_postcode = "EH7 5EZ"
    context.postcodes = random_postcode(1)
    context.drive_time_cache = Mock()
    context.drive_time_cache.get.return_value = None
    context.client = DriveTimeClient(batch_size=5, drive_time_cache=context.drive_time_cache, get=context.mock_requests)

@Then('the driving duration for the invalid postcode is None')
def step_impl(context):
    assert context.return_value[context.postcodes[0]] == None

@Given('10 cached postcodes and a batch size of 5')
@mock.patch('requests.get')
def step_impl(context, mock_requests):
    context.mock_requests = mock_requests
    context.postcodes = random_postcode(10)
    context.target_postcode = "EH7 5EZ"
    context.drive_time_cache = Mock()
    context.drive_time_cache.get.side_effects = context.postcodes

    context.client = DriveTimeClient(batch_size=5, drive_time_cache=context.drive_time_cache, get=mock_requests)


@Then('we will not call Google')
def step_impl(context):
    assert context.mock_requests.call_count == 0, "requests was called {} times, should have been 0".format(context.mock_requests.call_count)




@Given('3 cached postcodes and 7 uncached postcodes with a batch size of 5')
@mock.patch('requests.get', side_effect=[fake_google_response(5), fake_google_response(2)])
def step_impl(context, mock_requests):
    context.mock_requests = mock_requests
    context.postcodes = random_postcode(10)
    context.target_postcode = "EH7 5EZ"
    context.drive_time_cache = Mock()
    context.drive_time_cache.get.side_effect = [None, None, '500 miles', None, '500 miles', None, '500 miles', None, None, None]

    context.client = DriveTimeClient(batch_size=5, drive_time_cache=context.drive_time_cache, get=mock_requests)

@Then('we call Google on only the uncached')
def step_impl(context):
    context.expected_postcodes = [
        context.postcodes[0],
        context.postcodes[1],
        context.postcodes[3],
        context.postcodes[5],
        context.postcodes[7],
        context.postcodes[8],
        context.postcodes[9],
    ]
    expected_url_one = DriveTimeClient.URL.format(target_postcode=context.target_postcode, postcodes='|'.join(context.expected_postcodes[:5]))
    expected_url_two = DriveTimeClient.URL.format(target_postcode=context.target_postcode, postcodes='|'.join(context.expected_postcodes[5:]))
    context.mock_requests.assert_has_calls([call(expected_url_one), call(expected_url_two)])

@Then('we cache the missing results')
def step_impl(context):
    for postcode in context.expected_postcodes:
        context.drive_time_cache.set.assert_any_call(context.target_postcode, postcode, '500 miles')


@Given('the Google API requests limit has been exceeded')
def step_impl(context):
    mock_response = Mock()
    mock_response.json.return_value = {'status': 'OVER_QUERY_LIMIT'}
    context.mock_requests.return_value = mock_response

@Then("return None and don't cache")
def setp_impl(context):
    assert context.drive_time_cache.set.call_count == 0
    for postcode in context.postcodes:
        assert context.return_value[postcode] == None

