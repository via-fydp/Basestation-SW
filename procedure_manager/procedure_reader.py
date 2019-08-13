from lxml import etree

from procedure_utils import verify_with_schema

class Proc_Reader():

    def __init__(self, schema, proc_file):
        self._schema = schema
        self._xml_tree = None

        self._read_procedure_file(proc_file)

    def _read_procedure_file(self, proc_file):
        """ Read in the xml file to ensure that no errors occur during printing or parsing """
        with open(proc_file, 'r') as read_file:
            read_xml = etree.parse(read_file)
            verify_with_schema(etree.tostring(read_xml), self._schema)

        self._xml_tree = read_xml

    def get_step(self, test_id, step_id):
        """ Get the xml for a test step """
        pass

