import unittest
import base64

from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):
    def test_throws_on_invalid_payload(self):
        with self.assertRaisesRegex(Exception, 'Invalid payload.'):
            lambda_handler({'blah': 'blah'}, {})

    def test_throws_on_invalid_base64_encoding(self):
        with self.assertRaisesRegex(Exception, 'Payload is not base64-encoded.'):
            lambda_handler({'to-sign': 'bllasdkjgh'}, {})

    def test_throws_on_invalid_starting_bytes(self):
        with self.assertRaisesRegex(Exception, 'Invalid preamble.'):
            lambda_handler({'to-sign': 'SGVsbG8sIFdvcmxkIQo='}, {})

    def test_succeeds_with_valid_preamble(self):
        encoded = base64.b64encode(''.join(['\0', 'H', 'e', 'l', 'l', 'o']).encode('utf-8'))
        response = lambda_handler({'to-sign': encoded}, {})
        for key in response:
            self.assertEquals(key, 'signature')

if __name__ == '__main__':
    unittest.main()