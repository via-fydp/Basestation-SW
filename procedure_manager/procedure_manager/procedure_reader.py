from lxml import etree
import xmltodict as xd

from .procedure_utils import verify_with_schema
from pprint import pprint as pp

class Proc_Reader():
    instance = None

    def __init__(self, schema=None, proc_file=None):
        if schema and proc_file:
            Proc_Reader.instance = Proc_Reader.__Proc_Reader(schema, proc_file)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __str__(self):
        return str(self.instance) 

    class __Proc_Reader:
        def __init__(self, schema, proc_file):
            self._schema = schema
            self._xml_tree = None
            self._proc_dict = None
            self.cur_step = 1

            self._read_procedure_file(proc_file)

        def __str__(self):
            return etree.tostring(self._xml_tree).decode("utf-8") 

        def _read_procedure_file(self, proc_file):
            """ Read in the xml file to ensure that no errors occur during printing or parsing """
            with open(proc_file, 'r') as read_file:
                read_xml = etree.parse(read_file)
                verify_with_schema(etree.tostring(read_xml), self._schema)

            self._xml_tree = read_xml

        def get_dict_proc(self):
            proc_dict = {
                "created_date": None,
                "author": None,
                "test_id": None,
                "steps": {},
            }

            proc_dict['created_date'] = self._xml_tree.find('created_date').text
            proc_dict['author'] = self._xml_tree.find('author').text
            proc_dict['test_id'] = self._xml_tree.find('test_id').text

            # retrieve steps
            for step in self._xml_tree.iter(tag='step'):
                s_id = step.find('id').text
                proc_dict['steps'][s_id] = {
                    "readings": {},
                    "validations": [],
                    "controls": {},
                    "setup": {},
                    "procedure": {
                        "substeps": {},
                    },
                }
                step_dict = proc_dict['steps'][s_id]

                for reading in step.find('readings').iter(tag='reading'):
                    sensor_id = reading.find('sensor_id').text
                    step_dict['readings'][sensor_id] = None

                for validation in step.find('validations').iter(tag='validation'):
                    v_type = validation.find('type').text
                    v_params = validation.find('parameters').text
                    step_dict['validations'].append((v_type, v_params))


                setup = step.find('procedure').find('setup')
                step_dict['setup'] = etree.tostring(setup).decode("utf-8")

                for substep in step.find('procedure').iter(tag='sub_step'):
                    actions = []
                    sub_id = substep.find('id').text

                    for action in step.iter(tag='action'):
                        actions.append(action.text)

                    step_dict['procedure']['substeps'][sub_id] = actions

                # etree.tostring(e).decode("utf-8")
                # print(etree.tostring(e).decode("utf-8"))

            self._proc_dict = proc_dict

        def get_step(self, test_id=None, step_id=None):
            """ Get the xml for a test step """
            # steps = self._xml_tree.findall(".//step")
            # for s in steps:
            #     print(etree.tostring(s).decode("utf-8"))
            #     attrib = s.get('id')
            # print(self._proc_dict)

            if not self._proc_dict:
                return {}

            step = self._proc_dict['steps'][str(self.cur_step)]
            self.cur_step = self.cur_step + 1

            print(f'Step: {step}')

            return step


