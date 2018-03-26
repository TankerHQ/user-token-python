import base64
import json

import tankersdk.crypto
import tankersdk.usertoken

import pytest
from tankersdk.crypto import BLOCK_HASH_SIZE, CHECK_HASH_BLOCK_SIZE, USER_SECRET_SIZE
from tankersdk.test.helpers import corrupt_buffer


TRUSTCHAIN_ID = b"AzES0aJwDCej9bQVY9AUMZBCLdX0msEc/TJ4DOhZaQs="
TRUSTCHAIN_PUBLIC_KEY = b"dOeLBpHz2IF37UQkS36sXomqEcEAjSyCsXZ7irn9UQA="
TRUSTCHAIN_PRIVATE_KEY = b"cBAq6A00rRNVTHicxNHdDFuq6LNUo6gAz58oKqy9CGd054sGkfPYgXftRCRLfqxeiaoRwQCNLIKxdnuKuf1RAA=="


def parse_b64_token(b64_token):
    json_token = base64.b64decode(b64_token)
    token = json.loads(json_token.decode())
    return token


def generate_test_token():
    user_id = "guido@tanker.io"
    b64_token = tankersdk.usertoken.generate_user_token(
        TRUSTCHAIN_ID,
        TRUSTCHAIN_PRIVATE_KEY,
        user_id
    )
    token = parse_b64_token(b64_token)
    return token


def test_generate_token_happy():
    token = generate_test_token()
    delegation_signature = base64.b64decode(token["delegation_signature"])

    check_user_secret(token)
    check_signature(token, delegation_signature)


def test_generate_token_invalid_signature():
    token = generate_test_token()
    delegation_signature = base64.b64decode(token["delegation_signature"])
    invalid_signature = corrupt_buffer(delegation_signature)

    with pytest.raises(tankersdk.crypto.InvalidSignature):
        check_signature(token, invalid_signature)


def check_user_secret(token):
    hashed_user_id = base64.b64decode(token["user_id"])
    user_secret = base64.b64decode(token["user_secret"])

    assert len(hashed_user_id) == BLOCK_HASH_SIZE
    assert len(user_secret) == USER_SECRET_SIZE
    to_hash = user_secret[:-1] + hashed_user_id
    control = tankersdk.crypto.generichash(to_hash, size=CHECK_HASH_BLOCK_SIZE)
    assert user_secret[-1] == control[0]


def check_signature(token, signature):
    e_pub_key = base64.b64decode(token["ephemeral_public_signature_key"])
    user_id = base64.b64decode(token["user_id"])
    signed_data = e_pub_key + user_id
    verify_key = base64.b64decode(TRUSTCHAIN_PUBLIC_KEY)
    tankersdk.crypto.verify_sign_detached(signed_data, signature, verify_key)