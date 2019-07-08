#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = '''
---
module: dt_validate_vms_provisioning_config

short_description: validates config options for OpenShift deployment tool

version_added: "2.4"

description:
    - "validates config options for OpenShift deployment tool"

options:
    path:
        description:
            - Path to config file, which should be validated.
        required: true
    check_groups:
        description:
            - List of top-level config options to validate.
        required: false

extends_documentation_fragment:

author:
    - Valerii Ponomarov (@vponomar)
'''

EXAMPLES = '''
- name: Read and validate whole config file
  dt_validate_vms_provisioning_config:
    path: "/fake/path/to/config/file.yaml"
  register: config_output

- name: Read and validate part of a config file
  dt_validate_vms_provisioning_config:
    path: "/fake/path/to/config/file.yaml"
    check_groups: ['common', 'vms']
  register: config_output
'''

RETURN = '''
config:
    description: Dictionary with validated data and inserted in default values.
    type: dict
'''

import schema
import yaml

from ansible.module_utils.basic import AnsibleModule


def validate_config_structure(module, config):

    vm_repo_downstream_default = {
        "skip": True,
        "repositories_to_enable": {
            "all": [], "masters": [], "nodes": [], "glusterfs": [],
            "glusterfs_registry": [],
        },
    }
    common_default = {
        "output_tests_config_file": "../tests_config.yaml",
        "output_cluster_info_file": "../cluster_info.yaml",
    }
    ocp_update_default = {
        "heketi": {
            "install_client_on_masters": True,
            "client_package_url": None,
            "add_public_ip_address": True,
        },
    }
    config_schema_dict = {
        "vmware": {
            "host": schema.And(str, len),
            "username": schema.And(str, len),
            "password": schema.And(str, len),
            "datacenter": schema.And(str, len),
            "cluster": schema.And(str, len),
            "resource_pool": schema.And(str, len),
            "folder": schema.And(str, len),
            "datastore": schema.And(str, len),
            "vm_network": schema.And(str, len),
            "vm_templates": [schema.And(str, len)],
            "vm_parameters": {
                "masters": {
                    schema.Optional("num_cpus", default=1): schema.And(
                        int, lambda i: i in range(1, 17)),
                    schema.Optional("ram_mb", default=16384): schema.And(
                        int, lambda i: 4096 <= i <= 65535),
                    schema.Optional("names", default=[]): schema.Or(
                        schema.And(
                            [schema.And(str, len)], lambda l: len(l) <= 3),
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                        ))
                    ),
                    schema.Optional("system_disks_gb",
                                    default=[150]): schema.And(
                        [schema.And(int, lambda i: 0 < i)],
                        lambda l: len(l) <= 4),
                    schema.Optional("system_disks_type", default='thin'): (
                        schema.And(str, len))
                },
                "nodes": {
                    schema.Optional("num_cpus", default=1): schema.And(
                        int, lambda i: i in range(1, 17)),
                    schema.Optional("ram_mb", default=16384): schema.And(
                        int, lambda i: 4096 <= i <= 65535),
                    schema.Optional("names", default=[]): schema.Or(
                        schema.And(
                            [schema.And(str, len)], lambda l: len(l) <= 3),
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                        ))
                    ),
                    schema.Optional("system_disks_gb",
                                    default=[150]): schema.And(
                        [schema.And(int, lambda i: 0 < i)],
                        lambda l: len(l) <= 4),
                    schema.Optional("system_disks_type", default='thin'): (
                        schema.And(str, len))
                },
                "glusterfs": {
                    schema.Optional("num_cpus", default=1): schema.And(
                        int, lambda i: i in range(1, 17)),
                    schema.Optional("ram_mb", default=16384): schema.And(
                        int, lambda i: 4096 <= i <= 65535),
                    schema.Optional("names", default=[]): schema.Or(
                        schema.And(
                            [schema.And(str, len)], lambda l: len(l) <= 9),
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                        ))
                    ),
                    schema.Optional("system_disks_gb",
                                    default=[150]): schema.And(
                        [schema.And(int, lambda i: 0 < i)],
                        lambda l: len(l) <= 4),
                    schema.Optional("system_disks_type", default='thin'): (
                        schema.And(str, len)),
                    schema.Optional("storage_disks_gb",
                                    default=[100, 600, 100]): schema.And(
                        [schema.And(int, lambda i: 0 < i)],
                        lambda l: len(l) <= 7),
                    schema.Optional("storage_disks_type", default='thin'): (
                        schema.And(str, len))
                },
                "glusterfs_registry": {
                    schema.Optional("num_cpus", default=1): schema.And(
                        int, lambda i: i in range(1, 17)),
                    schema.Optional("ram_mb", default=16384): schema.And(
                        int, lambda i: 4096 <= i <= 65535),
                    schema.Optional("names", default=[]): schema.Or(
                        schema.And(
                            [schema.And(str, len)], lambda l: len(l) <= 9),
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                        ))
                    ),
                    schema.Optional("system_disks_gb",
                                    default=[150]): schema.And(
                        [schema.And(int, lambda i: 0 < i)],
                        lambda l: len(l) <= 4),
                    schema.Optional("system_disks_type", default='thin'): (
                        schema.And(str, len)),
                    schema.Optional("storage_disks_gb",
                                    default=[100, 600, 100]): schema.And(
                        [schema.And(int, lambda i: 0 < i)],
                        lambda l: len(l) <= 7),
                    schema.Optional("storage_disks_type", default='thin'): (
                        schema.And(str, len))
                },
            },
        },
        "vm": {
            "repo": {
                schema.Optional("upstream",
                                default={"skip": True,
                                         "subscription_server": "not_set",
                                         "subscription_baseurl": "not_set",
                                         "subscription_user": "not_set",
                                         "subscription_pass": "not_set",
                                         "subscription_pool": "not_set",
                                         "repositories_to_enable": {
                                             "all": [], "masters": [],
                                             "nodes": [], "glusterfs": [],
                                             "glusterfs_registry": []}}): {
                    schema.Optional("skip", default=True): bool,
                    schema.Optional("subscription_server",
                                    default="not_set"): schema.Or(
                        schema.And(str, len), None),
                    schema.Optional("subscription_baseurl",
                                    default="not_set"): schema.Or(
                        schema.And(str, len), None),
                    schema.Optional("subscription_user",
                                    default="not_set"): schema.Or(
                        schema.And(str, len), None),
                    schema.Optional("subscription_pass",
                                    default="not_set"): schema.Or(
                        schema.And(str, len), None),
                    schema.Optional("subscription_pool",
                                    default="not_set"): schema.Or(
                        schema.And(str, len), None),
                    schema.Optional("repositories_to_enable",
                                    default={"all": [],
                                             "masters": [],
                                             "nodes": [],
                                             "glusterfs": []}): schema.Or({
                        "all": schema.Or(
                            [schema.And(str, len)],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                            ))
                        ),
                        "masters": schema.Or(
                            [schema.And(str, len)],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                            ))
                        ),
                        "nodes": schema.Or(
                            [schema.And(str, len)],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                            ))
                        ),
                        "glusterfs": schema.Or(
                            [schema.And(str, len)],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                            ))
                        ),
                        "glusterfs_registry": schema.Or(
                            [schema.And(str, len)],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"]
                            ))
                        ),
                    }, None),
                },
                schema.Optional("downstream",
                                default=vm_repo_downstream_default): schema.Or({
                    schema.Optional("skip", default=True): bool,
                    schema.Optional("repositories_to_enable",
                                    default=vm_repo_downstream_default[
                                        "repositories_to_enable"]): schema.Or({
                        "all": schema.Or(
                            [{
                                "name": schema.And(str, len),
                                "url": schema.And(str, lambda s: 'http' in s),
                                "cost": schema.And(int, lambda i: 0 < i),
                            }],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"])),
                        ),
                        "masters": schema.Or(
                            [{
                                "name": schema.And(str, len),
                                "url": schema.And(str, lambda s: 'http' in s),
                                "cost": schema.And(int, lambda i: 0 < i),
                            }],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"])),
                        ),
                        "nodes": schema.Or(
                            [{
                                "name": schema.And(str, len),
                                "url": schema.And(str, lambda s: 'http' in s),
                                "cost": schema.And(int, lambda i: 0 < i),
                            }],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"])),
                        ),
                        "glusterfs": schema.Or(
                            [{
                                "name": schema.And(str, len),
                                "url": schema.And(str, lambda s: 'http' in s),
                                "cost": schema.And(int, lambda i: 0 < i),
                            }],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"])),
                        ),
                        "glusterfs_registry": schema.Or(
                            [{
                                "name": schema.And(str, len),
                                "url": schema.And(str, lambda s: 'http' in s),
                                "cost": schema.And(int, lambda i: 0 < i),
                            }],
                            schema.Use(lambda o: ([] if o is None else {}[
                                "Only 'None' or 'list' objects are allowed"])),
                        ),
                    }, schema.Use(lambda o: ([] if o is None else {}[
                        "Only 'None' or 'dict' objects are allowed"])),
                    ),
                }, schema.Use(lambda o: (
                    vm_repo_downstream_default if o is None else {}[
                    "Only 'None' or 'dict' objects are allowed"])),
                ),
            },
            "yum": {
                schema.Optional("update", default=True): bool,
                schema.Optional("reboot_after_update", default=True): bool,
                schema.Optional("sleep_after_reboot_sec", default=60): int,
            },
            schema.Optional("uninstall_packages",
                            default={"all": [], "masters": [], "nodes": [],
                                     "glusterfs": [],
                                     "glusterfs_registry": []}): schema.Or(
                {
                    schema.Optional("all", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("masters", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("nodes", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("glusterfs", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("glusterfs_registry",
                                    default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                },
                schema.Use(lambda o: (
                    {"all": [], "masters": [], "nodes": [], "glusterfs": [],
                     "glusterfs_registry": []}
                    if o is None else {}[
                        "Only 'None' or 'dict' objects are allowed"]
                ))
            ),
            schema.Optional("install_packages",
                            default={"all": [], "masters": [], "nodes": [],
                                     "glusterfs": [],
                                     "glusterfs_registry": []}): schema.Or(
                {
                    schema.Optional("all", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("masters", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("nodes", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("glusterfs", default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                    schema.Optional("glusterfs_registry",
                                    default=[]): schema.Or(
                        [schema.And(str, len)],
                        schema.Use(lambda o: (
                            [] if o is None else {}[
                                "Only 'None' or 'str' objects are allowed"]
                        ))
                    ),
                },
                schema.Use(lambda o: (
                    {"all": [], "masters": [], "nodes": [], "glusterfs": [],
                     "glusterfs_registry": []}
                    if o is None else {}[
                        "Only 'None' or 'dict' objects are allowed"]
                ))
            ),
            schema.Optional("setup_and_configuration", default={
                    "setup_common_packages": True,
                    "setup_ntp": True,
                    "setup_vmware_tools": True,
                    "mount_disks": [],
                    "setup_docker_storage": {"skip": True, "disk_path": None},
                    "setup_standalone_glusterfs": False,
                    "setup_standalone_glusterfs_registry": False}): {
                schema.Optional("setup_common_packages",
                                default=True): bool,
                schema.Optional("setup_ntp", default=True): bool,
                schema.Optional("setup_vmware_tools", default=True): bool,
                schema.Optional("mount_disks", default=[]): schema.Or(
                    [{
                        "disk_path": schema.And(
                            str, lambda s: s.startswith("/dev/")),
                        "mount_point": schema.And(
                            str, lambda s: s.startswith("/")),
                        "name_prefix": schema.And(str, len),
                        "fstype": schema.And(str, len),
                    }],
                    schema.Use(lambda o: ([] if o is None else {}[
                        "Only 'None' or 'list' objects are allowed"])),
                ),
                schema.Optional("setup_docker_storage",
                                default={"skip": True, "disk_path": None}): {
                    schema.Optional("skip", default=True): bool,
                    schema.Optional("disk_path", default=None): (
                        schema.And(str, len)),
                },
                schema.Optional("setup_standalone_glusterfs",
                                default=False): bool,
                schema.Optional("setup_standalone_glusterfs_registry",
                                default=False): bool,
            },
        },
        schema.Optional("ocp_update", default=ocp_update_default): {
            schema.Optional("heketi", default=ocp_update_default["heketi"]): {
                schema.Optional("install_client_on_masters",
                                default=True): bool,
                schema.Optional("client_package_url", default=None): (
                    schema.And(str, len)),
                schema.Optional("add_public_ip_address", default=True): bool,
            },
        },
        schema.Optional("common", default=common_default): schema.Or(
            {
                schema.Optional("output_tests_config_file",
                                default=(common_default[
                                    "output_tests_config_file"])): (
                    schema.And(str, len)),
                schema.Optional("output_cluster_info_file",
                                default=(common_default[
                                    "output_cluster_info_file"])): (
                    schema.And(str, len)),
            },
            schema.Use(lambda o: (
                {
                    "output_tests_config_file": (
                        common_default["output_tests_config_file"]),
                    "output_cluster_info_file": (
                        common_default["output_cluster_info_file"]),
                }
                if o is None else {}[
                    "Only 'dict' and 'None' values are allowed"]))
        ),
    }
    if module.params["check_groups"]:
        config_schema_dict = {
            k:v for k, v in config_schema_dict.items()
            if getattr(k, 'key', k) in module.params["check_groups"]}
        config_schema = schema.Schema(
            config_schema_dict, ignore_extra_keys=True)
    else:
        config_schema = schema.Schema(config_schema_dict)

    try:
        validated_config = config_schema.validate(config)
    except schema.SchemaError as e:
        module.fail_json(msg=("Error: %s" % e))
    return validated_config


def main():
    module_args = {
        "path": {"type": "str", "required": True},
        "check_groups": {"type": "list", "required": False},
    }
    result = {"config": ""}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    if module.check_mode:
        return result

    # Make sure file was provided, it exists and yaml-parsible
    if not (module.params['path'] and module.params['path'].strip()):
        module.fail_json(msg="Path for config file is not provided")
    with open(module.params['path'], 'r') as config_stream:
        try:
            config = yaml.load(config_stream)
        except yaml.YAMLError as e:
            module.fail_json(
                msg=("Failed to parse '%s' file as yaml. "
                     "Got following error: %s") % (module.params['path'], e))

    # Validate config structure after successful parsing of the file
    validated_config = validate_config_structure(module, config)

    # Finish module execution
    result["config"] = validated_config
    module.exit_json(**result)


if __name__ == '__main__':
    main()
