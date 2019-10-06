#!/usr/bin/env python3

import argparse
import hashlib
import hmac
import json
import logging
import os
import sys
import uuid

from base64 import encodebytes
from datetime import datetime
from urllib import error
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


class AliDDNS:
    def __init__(self, domain):
        self.domain = domain
        self.accesskey = os.environ.get('ALIDDNS_ACCESSKEYID', '')
        self.secret = os.environ.get('ALIDDNS_SECRET', '')
        self.api_url = 'http://alidns.aliyuncs.com/'
        self.sign_method = 'HMAC-SHA1'

    def _bytes(self, s, encoding='utf-8'):
        return bytes(s, encoding=encoding)

    def _sign(self, str_to_sign):
        key = self._bytes(self.secret + '&')
        msg = self._bytes('GET&%2F&{}'.format(str_to_sign))
        logger.debug('key: {}'.format(key))
        logger.debug('msg: {}'.format(msg))
        h = hmac.new(key, msg, hashlib.sha1)
        return str(encodebytes(h.digest()).strip(), encoding='utf-8')

    def _make_url(self, **kwargs):
        default_params = {
            'Version': '2015-01-09',
            'Format': 'json',
            'AccessKeyId': self.accesskey,
            'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'SignatureMethod': self.sign_method,
            'SignatureNonce': str(uuid.uuid4()),
            'SignatureVersion': '1.0',
        }
        default_params.update(kwargs)
        params = urlencode(sorted(default_params.items()))
        str_to_sign = quote(params)
        return '{}?{}&Signature={}'.format(
            self.api_url, params, self._sign(str_to_sign))

    def _request(self, action, **kwargs):
        url = self._make_url(Action=action, **kwargs)
        logging.debug('URL: {}'.format(url))
        req = Request(url)
        req.add_header('Accept', 'application/json')
        try:
            with urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except error.HTTPError as e:
            logger.error('Failed to call {} : {} {} {}'.format(
                action, e.code, e.reason, e.fp.read()))
            sys.exit(1)
        except Exception as e:
            logger.error('Unexpected error: {}'.format(e))
            sys.exit(1)

    def get_records_list(self):
        args = {
            'DomainName': self.domain
        }
        data = self._request('DescribeDomainRecords', **args)
        return data['DomainRecords']['Record']

    def get_record(self, rr, rtype):
        records = self.get_records_list()
        for r in records:
            if r['RR'] == rr and r['Type'] == rtype:
                logger.debug('Found record: {}'.format(r))
                return r
        return None

    def get_ip(self):
        urls = ['http://whatismyip.akamai.com', 'https://api.ipify.org']
        for url in urls:
            logger.debug('Getting public IP via {}'.format(url))
            try:
                with urlopen(url, timeout=10) as resp:
                    return resp.read().decode("utf-8")
            except Exception as e:
                logger.debug('Get IP from {} failed: {}'.format(url, e))
        logger.error('Failed to get public IP')
        sys.exit(1)

    def add_record(self, rr, rtype, value):
        logger.info('Adding new record: RR={} Type={}'.format(rr, rtype))

    def update_record(self, record_id, rr, rtype, value):
        logger.info('Updating record: ID={} RR={} Type={} Value={}'.format(
            record_id, rr, rtype, value))
        args = {
            'RecordId': record_id,
            'RR': rr,
            'Type': rtype,
            'Value': value
        }
        self._request('UpdateDomainRecord', **args)
        logger.info('Record updated: ID={} RR={} Type={} Value={}'.format(
            record_id, rr, rtype, value))

    def refresh(self, rr, rtype):
        record = self.get_record(rr, rtype)
        ip = self.get_ip()
        if record:
            if ip != record['Value']:
                self.update_record(record['RecordId'], rr, rtype, ip)
            else:
                logger.info('Record is up to date')
        else:
            self.add_record(rr, rtype, ip)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('domain', help='Domain name, e.g. example.com')
    parser.add_argument(
        'rr',
        help=('For main domain example.com, rr should be @; '
              'for subdomain abc.example.com, rr should be abc'))
    parser.add_argument('--type', default='A', help='DNS record type')
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Print more logs for debugging')
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    ddns = AliDDNS(args.domain)
    ddns.refresh(args.rr, args.type)


if __name__ == '__main__':
    main()
