#!/usr/bin/env python
#
# Based on a script by Pablo Iranzo Gomez (Pablo.Iranzo@redhat.com)
#
# Description: Script for creating VM's
#
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
vmgest can be: ovirtmgmt, or your defined networks
osver can be: rhel_6x64, etc
"""

# Option parsing
p = optparse.OptionParser("rhev-vm-create.py [arguments]", description=description)
p.add_option("-u", "--user", dest="username", help="Username to connect to ovirt-engine API", metavar="admin@internal", default="admin@internal")
p.add_option("-w", "--password", dest="password", help="Password to use with username", metavar="admin", default="redhat")
p.add_option("-s", "--server", dest="server", help="RHEV-M server address/hostname to contact", metavar="server", default="127.0.0.1")
p.add_option('-v', "--verbosity", dest="verbosity", help="Show messages while running", metavar='[0-n]', default=0, type='int')
p.add_option("-n", "--name", dest="name", help="VM name", metavar="name", default="name")
p.add_option("-c", "--cluster", dest="cluster", help="VM cluster", metavar="cluster", default="Default")
p.add_option("--vmcpu", dest="vmcpu", help="VM CPU", metavar="vmcpu", default="1")
p.add_option("--vmmem", dest="vmmem", help="VM RAM in GB", metavar="vmmem", default="1")
p.add_option("--sdtype", dest="sdtype", help="SD type", metavar="sdtype", default="Default")
p.add_option("--sdsize", dest="sdsize", help="SD size in GB", metavar="sdsize", default="20")
p.add_option("--osver", dest="osver", help="OS version", metavar="osver", default="rhel_6x64")
p.add_option("--vmnet", dest="vmnet", help="Network to use", metavar="vmnet", default="rhevm")

(options, args) = p.parse_args()

baseurl = "https://%s" % (options.server)

api = API(url=baseurl, username=options.username, password=options.password, insecure=True)

try:
    value = api.hosts.list()
except:
    print "Error accessing RHEV-M api, please check data and connection and retry"
    sys.exit(1)

# Define VM based on parameters
if __name__ == "__main__":
    vmparams = params.VM(os=params.OperatingSystem(type_=options.osver),
    cpu=params.CPU(topology=params.CpuTopology(cores=int(options.vmcpu))),
    name=options.name, memory=1024 * 1024 * 1024 * int(options.vmmem),
    cluster=api.clusters.get(name=options.cluster),
    template=api.templates.get(name="Blank"), type_="server")
    vmdisk = params.Disk(size=1024 * 1024 * 1024 * int(options.sdsize), wipe_after_delete=True, sparse=True, interface="virtio", type_="System", format="cow",
    storage_domains=params.StorageDomains(storage_domain=[api.storagedomains.get(name="DATA1")]))
    vmnet = params.NIC()

    network_net = params.Network(name=options.vmnet)

    nic_net1 = params.NIC(name='nic1', network=network_net, interface='virtio')

    try:
        api.vms.add(vmparams)
    except:
        print "Error creating VM with specified parameters, recheck"
        sys.exit(1)

    if options.verbosity > 1:
        print "VM created successfuly"

    if options.verbosity > 1:
        print "Attaching networks and boot order..."
    vm = api.vms.get(name=options.name)
    vm.nics.add(nic_net1)

    try:
        vm.update()
    except:
        print "Error attaching networks, please recheck and remove configurations left behind"
        sys.exit(1)

    if options.verbosity > 1:
        print "Adding HDD"
    try:
        vm.disks.add(vmdisk)
    except:
        print "Error attaching disk, please recheck and remove any leftover configuration"

    if options.verbosity > 1:
        print "VM creation successful"

    vm = api.vms.get(name=options.name)
    vm.high_availability.enabled = True
    vm.update()

#wait until VM is stopped before we start it.
status = api.vms.get(name=options.name).status.state
while status != 'down':
		print status
		time.sleep(5)
		status = api.vms.get(name=options.name).status.state
		vm.start()

#print "MAC:%s" % vm.nics.get(name="eth0").mac.get_address()
