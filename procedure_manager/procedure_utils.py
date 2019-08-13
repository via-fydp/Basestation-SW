import xml.etree.ElementTree as ET
from xml.dom import minidom

from lxml import etree

def verify_with_schema(xml_str, schema_file):
    """ Verify the fiven xml string against the Procedure's xml schema

    Args:
        xml_str: an xml string to verify
        schema_file: the xsd schema file to validate against
    """

    xmlschema_doc = etree.parse(open( schema, "r", encoding="utf-8"))
    xmlschema = etree.XMLSchema(xmlschema_doc)
    xmlschema.assertValid(etree.XML(xml_str))