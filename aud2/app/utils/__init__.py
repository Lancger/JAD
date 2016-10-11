#coding=utf-8
import os, requests, json, zipfile, re, base64
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
# import config.default
import config.default
from config import default



# 对数据进行签名
def data_sign(data):
    pri_key = RSA.importKey(open(config.PRI_KEY_PATH))
    data_sha = SHA.new(data)
    signer = PKCS1_v1_5.new(pri_key)
    signature = signer.sign(data_sha)
    signed_data = base64.b64encode(signature)
    return signed_data


# 对数据进行验证签名
def data_check_sign(data, signed_data, pub_key_name):

    # print config.default.PUB_KEY_DIR
    # pub_key_path = os.path.join(config.default.PUB_KEY_DIR, '%s.pub' % pub_key_name)
    #print default.PUB_KEY_DIR
    pub_key_path = os.path.join(config.default.Config.PUB_KEY_DIR, '%s.pub' % pub_key_name)
    print "==" * 20
    print pub_key_path
    if not os.path.isfile(pub_key_path):
        return False
    pub_key = RSA.importKey(open(pub_key_path))
    data_sha = SHA.new(data)
    verifier = PKCS1_v1_5.new(pub_key)
    print pub_key
    print data_sha
    print verifier
    print verifier.verify(data_sha, base64.b64decode(signed_data))
    return verifier.verify(data_sha, base64.b64decode(signed_data))


# 数据签名并POST到API接口
def post_to_api_sign(url, data, data_key_name='sign_data', sign_key_name='sign'):
    '''post_to_api_sign('http://xxx', '{"status": 1}')'''

    if not url:
        return False
    sign = data_sign(data)
    try:
        json_loads_data = json.loads(data)
    except:
        json_loads_data = data
    post_data = {data_key_name: json_loads_data, sign_key_name: sign}
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    try:
        post_return = requests.post(url, data=json.dumps(post_data), headers=headers, verify=False)
        post_result = post_return.json()
    except:
        return False
    return post_result
