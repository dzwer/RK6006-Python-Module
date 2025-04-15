
from RK6006_module import RK6006

import serial.tools.list_ports
from time import sleep as wait

time_to_settle = 0.75  # In seconds. There is about 200ms Up and Down settle time for the output voltage.
set_voltage = 5  # In Volts
set_current = 2  # In Amperes

print("------------------")
print("List all COM ports:")
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(p)

# Automatic search for the RK6006 module. Will not work if there are other CH340 USB/UART converters connected!
print("------------------")
for p in ports:
    if "VID:PID=1A86:7523" in p[2]:
        print("Used COM port: ", p)
        rk_module = RK6006(p[0])
        break
else:
    print("No CH340 device found!\nExit the program!")
    exit(0)

# If there are 2 or more RK6006 modules, or other CH340 USB/UART converters connected, then use manual set of COM port!
# Also, if Baudrate and Address are changed in the module, you have to set them too:
# module_com_port = 'COM13'
# module_baudrate = 38400
# module_address = 5
# rk_module = RK6006(module_com_port, module_baudrate, module_address)

print("------------------")
print("Check if output is enabled. If ON -> turn OFF")
output_state = rk_module.get_enable_state()
if output_state:
    print("Output State: ON")
    print("Output State changed to OFF!")
    rk_module.set_enable_state(False)
else:
    print("Output State: OFF")

print("------------------")
print("Module full status:")
rk_module.print_status()

print("------------------")
print("Set Voltage to: ", set_voltage, "V")
rk_module.set_voltage(set_voltage)
print("Current Set Voltage: ", rk_module.get_set_voltage(), 'V')
output_voltage = rk_module.get_output_voltage()
print("Current Output Voltage: ", output_voltage, "V")

print("Set Current to: ", set_current, "A")
rk_module.set_current(set_current)
print("Current Set Current: ", rk_module.get_set_current(), 'A')
output_current = rk_module.get_output_voltage()
print("Current Output Current: ", output_current, "A")

output_power = rk_module.get_output_power()
print("Current Output Power: ", output_power, 'W')

print("------------------")
print("Enable the Output")
rk_module.set_enable_state(True)

wait(time_to_settle)

output_voltage = rk_module.get_output_voltage()
print("Current Output Voltage: ", output_voltage, "V")
output_current = rk_module.get_output_current()
print("Current Output Current: ", output_current, "A")
output_power = rk_module.get_output_power()
print("Current Output Power: ", output_power, 'W')

print("------------------")
print("Disable the Output")
rk_module.set_enable_state(False)
output_state = rk_module.get_enable_state()
if output_state:
    print("Output State: ON")
else:
    print("Output State: OFF")

wait(time_to_settle)

print("------------------")
output_voltage = rk_module.get_output_voltage()
print("Current Output Voltage: ", output_voltage, "V")
output_current = rk_module.get_output_current()
print("Current Output Current: ", output_current, "A")
output_power = rk_module.get_output_power()
print("Current Output Power: ", output_power, 'W')
print("------------------")
