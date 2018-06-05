import base64
import binascii


def lambda_handler(event, context):
    signature = ''
    if 'to-sign' in event:
        try:
            decoded = base64.b64decode(event['to-sign'])
        except binascii.Error:
            raise Exception('Payload is not base64-encoded.') from binascii.Error
        signature = decoded

        bytes = list(decoded)
        if bytes[0] != 0 and bytes[0] != 1:
            raise Exception('Invalid preamble.')

        # TODO: check block level is near current level
        # TODO: check block hasn't already been signed

    else:
        raise Exception('Invalid payload.')

    return {'signature': signature}
