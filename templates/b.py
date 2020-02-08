#!/usr/bin/python3
# Author: DL

import http.client
import urllib
import sqlite3
import subprocess
import tarfile
import os
import sys
from datetime import date
from mega import Mega  # mega.py
from b2sdk.v1 import *  # b2 sdk

currenttime = date.today()
important = [
            "/var/local/{{ podman_user }}/data/bitwarden.db",
            "/var/local/{{ podman_user }}/data/attachments",
            "/var/local/{{ podman_user }}/data/backup.db"]

tarname = "/tmp/bw_backup-" + currenttime.strftime("%d%m%Y") + '.tar.gz'
tarname1 = "bw_backup-" + currenttime.strftime("%d%m%Y") + '.tar.gz'
mega = Mega()
#############
# B2 SDK
info = InMemoryAccountInfo()
b2_api = B2Api(info)
application_key_id = '{{ b2_application_key_id }}'
application_key = '{{ b2_application }}'
b2_api.authorize_account("production", application_key_id, application_key)


# Send http response to pushover api when backup completes.
def pushover(message):
    try:
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": "{{ pushover_token }}",
            "user": "{{ pushover_user }}",
            "message": message,
        }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()
    except:
        sys.exit("pushover notification request failed")

# def progress(status, remaining, total): #Print sqlite copy progress.
#     print(f'Copied {total-remaining} of {total} pages...')

# def databaseBackup(): #Copy sqlite3 db to another file (safely)
#     con = sqlite3.connect(important[0])
#     bck = sqlite3.connect(important[2])
#     with bck:
#         con.backup(bck, pages=1, progress=None)
#     bck.close()
#     con.close()

def cleanup():
    # Remove copied database as its include in the tar.
    try:
        os.remove(tarname)
        os.remove(important[2])
    except OSError:
        pass


# Create tar file of important files to backup.
def tarCreate():
    try:
        archive = tarfile.open(tarname, mode='w:gz') 
        for name in [important[1], important[2]]:
            fname = os.path.basename(name)  # only filename (no path)
            archive.add(name, fname)
        archive.close()
        print(tarname + " Created")
    except:
        pushover("Could not create tar")
        cleanup()
        sys.exit("Could not create tar")


def b2_upload():
    file_info = {'bw': 'important'}

    try:
        bucket = b2_api.get_bucket_by_name("{{ b2_bucket }}")
        bucket.upload_local_file(
            local_file=tarname,
            file_name=tarname1,
            file_infos=file_info,
        )
    except:
        pushover("B2 upload failed")
        cleanup()
        sys.exit("B2 upload failed")

# Workaround for py3.6 due to no sql.backup lib.
# Once on Cent8.2 not needed.
subprocess.run(['sqlite3', important[0], '.backup ' + important[2]])
# databaseBackup()
tarCreate()
b2_upload()
try:
    m = mega.login(
        "{{ mega_user }}", r'{{ mega_pass }}')
    m.upload(tarname)
except:
    print("Upload to mega failed.")
    pass
cleanup()
