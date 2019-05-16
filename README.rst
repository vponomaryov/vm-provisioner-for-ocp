===================================
End-to-end OpenShift 3.X deployment
===================================

-----------
What is it?
-----------

It is end-to-end deployment tool for deployment of OpenShift 3.x and
OpenShift Container Storage (OCS).
Supported cloud platform for provisioning of nodes is VMWare. Support for
other cloud platforms can be added if needed.

Technically, it is set of Ansible playbooks, which allows to provision and
configure nodes before and after OpenShift deployment. Also, it generates
config file for 
`automated test cases. <https://github.com/gluster/glusterfs-containers-tests>`__

----------------------
What can it do? It can
----------------------

- Provision any amount of VMs with any number of vCPUs, RAM and disks.
- Enable upstream and downstream package repositories.
- Pre-install and delete packages per node-type.
- Run yum update and reboot nodes before OpenShift installation.
- Deploy any OpenShift 3.X using inventory files the same way as it
  can be done manually.
- Deploy containerized and standalone GlusterFS clusters.
- Run any Ansible playbook stored in 'openshift-ansible' library.
  It means, we can do following:
    * Deploy any OpenShift 3.X and OCS/CRS versions.
    * Scaleup existing cluster with nodes.
    * Upgrade existing cluster.
- Apply post-deployment changes.
- Gather basic info about cluster.
- Gather whole set of logs from each cluster node.
  
-------------------
VMWare requirements
-------------------

- DHCP configured for all the new VMs.

- New VMs get deployed from VMWare 'template'. So, should be created proper
  VMWare template. It can be bare RHEL7. Or somehow updated RHEL7.

- Enough computing resources for all the VMs which should be provisioned.

-------------------
Playbooks structure
-------------------

.. code-block:: console

    ======= Playbook № 1 - Provision nodes ===================
    - provision VMs
    - configure routing to each other
    ======= Playbook № 2 - Configure nodes ===================
    - enable/disable upstream repos
    - enable/disable downstream repos
    - run yum update if needed
    - reboot nodes after yum update if needed
    - remove undesired packages
    - install desired packages
    ======= Playbook № 3 - Run openshift-ansible playbooks ===
    - run openshift-ansible playbooks with your inventory file
    ======= Playbook № 4 - Update OCP ========================
    - perform updates on the just deployed ocp cluster
    ======= Playbook № 5 - Generate config for tests =========
    - generate config file for automated test cases
    ======= Playbook № 6 - Gather info about cluster =========
    - gather cluster info
    ==========================================================

    ======= Extra playbook - gather logs =====================
    - gather whole set of logs
    ======= Extra playbook - cleanup cluster =================
    - cleanup cluster
    ==========================================================

-----
Usage
-----

1) Create VMWare template VM using RHEL7
----------------------------------------

- Add SSH public key(s) for password-less connection required by Ansible

.. code-block:: console

    $ ssh-copy-id username@ip_address_of_the_vm_which_will_be_used_as_template

- Make sure that default user SSH key pair is the same on the “Ansible” machine

2) Install dependencies
-----------------------

Install following dependencies on the machine where you are going to run
deployment.

- Install “pip”, “git” and “libselinux-python” if not installed yet:

.. code-block:: console

    $ yum install python-pip git libselinux-python

- Install “tox” if not installed yet:

.. code-block:: console

    $ pip install git+git://github.com/tox-dev/tox.git@2.9.1#egg=tox

Considering the fact that it is 'end-to'end' deployment tool,
deployment always will run on the separate machine compared to the machines
of deployed cluster.

3) Configure tool before starting deployment
--------------------------------------------

Current deployment tool has it's own configuration file. Examples are stored in
"config-examples" directory. Config file is expected to be in 'yaml' format.
Config file is specified as argument for Ansible playbook.

4) Deploy OpenShift with or without OCS:
----------------------------------------

Example of CLI command to run end-to-end deployment:

.. code-block:: console

    $ tox -e ocp3.11 -- ansible-playbook -i inventory-file.yaml \
        control_playbook.yaml \
        -e config_filepath=/path/to/the/config.yaml \
        -e ocp_playbooks=playbooks/prerequisites.yml,playbooks/deploy_cluster.yml \
        --tags 1,2,3,4,5,6

Option called "--tags" can also be "all". Here is list of tags you can use:

- '1', 'node_provision' or 'node_provisioning' to run first step where we
  provision nodes.
- '2' or 'node_configure' to run second step where we configure nodes.
- '3', 'ocp_deploy' or 'ocp_deployment' to run third, special, step
  where we run playbooks from 'openshift-ansible' library. Inventory file you
  specify is used only on this step.
- '4' or 'ocp_update' to run forth step where we update just deployed cluster
  with such things as adding public IP address for Heketi service.
- '5' or 'tests_config' to autogenerate config file for automated test cases.
- '6' or 'cluster_info' to autogenerate info file about services and packages
  used in just deployed cluster.

Any step can be run separately, while you keep config file the same.
For example, if you ran deployment and it failed on node configuration due to
the improper configuration option values. You can continue deployment, after
fixing config file, from the failed step, removing previous steps from "--tags"
option.

Name of virtual environment in 'tox' command can take following values:

- ocp3.6
- ocp3.7
- ocp3.9
- ocp3.10
- ocp3.11

Separate virtual environments are required for possibility to automatically
pull all the required dependencies for Ansible runner.

If you need to specify custom version of 'openshift-ansible' library, then
define following environment variable in the shell you are going to use for
running Ansible playbooks:

.. code-block:: console

    $ export OPENSHIFT_ANSIBLE_GIT_TAG=openshift-ansible-3.11.115-1

And then run deployment.

5) Gather cluster logs
----------------------

It is possible to gather logs of a cluster running following playbook:

.. code-block:: console

    $ tox -e ocp3.11 -- ansible-playbook -i localhost, gather_logs.yaml \
        -e config_filepath=/path/to/the/config.yaml \
        -e output_artifacts_dir=../cluster_logs/

6) Clean up deployed cluster
----------------------------

If deplyoed cluster is not needed anymore, it can be cleaned up using following
command:

.. code-block:: console

    $ tox -e ocp3.11 -- ansible-playbook -i localhost, cleanup.yaml \
        -e config_filepath=/path/to/the/config.yaml
