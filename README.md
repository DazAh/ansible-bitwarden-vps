# ansible-bitwarden-vps
Personal bitwarden_rs vps playbook hacky!.


Uses B2 and Mega to backup bitwarden attachments and database (SQLITE).
Airsonic proxy can be toggled on/off in vars file. Tested on CentOS 8.

    ansible-playbook site.yml -k
