#!/usr/bin/env python
#
# Based on a script by Pablo Iranzo Gomez (Pablo.Iranzo@redhat.com)
#
# Description: Script for creating VM's
#
# Requires rhevm-sdk to work or RHEVM api equivalent
#
# This software is based on GPL code so:
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.

import sys
import getopt
import optparse
import os
import time


from ovirtsdk.api import API
from ovirtsdk.xml import params

description = """
vmcreate is a script for creating vm's based on specified values

vmcpu    defines the number of CPUs
sdtype can be: SD to use
sdsize can be: Storage to assing
vmgest can be: rhevm, or your defined networks
vmserv can be: rhevm, or your defined networks
osver can be: rhel_6x64, etc
"""

# Option parsing
p = optparse.OptionParser("rhev-vm-create.py [arguments]", description=description)
p.add_option("-u", "--user", dest="username", help="Username to connect to RHEVM API", metavar="admin@internal", default="admin@internal")
p.add_option("-w", "--password", dest="password", help="Password to use with username", metavar="admin", default="redhat")
p.add_option("-s", "--server", dest="server", help="RHEV-M server address/hostname to contact", metavar="server", default="127.0.0.1")
p.add_option('-v', "--verbosity", dest="verbosity", help="Show messages while running", metavar='[0-n]', default=0, type='int')
p.add_option("-n", "--name", dest="name", help="VM name", metavar="name", default="name")
p.add_option("-c", "--cluster", dest="cluster", help="VM cluster", metavar="cluster", default="Default")
p.add_option("--vmcpu", dest="vmcpu", help="VM CPU", metavar="vmcpu", default="1")
p.add_option("--vmmem", dest="vmmem", help="VM RAM in GB", metavar="vmmem", default="1")
p.add_option("--vmnet", dest="vmnet", help="Network to use", metavar="vmnet",default="ovirtmgmt")
p.add_option("--template", dest="template", help="give template name",default="Blank")
(options, args) = p.parse_args()

#baseurl = "https://%s:%s" % (options.server, options.port)
baseurl = "https://%s" % (options.server)

api = API(url=baseurl, username=options.username, password=options.password, insecure=True)

try:
    value = api.hosts.list()
except:
    print "Error accessing ovirt api, please check data and connection and retry"
    sys.exit(1)

# Define VM based on parameters
if __name__ == "__main__":
    vmparams = params.VM(name=options.name,cluster=api.clusters.get(name=options.cluster),template=api.templates.get(name=options.template))
    #storage_domains=params.StorageDomains(storage_domain=[api.storagedomains.get(name="FC-STOR1")]))

    try:
        api.vms.add(vmparams)
    except:
        print "Error creating VM with specified parameters, recheck"
        sys.exit(1)

    if options.verbosity > 1:
        print "VM created successfuly"

    if options.verbosity > 1:
        print "VM creation successful"

    vm = api.vms.get(name=options.name)


#Change settings to the deployed template before starting.
status = api.vms.get(name=options.name).status.state
while status != 'down':
    time.sleep(5)
    status = api.vms.get(name=options.name).status.state
    if status == 'down':
        vm.start()

