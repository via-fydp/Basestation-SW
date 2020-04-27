""" This file contains tools for building an xml representation of a test
procedure, compliant with the sample scema contained at the root of this project.
An example xml scema that  output file can be found in the root directory of this
project.

These procedure files are intended to be delivered to a front-end user interface
so that the interface can generate the correct components for display to the user
and make the correct requests to step through the test procedure.
"""

from datetime import datetime
from uuid import uuid4
import xml.etree.ElementTree as ET
from xml.dom import minidom

from lxml import etree

from procedure_utils import verify_with_schema

class SubStep():
    """ A substep contains actions and checks to perform in the system """

    def __init__(self, etree_parent, etree_substep, substep_id):
        self._id = substep_id
        self._substep_xml = etree_substep
        self._step_id_xml = etree.SubElement(self._substep_xml, 'id')
        self._step_id_xml.text = substep_id

    def add_action(self, fn_name, *params):
        """ Add an action to the substep.

        Args:
            fn_name: a function name for the server to execute when performing the step
            params: the parameters that should be passed to the server function
        """
        action_xml = etree.SubElement(self._substep_xml, 'action')
        action_xml.text = f"perform:{fn_name}:{params}"

    def add_check(self, ref, *params, label):
        """ Add a check to the substep.

        Args:
            ref: the label of what is being checked (sensor, user, etc.)
            params: parameters to determine a successful check
            label: the label that is used to store the result of this check
        """
        action_xml = etree.SubElement(self._substep_xml, 'action')
        action_xml.text = f"check:{label}:{ref}:{params}"

class Step():
    """ A step contains a selection of pressure readings to display, validations
    to confirm that the step has passed and controls that should be accessible
    to the user while the step is being displayed.
    """

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
        """ Add an xml representation of a pressure reading that should be displayed
        during this test step. Readings consist of a label for display to the user
        and sensor_id of the corresponding sensor that should be used to reference
        the appropriate data stored by the server.

        Args:
            label: the label that should be displayed to the user
            sensor_id: the sensor id who's value should be displayed

        Ex.
        <reading>
          <label>Brake Line</label>
          <sensor_id>brake_line_pressure_sensor</sensor_id>
        </reading>
        """
        reading = etree.SubElement(self._step_readings, 'reading')

        label_xml = etree.SubElement(reading, 'label')
        label_xml.text = label

        sensor_id_xml = etree.SubElement(reading, 'sensor_id')
        sensor_id_xml.text = sensor_id

    def add_validation(self, validation_type, *params):
        """ Add a validation metric to determine whether the step has succeeded.
        These validations are intended to be performed by the server and correlated
        by label with a 'check' that is performed during this step.

        Logic has not yet been implemented for validation, meaning that the structure
        may be changed. This first-pass implementation requires a type of validation
        so that the server knows what kind of check it is performing, plus any
        parameters that can be used to perform the validation check.

        validation_type: the type of validation that is being performed - used
            by the server to correctly identify how the validation should be
            performed
        params: any parameters needed for this type of validation

        Ex.
        <validation>
          <type>value</type>
          <parameters>('pressure_1', 'number', 'greater_than', 110)</parameters>
        </validation>
        """
        validate_xml = etree.SubElement(self._step_validations, 'validation')

        type_xml = etree.SubElement(validate_xml, 'type')
        type_xml.text = validation_type

        parameters_xml = etree.SubElement(validate_xml, 'parameters')
        parameters_xml.text = f"{params}"

    def add_substep(self, substep_id):
        """ Substeps are intended to provide a procedural order of actions within
        a test step. Substeps do not contain validations, but provide a useful way
        to organize barriers to order the sequence of events during a step of testing.

        Args:
            substep_id: an id label applied to this label for reference and retrieval

        Ex.
        <sub_step>
          <id>0</id>
          <action>perform:set_flow:(2,)</action>
          <action>check:changed_to_lap:user_validate:('Change to Lap?', True)</action>
        </sub_step>
        <sub_step>
          <id>1</id>
          <action>perform:set_flow:(3,)</action>
          <action>perform:wait:(5,)</action>
          <action>check:soap_passed:user_validate:('Soap check passed?', True)</action>
        </sub_step>
        """
        substep = SubStep(self._step_xml, etree.SubElement(self._step_procedure, 'sub_step'), str(substep_id))
        self._substeps[substep_id] = substep

    def setup(self):
        """ The setup step is a special step that is designed to allow prompting
        the user or setup of initial conditions before the current test is enacted.
        """
        return self._setup

    def substep(self, substep_id):
        """ Get a substep with a specific label

        Args:
            substep_id: the id of the step to be retrieved
        """
        return self._substeps[substep_id]


class Procedure():
    """ The hghest level of the test procedure, containing metadata about the
    procedure, scema and author. Also contains the steps of the prcedure. """

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
        """ Return a step with the provided label. """
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