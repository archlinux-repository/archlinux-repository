#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

import os
import sys
import json
import socket
import secrets
import requests

from core.app import app
from util.process import execute
from util.process import output
from environment import environment


def _file_exists(path):
    return os.path.isfile(os.path.join(app.path.base, path))

def _get_directories(path):
    directories = []
    for f in os.scandir(path):
        if f.is_dir():
            directories.append(f.name)
    return directories

def _check_user_privilege():
    if os.getuid() == 0:
        return "This program needs to be not execute as root."

def _check_docker_image():
    if not os.environ.get("IS_DOCKER", True):
        return "This program needs to be executed in a docker image."

def _check_internet_up():
    try:
        socket.create_connection(("www.github.com", 80))
    except OSError:
        return "This program needs to be connected to internet."

def _check_repository():
    if _file_exists("repository.yml") is False:
        return "repository.yml could not been found."

def _check_deploy_key():
    if _file_exists("deploy_key") is False:
        return "deploy_key could not been found."

def _check_database():
    if not app.database:
        return "Database must be defined in repository.yml"
    elif app.database in ("core", "extra", "community"):
        return "Database must be different than core, community and extra."
    elif app.database.isalnum() is False:
        return "Database must be an alphanumeric string."

def _check_ssh_port():
    if type(app.ssh.port) != int:
        return "Port must be an interger in repository.yml"

def _check_ssh_connection():
    # Prepare SSH with deploy_key.
    environment.prepare_ssh()

    # Catch exit code with SSH connection script.
    exit_code = output(f"""
    ssh {app.ssh.user}@{app.ssh.host} \
        [[ -d {app.ssh.path} ]] && echo 1 || echo 0
    """)

    if exit_code != "1":
        return "SSH connection could not be established."

def _check_mirror_connection():
    # Write a validation token file to test mirror connection.
    with open(app.path.mirror + "/validation_token", "w") as f:
        f.write(secrets.token_hex(15))
        f.close()

    # Add file to server.
    execute(f"""
    rsync \
        --archive \
        --copy-links \
        --delete \
        --recursive \
        --update \
        --verbose \
        {app.path.mirror}/validation_token \
        {app.ssh.user}@{app.ssh.host}:{app.ssh.path}
    """)

    # Catch status code to check if the mirror address is correctly defined.
    # Expected: 200
    try:
        response = requests.get(app.website + "/validation_token")
        status_code = response.status_code
    except requests.RequestException:
        status_code = 400

    if status_code != 200:
        return "This program can't connect to %s." % app.website

def _check_github_token():
    response = output(f"""
    curl -su {app.remote_user}:{app.github_token} https://api.github.com/user
    """)

    if "login" not in json.loads(response):
        return """
        An error occured while trying to connect to your github repository with your encrypted token.
        Please make sure that your token is working.
        """

def _check_packages():
    # Check directories in pkg with no package.py
    directories = _get_directories(app.path.pkg)
    undefined_packages = set(directories) - set(app.package)

    if len(app.package) == 0:
        return "No package was found in pkg directory."
    elif len(undefined_packages) > 0:
        return "No package.py was found in pkg subdirectories: %s" % (", ".join(undefined_packages))


class Validator():
    current = 1
    statements = {
        "_check_user_privilege": "user privilege",
        "_check_docker_image": "docker image",
        "_check_internet_up": "internet connection",
        "_check_repository": "repository",
        "_check_deploy_key": "deploy key",
        "_check_database": "database",
        "_check_ssh_port": "ssh port",
        "_check_ssh_connection": "ssh connection",
        "_check_mirror_connection": "mirror connection",
        "_check_github_token": "github token",
        "_check_packages": "package directory"
    }

    def execute(self):
        if not app.has("ssh"):
            self._delete([
                "_check_deploy_key",
                "_check_ssh_port",
                "_check_ssh_connection",
                "_check_mirror_connection"
            ])

        self._prepare()

        for reference in self.statements:
            text = self.statements[reference]
            if app.runner == "run":
                self._print_on_same_line(text)
            else:
                self._print_on_multiple_line(text)

            self._catch_error(reference)

        if app.runner == "run":
            self._print_on_same_line(text, True)

    def _prepare(self):
        self.current = 0
        self.longest_text = 0
        self.length = len(self.statements)

        for reference in self.statements:
            length = len(self.statements[reference])

            if self.longest_text < length:
                self.longest_text = length

    def _print_on_same_line(self, text, last=False):
        if last:
            achivement = "Done"
            end = '\n'
        else:
            achivement = str(round(self.current / self.length * 100)) + "%"
            end = '\r'

        space = " " * (self.longest_text - len(text))
        print(f"Validating {text}... {achivement}{space}", end=end)

    def _print_on_multiple_line(self, text):
        if self.current + 1 < 10 and self.length >= 10:
            space = " "
        else:
            space = ""

        print(f"({space}{self.current + 1}/{self.length}) Validating {text}")

    def _delete(self, to_remove):
        for reference in to_remove:
            del(self.statements[reference])

    def _catch_error(self, reference):
        text = eval(reference + "()")

        if not text:
            self.current = self.current + 1
            return

        sys.exit(self._get_formated_error(text))

    def _get_formated_error(self, error):
        text = "\nError: "
        for line in error.strip().split("\n"):
            text = text + line.strip() + "\n"
        return text


validator = Validator()