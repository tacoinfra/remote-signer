from resigner import Resigner


def lambda_handler(event, context):
    rs = Resigner(event)
    signature = ''
    if rs.is_block() and rs.is_within_level_threshold():
        pass
    elif rs.is_endorsement():
        pass
    else:
        raise Exception('Invalid preamble.')
    return {'signature': signature}