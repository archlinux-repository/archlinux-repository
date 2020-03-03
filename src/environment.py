#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import time
import sys
import subprocess

from core.app import app

from util.process import execute
from util.process import output


class Environment():
    def prepare_ssh(self):
        """
        This function prepare ssh before to interact with the remote.
        """
        execute(f"""
        eval $(ssh-agent);
        chmod 600 ./deploy_key;
        ssh-add ./deploy_key;
        mkdir -p ~/.ssh;
        chmod 0700 ~/.ssh;
        ssh-keyscan -t rsa -H {app.ssh.host} >> ~/.ssh/known_hosts;
        """)

        with open("/home/bot/.ssh/config", "w") as f:
            f.write(f"""
            LogLevel ERROR
            Host {app.ssh.host}
                HostName {app.ssh.host}
                User {app.ssh.user}
                Port {app.ssh.port}
                IdentityFile {app.path.base}/deploy_key
            """)
            f.close()

    def prepare_git(self):
        """
        This function prepare git by setting user name and email.
        Uvobot is used to commit repository changes.
        """
        execute("""
        git config --global user.email 'uvobot@lognoz.org';
        git config --global user.name 'uvobot';
        """)

    def prepare_mirror(self):
        """
        This function prepare mirror by verifing if we can pull files online.
        """
        black_list   = [ "validation_token", "packages_checked" ]
        staged       = output("git ls-files " + app.path.mirror).strip()
        in_directory = os.listdir(app.path.mirror)

        if staged != "":
            black_list = staged.split("\n") + black_list

        for f in black_list:
            if f in in_directory:
                in_directory.remove(f)

        if not app.has("ssh") or in_directory != []:
            return

        print("Updating local mirror directory... ")

        command = (f"""
        rsync \
            --update \
            --progress \
            {app.ssh.user}@{app.ssh.host}:{app.ssh.path}/libc* \
            {app.path.mirror}/
        """)

        os.system(command)

    def prepare_pacman(self):
        """
        This function is used to update pacman remote.
        """
        path = app.path.mirror + "/" + app.database + ".db"

        execute("sudo chmod 777 /etc/pacman.conf")

        if os.path.exists(path) is False:
            return

        with open("/etc/pacman.conf", "a+") as fp:
            fp.write(textwrap.dedent(f"""
            [{app.database}]
            SigLevel = Optional TrustedOnly
            Server = file:///{app.path.mirror}
            """))

        execute(f"""
        sudo cp {path} /var/lib/pacman/sync/{app.database}.db
        """)


environment = Environment()
