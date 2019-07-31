from procedure_builder import Procedure

LAP = 3
SLOW_CHARGE = 2

def build_tp_0():
    tp_0 = Procedure("test_schema.xsd", "FYDP")

    
    tp_0.add_step(1)
    step1 = tp_0.get_step(1)

    step1.add_reading("Brake Line", "line_pressure_sensor")

    step1.setup().add_action("set_flow", LAP)
    step1.setup().add_check("line_pressure_sensor", "greater_than", 110)
    
    step1.add_substep(0)
    step1.substep(0).add_action("set_flow", SLOW_CHARGE)
    step1.substep(0).add_check("user_validate", "Change to Lap?", True)

    step1.add_substep(1)
    step1.substep(1).add_action("set_flow", LAP)
    step1.substep(1).add_action("wait", 5)
    step1.substep(1).add_check("user_validate", "Soap check passed?", True)

    tp_0.write_and_verify("output.xml")


if __name__ == "__main__":
    build_tp_0()