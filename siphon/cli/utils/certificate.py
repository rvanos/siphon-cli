import os
import re
import requests
import shutil
import subprocess
from datetime import datetime
from siphon.cli.utils.system import make_temp_dir

WWDR_CERT_URL = 'https://developer.apple.com/certificationauthority/' \
                'AppleWWDRCA.cer'

# Wrappers for keychain certificate operations
def valid_wwdr_cert_installed():
    cmd = ['security', 'find-certificate', '-p', '-a', '-Z', '-c',
           'Apple Worldwide Developer Relations Certification Authority']
    result = subprocess.check_output(cmd).decode('utf-8')
    cert_hash_pairs = re.findall('SHA-1 hash: [\s\w\+\\\/\=-]*-----END' \
                       ' CERTIFICATE-----', result)

    valid_certs = []
    for cert_hash in cert_hash_pairs:
        c = re.search('(?P<cert>-----BEGIN CERTIFICATE--' \
                      '---[\s\w\+\\\/\=]*-----END' \
                      ' CERTIFICATE-----)', cert_hash)
        c_hash = re.search('SHA-1 hash: (?P<hash>[\w]*)', cert_hash)
        echo = subprocess.Popen(['echo', c.group('cert')],
                                stdout=subprocess.PIPE)
        openssl = subprocess.Popen(['openssl', 'x509', '-text'],
                  stdin=echo.stdout, stdout=subprocess.PIPE)
        echo.stdout.close()
        processed = openssl.communicate()[0].decode('utf-8')
        echo.wait()
        expiry_date = re.search('Not After : (?P<month>[A-Z][a-z]{2}) ' \
                                '\s*(?P<day>[0-9]+)' \
                                ' (?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2}) ' \
                                '(?P<year>[0-9]{4}) (?P<timezone>[\w]+)',
                                processed)
        month = expiry_date.group('month')
        day = expiry_date.group('day')
        date_string = '%s %s %s %s' % (month, day,
                                    expiry_date.group('time'),
                                    expiry_date.group('year'))
        dt = datetime.strptime(date_string, "%b %d %H:%M:%S %Y")
        now = datetime.now()
        if (now < dt):
            valid_certs.append(c_hash.group('hash'))
    if valid_certs:
        return True
    else:
        return False

def add_wwdr_cert():
    response = requests.get(WWDR_CERT_URL, stream=True)
    with make_temp_dir() as tmp:
        out = os.path.join(tmp, 'AppleWWDRCA.cer')
        with open(out, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        cmd = ['security', 'add-certificates', out]
        subprocess.call(cmd)
