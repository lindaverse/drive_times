
  Feature: fetching drive times
    Scenario: fetching drive times multiple batches
      Given 10 postcodes and a batch size of 5
      when we get drive times
      then we only call Google twice
      and we cache the results

    Scenario: postcode not found
      Given an invalid postcode
      when we get drive times
      then the driving duration for the invalid postcode is None

    Scenario: fetching drive times that are already cached
      Given 10 cached postcodes and a batch size of 5
      when we get drive times
      then we will not call Google

    Scenario: fetching drive times when some postcodes are already cached
      Given 3 cached postcodes and 7 uncached postcodes with a batch size of 5
      when we get drive times
      then we call Google on only the uncached
      and we cache the missing results

    Scenario: exceed Google query limit
      Given 10 postcodes and a batch size of 5
      And the Google API requests limit has been exceeded
      when we get drive times
      then return None and don't cache



