from remote_signer import RemoteSigner


def lambda_handler(event, context):
    rs = RemoteSigner(event)
    return {'signature': rs.sign(event)}