#!/usr/bin/env python

import os
import sys

from utils.validator import validate
from utils.terminal import output

class init():
   def __init__(self, **parameters):
      self.config = parameters['config']
      self.contextual = parameters['contextual']

   def files(self):
      print("Validating files:")

      validate(
         error = "deploy_key could not been found.",
         target = "deploy_key",
         valid = os.path.isfile(self.contextual.path_base + "/deploy_key")
      )

   def ssh(self):
      print("Validating ssh connection:")

      script = "ssh -i ./deploy_key -p %i -q %s@%s [[ -d %s ]] && echo 1 || echo 0" % (
         self.config.get("ssh.port"),
         self.config.get("ssh.user"),
         self.config.get("ssh.host"),
         self.config.get("ssh.path")
      )

      validate(
         error = "ssh connection could not be established.",
         target = "ssh connection",
         valid = output(script) is "1"
      )

   def repository(self):
      print("Validating repository.json:")

      requirements = {
         "database"  : [ "not_blank" ],
         "git.email" : [ "not_blank" ],
         "git.name"  : [ "not_blank" ],
         "ssh.host"  : [ "not_blank" ],
         "ssh.path"  : [ "not_blank" ],
         "ssh.port"  : [ "not_blank", "is_integer" ],
         "ssh.user"  : [ "not_blank" ],
         "url"       : [ "not_blank" ]
      }

      errors = {
         "not_blank"  : "%s must be defined in repository.json",
         "is_integer" : "%s must be an integer in repository.json"
      }

      for name in requirements:
         value = self.config.get(name)
         target = name.replace(".", " ")

         for validation in requirements[name]:
            if validation == "not_blank":
               validate(
                  error = errors["not_blank"] % target,
                  target = target,
                  valid = value
               )

            elif validation == "is_integer":
               validate(
                  error = errors["is_integer"] % target,
                  target = target,
                  valid = type(value) is int
               )