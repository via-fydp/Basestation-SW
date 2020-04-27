from procedure_builder import Procedure

SERVICE_REDUCTION = 5
LAP = 3
SLOW_CHARGE = 2
QUICK_CHARGE = 1

def build_tp_0():
    tp_0 = Procedure("sample_schema.xsd", "FYDP")

    # START STEP 1
    tp_0.add_step(1)
    step1 = tp_0.get_step(1)

    step1.add_reading("Brake Line", "line_pressure_sensor")

    step1.setup().add_action("set_flow", LAP)
    step1.setup().add_action("wait_for_pressure", "pressure_sensor_1", "greater_than", 110)
    step1.setup().add_check("sensor", "pressure_sensor_1", label="pressure_1")
    
    step1.add_substep(0)
    step1.substep(0).add_action("set_flow", SLOW_CHARGE)
    step1.substep(0).add_check("user_validate", "Change to Lap?", True, label="changed_to_lap")

    step1.add_substep(1)
    step1.substep(1).add_action("set_flow", LAP)
    step1.substep(1).add_action("wait", 5)
    step1.substep(1).add_check("user_validate", "Soap check passed?", True, label="soap_passed")

    step1.add_validation("value", "pressure_1", "number", "greater_than", 110)
    step1.add_validation("value", "changed_to_lap", "bool", True)
    step1.add_validation("value", "soap_passed", "bool", True)
    # END STEP 1

    # START STEP 2
    tp_0.add_step(2)
    step2 = tp_0.get_step(2)

    S2_DIALOGUE = "\n".join([
        "PREPARATION:",
        "- wheel chocks applied",
        "- parking brake is released",
        "- LRC Cars: car connected to 480V source",
        "- HEP Cars: water raising system valve must be cut-out (isolated)",
        "- Pressure gauge installed on Brake Cylinder test port",
        "- Brake pipe connected to test device in 'Service Reduction'",
        "- Main Reservoir end hose disconnected ond kept vented to atmosphere",
        "- Brake Pipe and Main Reservoir hoses at other end of the car kept vented to atmosphere"
    ])

    step2.add_substep(0)
    step1.setup().add_action("set_flow", SERVICE_REDUCTION)
    step2.substep(0).add_check("user_validate", S2_DIALOGUE, True, label="validated")

    step2.add_validation("value", "validated", "bool", True)
    # START STEP 2

    # START STEP 3
    tp_0.add_step(3)
    step3 = tp_0.get_step(3)

    step3.setup().add_action("set_flow", SERVICE_REDUCTION)
    step3.add_substep(0)
    step3.substep(0).add_check("user_validate", "Change to Quick Charge", True, label="to_quick")
    step3.substep(0).add_action("set_flow", QUICK_CHARGE)
    step3.add_substep(1)
    step3.substep(1).add_check("user_validate", "Change to Service Reduction", True, label="to_reduction")
    step3.substep(1).add_action("set_flow", SERVICE_REDUCTION)
    step3.add_substep(2)
    step3.substep(2).add_check("user_input", "Does air escape freely?", "bool", label="air_free")
    # TODO: figure out how to save results

    step3.add_validation("value", "air_free", "bool", True)
    # END STEP 3


    # START STEP 4
    tp_0.add_step(4)
    step4 = tp_0.get_step(4)

    step4.setup().add_action("set_flow", "vent_main")
    step4.setup().add_action("set_flow", QUICK_CHARGE)

    step4.add_substep(0)
    step4.substep(0).add_check("user_input", "Select True when the system is charged", True, label=None)

    step4.add_substep(1)
    step4.substep(1).add_action("set_flow", LAP)
    step4.substep(1).add_check("sensor", "brake_line", label="brake_start")
    step4.substep(1).add_action("wait", 60)
    step4.substep(1).add_check("sensor", "brake_line", label="brake_end")

    step4.add_validation("difference", "brake_start", "brake_end", "less_than", 1)
    # END STEP 4


    tp_0.write_and_verify("sample_procedure_output.xml")


if __name__ == "__main__":
    build_tp_0()