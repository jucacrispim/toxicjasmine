# -*- coding: utf-8 -*-
# Copyright 2023 Juca Crispim <juca@poraodojuca.net>

# This file is part of toxicjasmine.

# toxicjasmine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# toxicjasmine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with toxicjasmine. If not, see <http://www.gnu.org/licenses/>.

from yaml import load, Loader

class MonkeyPatcher:

    def __init__(self):
        self.patched = {}
        # if the original patched object is a dict, indicates if
        # we should merge the original dict with the dict existing
        # when leaving the context manager.
        self._update_original_dict = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for obj, patches in self.patched.items():
            for attr, origobj in patches.items():
                if self._update_original_dict:
                    current_obj = getattr(obj, attr)
                    if hasattr(current_obj, 'update'):
                        origobj.update(current_obj)
                setattr(obj, attr, origobj)

    def patch_item(self, obj, attr, newitem, undo=True):
        """Sets ``attr`` in ``obj`` with ``newitem``.
        If not ``undo`` the item will continue patched
        after leaving the context manager"""

        NONE = object()
        olditem = getattr(obj, attr, NONE)
        if undo and olditem is not NONE:
            self.patched.setdefault(obj, {}).setdefault(attr, olditem)
        setattr(obj, attr, newitem)

    def patch_load(self):

        from jasmine.config import Config

        self.patch_item(Config, '_load', _load)

    def patch_all(self):
        self.patch_load()


def _load(self):
    with open(self.yaml_file, 'r') as f:
        self._yaml = load(f, Loader=Loader) or {}
