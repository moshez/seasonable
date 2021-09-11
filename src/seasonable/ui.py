from __future__ import annotations

import ipywidgets
import attr
import re
import functools
import httpx
import uuid
import traitlets
import pathlib

@attr.s(auto_attribs=True)
class UIBuilder:
    _widgets : Dict[str, Any] = attr.ib(init=False, factory=dict)
        
    def add_widgets(self, **kwargs):
        for name, widget in kwargs.items():
            self._widgets[name] = widget
        
    def __getattr__(self, name):
        if name.startswith("ui_"):
            return self._widgets[name[3:]]
        raise AttributeError(name)

