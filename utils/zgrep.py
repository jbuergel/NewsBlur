#!/usr/bin/env python

from optparse import OptionParser
import os
import select
import subprocess
import sys
import yaml


IGNORE_HOSTS = [
    'push',
]

def main(role="app", role2="dev", command=None, path=None):
    streams = list()
    if not path:
        path = "/srv/newsblur/logs/newsblur.log"
    if not command:
        command = "tail -f"
    hosts_path = os.path.expanduser(os.path.join('../secrets-newsblur/configs/hosts.yml'))
    hosts = yaml.load(open(hosts_path))
    
    for r in [role, role2]:
        if isinstance(hosts[r], dict):
            hosts[r] = ["%s:%s" % (hosts[r][k][-1], k) for k in hosts[r].keys()]
    
    for hostname in set(hosts[role] + hosts[role2]):
        if any(h in hostname for h in IGNORE_HOSTS): continue
        if ':' in hostname:
            hostname, address = hostname.split(':', 1)
        else:
            address = hostname
        if 'ec2' in hostname:
            s = subprocess.Popen(["ssh", "-i", os.path.expanduser("~/.ec2/sclay.pem"), 
                                  address, "%s %s" % (command, path)], stdout=subprocess.PIPE)
        else:
            s = subprocess.Popen(["ssh", address, "%s %s" % (command, path)], stdout=subprocess.PIPE)
        s.name = hostname
        streams.append(s)

    try:
        i = 0
        while True:
            i += 1
            r, _, _ = select.select(
                [stream.stdout.fileno() for stream in streams], [], [])
            for fileno in r:
                for stream in streams:
                    if stream.stdout.fileno() != fileno:
                        continue
                    data = os.read(fileno, 4096)
                    if not data:
                        streams.remove(stream)
                        break
                    combination_message = "%s" % (data)
                    sys.stdout.write(combination_message)
                    break
            if i > 1000:
                break
    except KeyboardInterrupt:
        print " --- End of Logging ---"


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--find", dest="find")
    parser.add_option("-p", "--path", dest="path")
    (options, args) = parser.parse_args()

    path = options.path
    find = options.find
    command = "zgrep \"%s\"" % find
    main(role="app", role2="dev", command=command, path=path)