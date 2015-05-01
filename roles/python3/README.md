python3
=========

Installs python3 

Requirements
------------

FreeBSD/Ubuntu OS

Role Variables
--------------

python3_pip_packages: packages to be installed by the pip3 python package manager

Example Playbook
----------------
```
--- 
- hosts: all
  connection: local
  sudo: yes
  roles:
    - python3
  vars:
    python3_pip_packages:
      - awscli
      - boto
```

License
-------

Apache

Author Information
------------------
Stephen Garlick @ gocurb
