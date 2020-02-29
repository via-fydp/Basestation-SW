from datetime import datetime
from uuid import uuid4
import xml.etree.ElementTree as ET
from xml.dom import minidom

from lxml import etree

from .procedure_utils import verify_with_schema

class SubStep():

    def __init__(self, etree_parent, etree_substep, substep_id):
        self._id = substep_id
        self._substep_xml = etree_substep
        self._step_id_xml = etree.SubElement(self._substep_xml, 'id')
        self._step_id_xml.text = substep_id

    def add_action(self, fn_name, *params):
        action_xml = etree.SubElement(self._substep_xml, 'action')
        action_xml.text = f"perform:{fn_name}:{params}"

    def add_check(self, sensor_id, *params, label):
        action_xml = etree.SubElement(self._substep_xml, 'action')
        action_xml.text = f"check:{sensor_id}:{params}"

class Step():

    def __init__(self, etree_parent, etree_step, step_id):
        self._id = step_id
        self._step_xml = etree_step
        self._step_id_xml = etree.SubElement(self._step_xml, 'id')
        self._step_id_xml.text = step_id
        self._step_readings = etree.SubElement(self._step_xml, 'readings')
        self._step_controls = etree.SubElement(self._step_xml, 'controls')
        self._step_procedure = etree.SubElement(self._step_xml, 'procedure')
        self._step_validations = etree.SubElement(self._step_xml, 'validations')
        self._setup = SubStep(self._step_xml, etree.SubElement(self._step_procedure, 'setup'), 'setup')

        self._substeps = {}

    def add_reading(self, label, sensor_id):
        reading = etree.SubElement(self._step_readings, 'reading')

        label_xml = etree.SubElement(reading, 'label')
        label_xml.text = label

        sensor_id_xml = etree.SubElement(reading, 'sensor_id')
        sensor_id_xml.text = sensor_id

    def add_validation(self, validation_type, *params):
        validate_xml = etree.SubElement(self._step_validations, 'validation')

        type_xml = etree.SubElement(validate_xml, 'type')
        type_xml.text = validation_type

        parameters_xml = etree.SubElement(validate_xml, 'parameters')
        parameters_xml.text = f"{params}"

    def add_substep(self, substep_id):
        substep = SubStep(self._step_xml, etree.SubElement(self._step_procedure, 'sub_step'), str(substep_id))
        self._substeps[substep_id] = substep

    def setup(self):
        return self._setup

    def substep(self, substep_id):
        return self._substeps[substep_id]


class Procedure():

    def __init__(self, schema, author, test_id=None):
        self._schema = schema

        self._xml_tree = etree.Element('test_procedure')
        etree.register_namespace('xs', 'Via_FYDP')

        created_date = etree.SubElement(self._xml_tree, 'created_date')
        today = datetime.now()
        created_date.text = today.strftime('%Y-%m-%d')

        author_xml = etree.SubElement(self._xml_tree, 'author')
        author_xml.text = author

        test_name = test_id or str(uuid4())
        test_id_xml = etree.SubElement(self._xml_tree, 'test_id')
        test_id_xml.text =test_name

        self._name = test_name
        self._test_steps_xml = etree.SubElement(self._xml_tree, 'steps')
        self._test_steps = {}

    @property
    def name(self):
        return self._name

    def add_step(self, step_num):
        """ Add a step to the Procedure

        Args:
            step_num: an integer step number to add
        """
        step = etree.SubElement(self._test_steps_xml, 'step')
        self._test_steps[step_num] = Step(self._test_steps_xml, step, str(step_num))

        self._test_steps_xml.insert(step_num, step)


    def get_step(self, step_num):
        return self._test_steps[step_num]


    def verify(self):
        """ Verify that the xml structure stored in the procedure adheres to the xml schema """
        verify_with_schema(formatted_xml, self._schema)


    def write_and_verify(self, out_file):
        """ Verify that the xml structure stored in the procedure adheres to the xml schema
        and print to a file if it does

        Args:
            out_file: the output file that the xml document should be written to
        """

        # verify the programmatic representation of the xml
        formatted_xml = minidom.parseString(etree.tostring(self._xml_tree)).toprettyxml(indent="  ")
        print(formatted_xml)
        verify_with_schema(formatted_xml, self._schema)

        # output the xml to a file
        with open(out_file, 'w') as output_file:
            output_file.write(formatted_xml)

        # read in the xml file to ensure that no errors occur during printing or parsing
        with open(out_file, 'r') as read_file:
            read_xml = etree.parse(read_file)
            verify_with_schema(etree.tostring(read_xml), self._schema)