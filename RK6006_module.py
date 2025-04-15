import minimalmodbus


class RK6006:
    def __init__(self, port, baudrate=115200, address=1, modbus_timeout=0.5):
        self.port = port
        self.address = address
        self.instrument = minimalmodbus.Instrument(port=port, slaveaddress=address)
        self.instrument.serial.baudrate = baudrate
        minimalmodbus.TIMEOUT = modbus_timeout

        regs = self._read_registers(0, 15)

        self.sn = regs[1] << 16 | regs[2]
        self.fw = regs[3] / 100
        self.type = int(regs[0])
        self.volts_resolution = 100
        self.amps_resolution = 1000
        self.power_resolution = 100
        self.in_volts_resolution = 100
        self.model = "RK6006"
        self.max_set_voltage = round((regs[14] / self.in_volts_resolution)/1.1 - 1.5, 2)  # max possible output voltage
        self.max_set_current = 6  # max possible output current for the module
        self.max_ocp_current = 6.2  # max OverCurrent Protection current
        self.registers_max_len = 120  # https://github.com/Baldanos/rd6006/blob/master/registers.md

        if self.type != 60066:
            print("Detected Type: ", self.type)
            print("Expected Type: 60066")
            print("Exit the program!")
            exit(0)

    def __repr__(self):
        return f"Model: {self.model}, SN:{self.sn}, FW:{self.fw}"

    def _read_register(self, register):
        try:
            return self.instrument.read_register(register)
        except minimalmodbus.NoResponseError:
            return self._read_register(register)

    def _read_registers(self, start, length):
        try:
            return self.instrument.read_registers(start, length)
        except minimalmodbus.NoResponseError:
            return self._read_registers(start, length)
        except minimalmodbus.InvalidResponseError:
            return self._read_registers(start, length)

    def _write_register(self, register, value):
        try:
            return self.instrument.write_register(register, value)
        except minimalmodbus.NoResponseError:
            return self._write_register(register, value)

    def update_max_set_voltage(self):
        """ Updates the value of max_set_voltage according the current module input voltage """
        self.max_set_voltage = round(self.get_input_voltage()/1.1 - 1.5, 2)

    def print_saved_memory(self, mem=0):
        """ Reads the 4 register of a Memory[0-9] and print on a single line"""
        regs = self._read_registers(mem * 4 + 80, 4)
        print(
            f"M{mem}: {regs[0] / self.volts_resolution: 2.2f}V, "
            f"{regs[1] / self.amps_resolution:1.3f}A, "
            f"OVP: {regs[2] / self.volts_resolution:2.2f}V, "
            f"OCP: {regs[3] / self.amps_resolution:1.3f}A"
        )

    def get_saved_memory(self, mem=0):
        """ Reads the 4 register of a Memory[0-9] and returns a tuple (Voltage, Current, OVP, OCP)"""
        regs = self._read_registers(mem * 4 + 80, 4)
        mem_tuple = ((regs[0] / self.volts_resolution),
                     (regs[1] / self.amps_resolution),
                     (regs[2] / self.volts_resolution),
                     (regs[3] / self.amps_resolution))
        return mem_tuple

    def print_status(self):
        """ Reads all registers and prints most of them"""
        regs = self._read_registers(0, self.registers_max_len)
        self.type = int(regs[0])
        if self.type != 60066:
            print("Detected Type: ", self.type)
            print("Expected Type: 60066")
            print("Exit the program!")
            exit(0)
        print("=== Print Full Status ===")
        print("=== Device ===")
        print(f"Model   : {self.model}")
        print(f"SN      : {(regs[1] << 16 | regs[2]):08}")  # SN is 4 bytes
        print(f"FW      : V{regs[3] / 100}")
        print(f"Input   : {regs[14] / self.in_volts_resolution}V")
        if regs[4]:
            sign = -1
        else:
            sign = +1
        print(f"Int.Temp: {sign * regs[5]}°C")
        if regs[34]:
            sign = -1
        else:
            sign = +1
        ext_temp = sign * regs[35]
        if ext_temp < -40:  # When external temp. sensor is missing, returns -71°C
            ext_temp = "--"
        print(f"Ext.Temp: {ext_temp}°C")
        print("=== Output ===")
        print(f"Voltage : {regs[10] / self.volts_resolution}V")
        print(f"Current : {regs[11] / self.amps_resolution}A")
        print(f"Power   : {(regs[12] <<16 | regs[13]) / self.power_resolution}W")
        print("=== V&A SET ===")
        print(f"Voltage : {regs[8] / self.volts_resolution}V")
        print(f"Current : {regs[9] / self.amps_resolution}A")
        print("=== OXP SET ===")
        print(f"Voltage : {regs[82] / self.volts_resolution}V")
        print(f"Current : {regs[83] / self.amps_resolution}A")
        print("=== Energy ===")
        print(f"Charge  : {(regs[38] <<16 | regs[39])/1000}Ah")
        print(f"Energy  : {(regs[40] <<16 | regs[41])/1000}Wh")
        print("=== Memories ===")
        for m in range(10):
            offset = m * 4 + 80
            print(f"M{m}: {regs[offset] / self.volts_resolution:2.2f}V, "
                  f"{regs[offset+1] / self.amps_resolution:1.3f}A, "
                  f"OVP: {regs[offset+2] / self.volts_resolution:2.2f}V, "
                  f"OCP: {regs[offset+3] / self.amps_resolution:1.3f}A")

        print("=== End Full Status ===")

    def get_input_voltage(self):
        """ Returns the current board input voltage and updates the max_set_voltage value """
        input_voltage = self._read_register(14) / self.in_volts_resolution
        self.max_set_voltage = round(input_voltage/1.1 - 1.5, 2)
        return input_voltage

    def get_set_voltage(self):
        """ Returns the set output voltage, not the current displayed voltage! """
        return self._read_register(8) / self.volts_resolution

    def set_voltage(self, value):
        """ Sets the output voltage """
        if value < 0:
            value = 0
        if value > self.max_set_voltage:
            value = self.max_set_voltage
        self._write_register(8, int(value * self.volts_resolution))

    def get_output_voltage(self):
        """ Returns the actual output voltage, not the set voltage! """
        return self._read_register(10) / self.volts_resolution

    def get_set_current(self):
        """ Returns the set current, not the actual output current! """
        return self._read_register(9) / self.amps_resolution

    def set_current(self, value):
        """ Sets the max output current """
        if value < 0:
            value = 0
        if value > self.max_set_current:
            value = self.max_set_current
        self._write_register(9, int(value * self.amps_resolution))

    def get_output_current(self):
        """ Returns the actual output current, not the set current! """
        return self._read_register(11) / self.amps_resolution

    def get_output_power(self):
        """ Returns the actual output power """
        return (self._read_register(12) << 16 | self._read_register(13)) / self.power_resolution

    def get_capacity_ah(self):
        """ Returns the actual consumed capacity in Ah from the start of the module """
        return (self._read_register(38) << 16 | self._read_register(39)) / 1000

    def get_energy_wh(self):
        """ Returns the actual consumed energy in Wh from the start of the module """
        return (self._read_register(40) << 16 | self._read_register(41)) / 1000

    def get_ovp_voltage(self):
        """ Returns the set OverVoltage Protection voltage"""
        return self._read_register(82) / self.volts_resolution

    def set_ovp_voltage(self, value):
        """ Sets the OverVoltage Protection voltage"""
        if value < 0:
            value = 0
        if value > self.max_set_voltage + 2:
            value = self.max_set_voltage + 2
        self._write_register(82, int(value * self.volts_resolution))

    def get_ocp_current(self):
        """ Returns the set OverCurrent Protection current"""
        return self._read_register(83) / self.amps_resolution

    def set_ocp_current(self, value):
        """ Sets the OverCurrent Protection current"""
        if value < 0:
            value = 0
        if value > self.max_ocp_current:
            value = self.max_ocp_current
        self._write_register(83, int(value * self.amps_resolution))

    def get_temp_internal(self):
        """ Returns board temperature in Celsius"""
        if self._read_register(4):
            return -1 * self._read_register(5)
        else:
            return 1 * self._read_register(5)

    def get_temp_f_internal(self):
        """ Returns board temperature in Fahrenheit"""
        if self._read_register(6):
            return -1 * self._read_register(7)
        else:
            return 1 * self._read_register(7)

    def get_temp_external(self):
        """ Returns external temperature in Celsius"""
        if self._read_register(34):
            return -1 * self._read_register(35)
        else:
            return 1 * self._read_register(35)

    def get_temp_f_external(self):
        """ Returns external temperature in Fahrenheit"""
        if self._read_register(36):
            return -1 * self._read_register(37)
        else:
            return 1 * self._read_register(37)

    def get_enable_state(self):
        """ Returns the actual module output state - 0: OFF, 1: ON """
        return self._read_register(18)

    def set_enable_state(self, value):
        """ Sets the module output state - 0/False: OFF, 1/True: ON """
        value = int(value)
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._write_register(18, value)

    def get_protection_status(self):
        """ Returns the Protection Status - 0: OK, 1: OVP, 2: OCP """
        return self._read_register(16)

    def get_current_output_mode(self):
        """ Returns the current CV/CC mode - 0: CV, 1: CC """
        return self._read_register(17)

    def get_backlight(self):
        """ Returns the current backlight level: 0..5 """
        return self._read_register(72)

    def set_backlight(self, value):
        """ Sets the backlight level: 0..5 """
        if value < 0:
            value = 0
        if value > 5:
            value = 5
        self._write_register(72, value)

    def get_take_out(self):
        """ Returns the current Take_Out state - 0: OFF, 1: ON """
        return self._read_register(67)

    def set_take_out(self, value):
        """ Sets the Take_Out state - 0: OFF, 1: ON """
        value = int(value)
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._write_register(67, value)

    def get_boot_power(self):
        """ Returns the current Boot Power state - 0: OFF, 1: ON """
        return self._read_register(68)

    def set_boot_power(self, value):
        """ Sets the Boot Power state - 0: OFF, 1: ON """
        value = int(value)
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._write_register(68, value)

    def get_buzzer(self):
        """ Returns the current Buzzer state - 0: OFF, 1: ON """
        return self._read_register(69)

    def set_buzzer(self, value):
        """ Sets the Buzzer state - 0: OFF, 1: ON """
        value = int(value)
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._write_register(69, value)

    # Serial port timeouts
    @property
    def read_timeout(self):
        return self.instrument.serial.timeout

    @read_timeout.setter
    def read_timeout(self, value):
        self.instrument.serial.timeout = value

    @property
    def write_timeout(self):
        return self.instrument.serial.write_timeout

    @write_timeout.setter
    def write_timeout(self, value):
        self.instrument.serial.write_timeout = value


# You can run the module as a self check script
if __name__ == "__main__":
    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "VID:PID=1A86:7523" in p[2]:
            print(p)
            rd = RK6006(p[0])
            break
    else:
        raise Exception("Port not found")
    rd.print_status()
