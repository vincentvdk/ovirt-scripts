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
import json
import getpass
import ConfigParser

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
def getParser(defaults):
    p = optparse.OptionParser("rhev-vm-create.py [arguments]", description=description)
    p.set_defaults(**defaults)
    p.add_option("-u", "--username", dest="username", help="Username to connect to ovirt-engine API", metavar="admin@internal")
    p.add_option("-w", "--password", dest="password", help="Password to use with username", metavar="admin")
    p.add_option("-s", "--server", dest="server", help="RHEV-M server address/hostname to contact", metavar="server")
    p.add_option('-v', "--verbosity", dest="verbosity", help="Show messages while running", metavar='[0-n]', type='int')
    p.add_option("-n", "--name", dest="name", help="VM name", metavar="name")
    p.add_option("-c", "--cluster", dest="cluster", help="VM cluster", metavar="cluster")
    p.add_option("--vmcpu", dest="vmcpu", help="VM CPU", metavar="vmcpu")
    p.add_option("--vmmem", dest="vmmem", help="VM RAM in GB", metavar="vmmem")
    p.add_option("--sdtype", dest="sdtype", help="SD type", metavar="sdtype")
    p.add_option("--sdsize", dest="sdsize", help="SD size in GB", metavar="sdsize")
    p.add_option("--osver", dest="osver", help="OS version", metavar="osver")
    p.add_option("--vmnet", dest="vmnet", help="Network to use", metavar="vmnet")
    p.add_option("--config", dest="config", help="JSON config file")
    p.add_option("--storage", dest="storage_name", help="Name of the storage domain")
    p.add_option("--ca", dest="ca_file", help="Path to the ca file")
    p.add_option("--insecure", dest="insecure", help="Connect without validating the CA")
    
    return p

# Define the function to add vms
def add_vm(vmparams, name, vmdisk, nic_net1):
    try:
        api.vms.add(vmparams)
    except:
        print "Error creating VM with specified parameters, recheck"
        sys.exit(1)

    if verbosity > 1:
        print "VM created successfuly"

    if verbosity > 1:
        print "Attaching networks and boot order..."
    vm = api.vms.get(name=name)
    vm.nics.add(nic_net1)

    try:
        vm.update()
    except:
        print "Error attaching networks, please recheck and remove configurations left behind"
        sys.exit(1)

    if verbosity > 1:
        print "Adding HDD"
    try:
        vm.disks.add(vmdisk)
    except:
        print "Error attaching disk, please recheck and remove any leftover configuration"
        sys.ext(1)
    
    if verbosity > 1:
        print "Setting boot order"
    try:
        hd_boot_dev = params.Boot(dev='hd')
        net_boot_dev = params.Boot(dev='network')
        vm.os.set_boot([net_boot_dev, hd_boot_dev])
    except:
        print "Error setting boot order"
        sys.exit(1)
    
    if verbosity > 1:
        print "VM creation successful"

    vm = api.vms.get(name=name)
    vm.high_availability.enabled = True
    vm.update()

    #wait until VM is stopped before we start it.
    status = api.vms.get(name=name).status.state
    while status != 'down':
        print status
        time.sleep(1)
        status = api.vms.get(name=name).status.state
    vm.start()

# Define VM based on parameters
if __name__ == "__main__":
   
    my_defaults = {'verbose': 1}
    options, args = getParser(my_defaults).parse_args()
    if options.config is not None:
        configToLoad = options.config
    else:
        configToLoad = None

    if configToLoad is not None:
        loadedConfig = json.load(open(configToLoad))
        my_defaults.update(loadedConfig)
        options, args = getParser(my_defaults).parse_args()

    username = options.username
    server = options.server
    name = options.name
    cluster = options.cluster
    vmcpu = options.vmcpu
    vmmem = options.vmmem
    sdtype = options.sdtype
    sdsize = options.sdsize
    osver = options.osver
    vmnet = options.vmnet
    verbosity = options.verbosity
    storage_name = options.storage_name
    ca_file = options.ca_file
    insecure = options.insecure

    if options.password is None:
        password = getpass.getpass()
    else:
        password = options.password

    baseurl = "https://%s" % (server)
    
    if options.insecure:
        try:
            api = API(url=baseurl, username=username, password=password, insecure=True),
        except Exception, e:
            print "Unable to make API connection:\n %s" % str(e)
            sys.exit(1)
    else:
        try:
            api = API(url=baseurl, username=username, password=password, ca_file=ca_file)
        except Exception, e:
           print "Unable to make API connection:\n %s" % str(e)
           sys.exit(1)
    
    
    # Set the parameters for VM creation
    vmparams = params.VM(os=params.OperatingSystem(type_=osver),
            cpu=params.CPU(topology=params.CpuTopology(cores=int(vmcpu))),
            name=name, 
            memory=1024 * 1024 * 1024 * int(vmmem),
            cluster=api.clusters.get(name=cluster),
            template=api.templates.get(name="Blank"), type_="server")
    
    vmdisk = params.Disk(
            size=1024 * 1024 * 1024 * int(sdsize), 
            wipe_after_delete=True, 
            sparse=True, 
            interface="virtio", 
            type_="System", 
            bootable=True,
            format="cow",
            storage_domains=params.StorageDomains(storage_domain=[api.storagedomains.get(name=storage_name)]))

    #vmnet = params.NIC()
    network_net = params.Network(name=vmnet)
    nic_net1 = params.NIC(name='nic1', network=network_net, interface='virtio')
    
    # Commit the action of adding the VM
    add_vm(vmparams, name, vmdisk, nic_net1)
#print "MAC:%s" % vm.nics.get(name="eth0").mac.get_address()
