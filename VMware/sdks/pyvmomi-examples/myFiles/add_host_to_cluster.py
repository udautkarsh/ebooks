import atexit
import subprocess

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect, SmartConnectNoSSL

# Use tasks.py from https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
from tools import tasks


def get_ssl_thumbprint(host_ip):
    p1 = subprocess.Popen(('echo-n'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(('openssls_client', '-connect', '{0}:443'.format(host_ip)), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p3 = subprocess.Popen(('opensslx509', '-noout', '-fingerprint', '-sha1'), stdin=p2.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p3.stdout.read()
    ssl_thumbprint = out.split(b'=')[-1].strip()
    return ssl_thumbprint.decode("utf-8")


class VMWareClient:
    def __init__(self, host, user, password, port=443, insecure=True):
        if insecure:
            self._service_instance = SmartConnectNoSSL(host=host, user=user, pwd=password, port=port)
        else:
            self._service_instance = SmartConnect(host=host, user=user, pwd=password, port=port)
        self._host = host
        self._user = user
        self._password = password 
        atexit.register(Disconnect, self._service_instance)
        self._content = self._service_instance.RetrieveContent()

    def create_datacenter(self, name):
        folder = self._content.rootFolder
        return folder.CreateDatacenter(name=name)

    def create_cluster(self, name, datacenter):
        host_folder = datacenter.hostFolder
        cluster_spec = vim.cluster.ConfigSpecEx()
        return host_folder.CreateClusterEx(name=name, spec=cluster_spec)

def add_host_to_vc(self, host_ip, host_username, host_password, datacenter_name, cluster_name):
    host_connect_spec = vim.host.ConnectSpec()
    host_connect_spec.hostName = host_ip
    host_connect_spec.userName = host_username
    host_connect_spec.password = host_password
    host_connect_spec.force = True
    host_connect_spec.sslThumbprint = get_ssl_thumbprint(host_ip)
    datacenter = self.create_datacenter(datacenter_name)
    cluster = self.create_cluster(cluster_name, datacenter)
    add_host_task = cluster.AddHost(spec=host_connect_spec, asConnected=True)
    tasks.wait_for_tasks(self._service_instance, [add_host_task])


# Example to add an ESXi host to VCenter
vcenter_ip = '192.168.10.20'
vcenter_username = 'administrator@vsphere.local'
vcenter_password = 'vcenterpassword'

esxi_host_ip = '192.168.10.10'
esxi_host_username = 'root'
esxi_host_password = 'esxipassword'

datacenter_name = 'esxi_dc'
cluster_name = 'esxi_cluster'

vmware_client = VMWareClient(vcenter_ip, vcenter_username, vcenter_password)
vmware_client.add_host_to_vc(esxi_host_ip, esxi_host_username, esxi_host_password, datacenter_name, cluster_name)