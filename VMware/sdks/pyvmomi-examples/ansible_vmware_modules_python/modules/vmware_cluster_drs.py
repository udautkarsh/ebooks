#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_cluster_drs
short_description: Manage Distributed Resource Scheduler (DRS) on VMware vSphere clusters
description:
    - Manages DRS on VMware vSphere clusters.
    - All values and VMware object names are case sensitive.
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
requirements:
    - Tested on ESXi 5.5 and 6.5.
    - PyVmomi installed.
options:
    cluster_name:
      description:
      - The name of the cluster to be managed.
      type: str
      required: true
    datacenter:
      description:
      - The name of the datacenter.
      type: str
      required: true
      aliases: [ datacenter_name ]
    enable_drs:
      description:
      - Whether to enable DRS.
      type: bool
      default: false
    drs_enable_vm_behavior_overrides:
      description:
      - Whether DRS Behavior overrides for individual virtual machines are enabled.
      - If set to C(True), overrides C(drs_default_vm_behavior).
      type: bool
      default: True
    drs_default_vm_behavior:
      description:
      - Specifies the cluster-wide default DRS behavior for virtual machines.
      - If set to C(partiallyAutomated), vCenter generates recommendations for virtual machine migration and
        for the placement with a host, then automatically implements placement recommendations at power on.
      - If set to C(manual), then vCenter generates recommendations for virtual machine migration and
        for the placement with a host, but does not implement the recommendations automatically.
      - If set to C(fullyAutomated), then vCenter automates both the migration of virtual machines
        and their placement with a host at power on.
      type: str
      default: fullyAutomated
      choices: [ fullyAutomated, manual, partiallyAutomated ]
    drs_vmotion_rate:
      description:
      - Threshold for generated ClusterRecommendations.
      type: int
      default: 3
      choices: [ 1, 2, 3, 4, 5 ]
    advanced_settings:
      description:
      - A dictionary of advanced DRS settings.
      default: {}
      type: dict
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Enable DRS
  community.vmware.vmware_cluster_drs:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_drs: true
  delegate_to: localhost

- name: Enable DRS and distribute a more even number of virtual machines across hosts for availability
  community.vmware.vmware_cluster_drs:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_drs: true
    advanced_settings:
      'TryBalanceVmsPerHost': '1'
  delegate_to: localhost

- name: Enable DRS and set default VM behavior to partially automated
  community.vmware.vmware_cluster_drs:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter_name: DC0
    cluster_name: "{{ cluster_name }}"
    enable_drs: True
    drs_default_vm_behavior: partiallyAutomated
  delegate_to: localhost
'''

RETURN = r'''#
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    PyVmomi,
    TaskError,
    find_datacenter_by_name,
    vmware_argument_spec,
    wait_for_task,
    option_diff,
)
from ansible.module_utils._text import to_native


class VMwareCluster(PyVmomi):
    def __init__(self, module):
        super(VMwareCluster, self).__init__(module)
        self.cluster_name = module.params['cluster_name']
        self.datacenter_name = module.params['datacenter']
        self.enable_drs = module.params['enable_drs']
        self.datacenter = None
        self.cluster = None

        self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
        if self.datacenter is None:
            self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)

        self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name, datacenter_name=self.datacenter)
        if self.cluster is None:
            self.module.fail_json(msg="Cluster %s does not exist." % self.cluster_name)

        self.advanced_settings = self.params.get('advanced_settings')
        if self.advanced_settings:
            self.changed_advanced_settings = option_diff(self.advanced_settings, self.cluster.configurationEx.drsConfig.option)
        else:
            self.changed_advanced_settings = None

    def check_drs_config_diff(self):
        """
        Check DRS configuration diff
        Returns: True if there is diff, else False

        """
        drs_config = self.cluster.configurationEx.drsConfig

        if drs_config.enabled != self.enable_drs or \
                drs_config.enableVmBehaviorOverrides != self.params.get('drs_enable_vm_behavior_overrides') or \
                drs_config.defaultVmBehavior != self.params.get('drs_default_vm_behavior') or \
                drs_config.vmotionRate != self.params.get('drs_vmotion_rate'):
            return True

        if self.changed_advanced_settings:
            return True

        return False

    def configure_drs(self):
        """
        Manage DRS configuration

        """
        changed, result = False, None

        if self.check_drs_config_diff():
            if not self.module.check_mode:
                cluster_config_spec = vim.cluster.ConfigSpecEx()
                cluster_config_spec.drsConfig = vim.cluster.DrsConfigInfo()
                cluster_config_spec.drsConfig.enabled = self.enable_drs
                cluster_config_spec.drsConfig.enableVmBehaviorOverrides = self.params.get('drs_enable_vm_behavior_overrides')
                cluster_config_spec.drsConfig.defaultVmBehavior = self.params.get('drs_default_vm_behavior')
                cluster_config_spec.drsConfig.vmotionRate = self.params.get('drs_vmotion_rate')

                if self.changed_advanced_settings:
                    cluster_config_spec.drsConfig.option = self.changed_advanced_settings

                try:
                    task = self.cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
                    changed, result = wait_for_task(task)
                except vmodl.RuntimeFault as runtime_fault:
                    self.module.fail_json(msg=to_native(runtime_fault.msg))
                except vmodl.MethodFault as method_fault:
                    self.module.fail_json(msg=to_native(method_fault.msg))
                except TaskError as task_e:
                    self.module.fail_json(msg=to_native(task_e))
                except Exception as generic_exc:
                    self.module.fail_json(msg="Failed to update cluster"
                                              " due to generic exception %s" % to_native(generic_exc))
            else:
                changed = True

        self.module.exit_json(changed=changed, result=result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True, aliases=['datacenter_name']),
        # DRS
        enable_drs=dict(type='bool', default=False),
        drs_enable_vm_behavior_overrides=dict(type='bool', default=True),
        drs_default_vm_behavior=dict(type='str',
                                     choices=['fullyAutomated', 'manual', 'partiallyAutomated'],
                                     default='fullyAutomated'),
        drs_vmotion_rate=dict(type='int',
                              choices=[1, 2, 3, 4, 5],
                              default=3),
        advanced_settings=dict(type='dict', default=dict(), required=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_cluster_drs = VMwareCluster(module)
    vmware_cluster_drs.configure_drs()


if __name__ == '__main__':
    main()
