#!/usr/bin/env python

"""
Copyright (c) Build Your Own Arch Linux Repository developers
See the file 'LICENSE' for copying permission
"""

from core.type import Attr

# Bot version (<major>.<minor>.<month>.<monthly commit>)
# To get the monthly commit, you need to execute:
#   git rev-list --count HEAD --since="last month"
VERSION = "1.0.6.33"

# Contextual paths
paths = Attr()

# Config into repository.json
configs = Attr()

# Packages in pkg directory
packages = []