from procedure_reader import Proc_Reader
from pprint import pprint as pp


if __name__ == "__main__":
    procedure = Proc_Reader("sample_schema.xsd", "output.xml")
    print(procedure)
    print('\n\n\n\nStart Iter')
    procedure.get_dict_proc()