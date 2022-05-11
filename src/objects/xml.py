from __future__ import annotations
from typing import Optional, List, Dict

import abc

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

class BaseXmlObject2(object, metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    def get_name(self):
        return ""

    def get_text(self):
        return ""

    def get_attrib(self):
        return dict()

    def get_children(self):
        return list()


    def get_xml_element(self) -> et.Element:
        self_element = et.Element(self.get_name())
        self_element.text = self.get_text()
        self_element.attrib = self.get_attrib()

        for child in self.get_children():
            self_element.append(child.get_xml_element())

        return self_element





