from __future__ import annotations
from typing import Dict, List, Optional, Callable, Union
from lxml import etree
from collections.abc import Iterable

from ..utils import convertstr
from ..config.constants import VUNITS


class IndexedList(list):
    def __init__(self, *args, key=lambda x: x):
        super().__init__(*args)
        self.key = key
        self._index = {self.key(val): idx for idx, val in enumerate(self)}

    def _update_index(self, start=0):
        for idx in range(start, len(self)):
            self._index[self.key(self[idx])] = idx

    def append(self, value):
        super().append(value)
        self._index[self.key(value)] = len(self) - 1

    def extend(self, values):
        start = len(self)
        super().extend(values)
        self._update_index(start)

    def insert(self, index, value):
        super().insert(index, value)
        self._update_index(index)

    def remove(self, value):
        super().remove(value)
        self._update_index()

    def pop(self, index=-1):
        value = super().pop(index)
        self._update_index(index)
        return value

    def clear(self):
        super().clear()
        self._index.clear()

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._update_index(index)

    def __delitem__(self, index):
        super().__delitem__(index)
        self._update_index(index)

    def __repr__(self):
        return f"{super().__repr__()} (Index: {self._index})"

    def index_of(self, value):
        """Returns the index of the given value, or raises a ValueError if not found."""
        return self._index.get(value, -1)


class VolumeUnitsMixin:
    @property
    def vunits(self):
        return VUNITS


class PhMixin:
    @property
    def pH(self):
        return self.ph


class XmlMixin:
    def get_xml_attributes(self) -> Dict:
        '''
        Generate the attributes of the xml 
        '''
        return {
            attr: convertstr(getattr(self, attr))
            for attr in self._attributes
        }

    def get_children(self) -> Union[Iterable[XmlMixin], object]:
        '''
        Get a list of children
        '''
        children = []
        for attr in self._children:
            child = getattr(self, attr)
            if child is None:
                continue
            if isinstance(child, XmlMixin):
                # This can include the iterable xmlelements
                children.append(child)
            # Exclude strings
            elif isinstance(child, Iterable) and not isinstance(child, str):
                # Also allow iterables to be pass as children
                # All items in the iterable will be used as a child
                for item in child:
                    if not isinstance(item, XmlMixin):
                        raise Exception(
                            'Iterable must only contain XmlMixin objects')
                    children.append(item)
            else:
                # As a default case cast the child to a str
                if isinstance(child, float):
                    string = f'{child:g}'
                else:
                    string = str(child)
                children.append(self.string_child(attr, string))
        return children

    def get_xml_text(self) -> str:
        '''
        Can be overridden by a child class for dynamic behaviour
        '''
        return self._xml_text

    def get_xml_name(self) -> str:
        '''
        Can be overridden by a child class for dynamic behaviour
        '''
        return self._xml_name

    def get_xml_element(self) -> etree.Element:
        self_element = etree.Element(
            self.get_xml_name(),
            attrib=self.get_xml_attributes())
        self_element.text = self.get_xml_text()
        children = self.get_children()
        for child in children:
            self_element.append(child.get_xml_element())

        return self_element

    def string_child(self, name, string) -> BaseXml:
        return BaseXml(
            name=name, text=string
        )

    def __repr__(self):
        return self.print_self()

    def print_self(self, children=False) -> str:
        # TODO Include printing of the children
        return f'{self._xml_name}:{self._xml_text}:{self.get_xml_attributes()}'

    def to_xml(self, as_string: bool = False):
        root = self.get_xml_element()
        xml = etree.ElementTree(root)
        if as_string:
            etree.indent(xml, space='  ')
            xml = etree.tostring(xml, xml_declaration=True,
                                 pretty_print=True, encoding='utf-8').decode()
        return xml


class BaseXml(XmlMixin):
    # __slots__ = ('_xml_text', '_xml_name', '_attributes', '_children')

    def __init__(self, *,
                 name: str = '',
                 text: str = '',
                 attributes: Dict[str, str] = [],
                 children: List[str] = []
                 ):
        self._xml_name = name
        self._xml_text = text
        self._attributes = attributes
        self._children = children


class ListXml(list, XmlMixin):
    '''
    A class that can be used as a list but implements the functionality to turn its contents into
    an xml file
    '''

    def __init__(self, *args,
                 name: Optional[str] = '',
                 text: Optional[str] = '',
                 attributes: Optional[List[str]] = [],
                 xml_constructor_fn: Optional[Callable] = None
                 ):
        list.__init__(self, *args)
        self.xml_constructor_fn = xml_constructor_fn
        self._xml_name = name
        self._xml_text = text
        self._attributes = attributes

    def get_children(self) -> List[XmlMixin]:
        if self.xml_constructor_fn is not None:
            return [self.xml_constructor_fn(x) for x in self]
        return self


class SetXml(set, XmlMixin):
    '''
    A class that can be used as a set but implements the functionality to turn its contents into
    an xml file
    '''

    def __init__(self, *args,
                 name: Optional[str] = '',
                 text: Optional[str] = '',
                 attributes: Optional[List[str]] = [],
                 xml_constructor_fn: Optional[Callable] = None
                 ):
        set.__init__(self, *args)
        self.xml_constructor_fn = xml_constructor_fn
        self._xml_name = name
        self._xml_text = text
        self._attributes = attributes

    def get_children(self) -> List[BaseXml]:
        if self.xml_constructor_fn is not None:
            return [self.xml_constructor_fn(x) for x in self]
        return list(self)


class IndexedListXml(IndexedList, XmlMixin):
    '''
    A class that can be used as a set but implements the functionality to turn its contents into
    an xml file
    '''

    def __init__(self, *args,
                 name: Optional[str] = '',
                 text: Optional[str] = '',
                 attributes: Optional[List[str]] = [],
                 xml_constructor_fn: Optional[Callable] = None,
                 key=lambda x: x
                 ):
        IndexedList.__init__(self, *args, key=key)
        self.xml_constructor_fn = xml_constructor_fn
        self._xml_name = name
        self._xml_text = text
        self._attributes = attributes

    def get_children(self) -> List[BaseXml]:
        if self.xml_constructor_fn is not None:
            return [self.xml_constructor_fn(x) for x in self]
        return list(self)
