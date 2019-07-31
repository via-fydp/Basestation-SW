from procedure_utils import verify_with_schema

class Proc_Reader():

    __init__(self):
        pass

    def read_procedure_file(self, proc_file):
        # read in the xml file to ensure that no errors occur during printing or parsing
        with open(proc_file, 'r') as read_file:
            read_xml = etree.parse(read_file)
            self._verify_with_schema(etree.tostring(read_xml))

    def get_step(self, proc_file):
        pass

