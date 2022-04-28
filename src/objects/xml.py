from __future__ import annotations
from typing import Optional, List, Dict

import xml.etree.ElementTree as et

class BaseXmlObject(object):
    def __init__(self, name: str, text: str = '', attrib: Dict = dict()):
        self.text = text
        self.name = name
        self.attrib = attrib
        self.children = []

    def add_child(self, child: BaseXmlObject):
        assert isinstance(child, BaseXmlObject)
        self.children.append(child)

    def get_xml_element(self) -> et.Element:
        self_element = et.Element(self.name)
        self_element.text = self.text
        self_element.attrib = self.attrib

        for child in self.children:
            self_element.append(child.get_xml_element())

        return self_element
