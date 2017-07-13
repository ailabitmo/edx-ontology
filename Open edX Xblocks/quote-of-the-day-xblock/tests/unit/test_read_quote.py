from __future__ import absolute_import, unicode_literals
import mock
import pytest

from quote_of_the_day.read_quote import read_quote, API_URL


def _json_request_mock(payload):
    request_mock = mock.Mock()
    request_mock.json.return_value = payload
    return request_mock


def test_read_quote_random():
    with mock.patch("quote_of_the_day.read_quote.requests") as requests_mock:
        requests_mock.get.return_value = _json_request_mock({"quoteText": "test", "quoteAuthor": "me"})
        quote = read_quote()

        requests_mock.get.assert_called_once_with(API_URL, {"method": "getQuote", "format": "json", "lang": "en"})

        assert quote.author == "me"
        assert quote.text == "test"


@pytest.mark.parametrize(
    "quoteId",
    [(123), ("456"), (789)]
)
def test_read_quote_by_id(quoteId):
    with mock.patch("quote_of_the_day.read_quote.requests") as requests_mock:
        requests_mock.get.return_value = _json_request_mock({"quoteText": "Another quote", "quoteAuthor": "some guy"})
        quote = read_quote(quoteId)

        requests_mock.get.assert_called_once_with(
            API_URL,
            {"method": "getQuote", "format": "json", "lang": "en", "key": quoteId}
        )

        assert quote.author == "some guy"
        assert quote.text == "Another quote"
