import os
import glob
import csv

def process_tc_files():
    """
    Finds all .TC files in the current directory, reads them as binary,
    and prints the data before and after the '08 04' hex sequence.
    """
    

    # Use glob to find all files ending with .TC in the current directory
    tc_files = glob.glob("input/*.TC")

    if not tc_files:
        print("No .TC files found in the current directory.")
        return

    print(f"Found {len(tc_files)} .TC file(s).")
    print("-" * 50)

    for file_path in tc_files:
        print(f"Processing file: {file_path}")

        try:
            # Open the file in binary read mode ('rb')
            with open(file_path, 'rb') as f:
                content = f.read()

            decoded_data = decode_binary_data(content)
            parameters_map_raw = decoded_data['ParametersMap']
            measurements_seq_raw = decoded_data['MeasurementsSeq']
            variables_and_units_seq_raw = decoded_data['VariablesAndUnitsSeq']

            parameters_map = process_parameters_map(parameters_map_raw)
            variables_and_units = process_variables_units(variables_and_units_seq_raw)
            variables_with_units = variables_and_units_to_string(parameters_map, variables_and_units)
            measurements = process_measurements(parameters_map, measurements_seq_raw, len(variables_with_units))

            tc_to_csv(file_path, variables_with_units, measurements)

        except IOError as e:
            print(f"  ❌ Error reading file {file_path}: {e}")
        except Exception as e:
            print(f"  ❌ An unexpected error occurred with {file_path}: {e}")

    print("-" * 50)


def tc_to_csv(csvPath: str, variable_names: list[str], values: list[list[str]]) -> None:
    """
    Convert measurement data from a TC-like file into a CSV file.

    Parameters:
        filename (str): Input filename (e.g. "foo.TC")
        variable_names (list[str]): List of variable names for the CSV header
        values (list[list[str]]): 2D list of measurements (rows of values)
    """
    # Derive CSV filename
    path, filename = os.path.split(csvPath)
    base, _ = os.path.splitext(filename)
    csv_filename = f"output/{base}.csv"

    # Create header row: Measurement number + variable names
    header = ["Measurement #"] + variable_names

    # Write CSV
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # Write measurements with numbering
        for i, row in enumerate(values, start=1):
            writer.writerow([i] + row)

    print(f"✅ CSV file saved as: {csv_filename}")

def process_measurements(parameters_map: list, measurements_seq: bytes, number_of_variables: int):
    number1 = numbers_from_bytes(measurements_seq, 0) # Always 0
    number2 = numbers_from_bytes(measurements_seq, 1) # no idea. Checksum???
    number3 = numbers_from_bytes(measurements_seq, 2) # number_of_variables * 4. So how many bites we should take at one time.

    assert(number3 == number_of_variables * 4)

    measurements_seq = measurements_seq[12:]

    all_measurements = []
    i = 0
    first = True

    # Iterates over whole measurement seq
    while 0 < len(measurements_seq):
        # Iterates over each variable in current measurement.
        values = []
        for i in range(number_of_variables):
            # measurement_seq contains indexes into parameters_map. We are taking the index, and moving it to index from 0.
            index = numbers_from_bytes(measurements_seq, i) - 1
            # Not all variables are measured from the start. If measurement is missing, index is set to -1.
            if index == -1:
                values.append("")
            else:
                values.append(parameters_map[index])
        all_measurements.append(values)
        first = False
        # remove the currently processed indexes
        measurements_seq = measurements_seq[4 * number_of_variables:]

    return all_measurements


def variables_and_units_to_string(parameters_map: list, variables_and_units: list):
    """
    Pairs variable names and unit names based on indexes in variables_and_units,
    and looks up the names in the parameters_map list.

    Args:
        parameters_map: A list where the index corresponds to the variable/unit ID.
        variables_and_units: A list of indices. The first half are variables,
                             the second half are units.
    """

    total_length = len(variables_and_units)

    half_length = total_length // 2
    variable_indexes = variables_and_units[:half_length]
    unit_indexes = variables_and_units[half_length:]

    combined_list = []

    for index, item in enumerate(variable_indexes):
        combined_list.append(f"{parameters_map[item - 1]} ({parameters_map[unit_indexes[index] - 1]})")

    return combined_list



def process_variables_units(data: bytes):
    number1 = numbers_from_bytes(data, 0) # no idea.
    number2 = numbers_from_bytes(data, 1) # no idea. Checksum???
    number3 = numbers_from_bytes(data, 2) # length of the data (without the first 3 number). With zeroes et the end. This will NOT be equal to length of the resulting array.

    data = data[12:] # removing first 3 numbers

    #resulting array of numbers
    numbers = []

    i = 0

    while i < len(data):
        # 1. Extract the current 4-byte chunk
        chunk = data[i:i + 4]  # e.g., b'\x0A\x00\x0A\x00'

        # 2. Split the chunk into the number and its required repetition
        number_bytes = chunk[0:2]  # First two bytes (the number)
        repeated_bytes = chunk[2:4]  # Second two bytes (the repetition)

        # 3. Assert that the second two bytes are the same as the first two
        # If this assert fails, the program will halt with an AssertionError.
        assert number_bytes == repeated_bytes, \
            (f"Validation failed at index {i}. Expected repetition of {number_bytes.hex()}, "
             f"but found {repeated_bytes.hex()}.")

        # 4. Convert the 2-byte segment to an integer (little-endian)
        # byteorder='little' means the least significant byte (LSB) is first.
        number = int.from_bytes(number_bytes, byteorder='little')

        if number == 0:
            break

        # 5. Store the number
        numbers.append(number)

        # 6. Advance the index by 4 bytes
        i += 4

    return numbers

def process_parameters_map(data: bytes):
    number1 = numbers_from_bytes(data, 0) # always 0
    number2 = numbers_from_bytes(data, 1) # no idea. Checksum???
    number3 = numbers_from_bytes(data, 2) # length of the resulting array
    data = data[12:] # removing first 3 numbers

    i = 0
    #resulting array of strings
    strings = []

    while i < len(data):
        # first byte is length of the next bytes, we should take into consideration.
        string_length = data[i]
        i += 1

        # Calculate the slice boundaries
        start_of_string = i
        end_of_string = i + string_length - 1

        # The first and last bytes should be always 0. omitting.
        assert(data[start_of_string] == 0)
        assert(data[end_of_string - 1] == 0)
        string_bytes = data[start_of_string + 1:end_of_string - 1]

        #Transforming bytes to ascii
        strings.append(string_bytes.decode('ascii'))

        # ... (decoding and index update)
        i = end_of_string

    assert(number3 == len(strings))
    return strings


def numbers_from_bytes(data: bytes, index = 0):
    return int.from_bytes(data[index * 4: (index + 1) * 4], byteorder='little')

def print_hex(data: bytes):
    print(data.hex(' '))
def decode_binary_data(binary_data: bytes) -> dict:
    """
    Decodes binary data by splitting it into three sections based on separators.

    Args:
        binary_data: The input binary data as a bytes object.

    Returns:
        A dictionary containing the three extracted binary data sections:
        'ParametersMap', 'MeasurementsSeq', and 'VariablesAndUnitsSeq'.
        The values are bytes objects.
    """
    # Define the separators as bytes
    SEP_PARAMETERS_MAP = b'\x00\x00\x10\x00\x02\x00'  # Separator for ParametersMap start
    SEP_MEASUREMENTS_SEQ = b'\x00\x00\x10\x00\x04\x00'  # Separator for MeasurementsSeq start
    SEP_VARIABLES_UNITS_SEQ = b'\x00\x00\x10\x00\x05\x00'  # Separator for VariablesAndUnitsSeq start

    # --- 1. Extract ParametersMap ---
    # From SEP_PARAMETERS_MAP till the end of the file
    try:
        start_parameters_map = binary_data.index(SEP_PARAMETERS_MAP)
        # + len(SEP_PARAMETERS_MAP) is optional here, as the prompt says "from" the separator
        # but usually it's better to exclude the separator itself. We'll include it for safety
        # based on the prompt's literal phrasing 'from the separator... till the end'.
        # However, for structured data splitting, typically the *data* starts *after* the marker.
        # Let's assume the data *starts* after the separator for cleaner sectioning.
        start_parameters_map_data = start_parameters_map + len(SEP_PARAMETERS_MAP)
        ParametersMap = binary_data[start_parameters_map_data:]
    except ValueError:
        print("Parameters map separator not found")
        # Separator not found
        ParametersMap = b''
        start_parameters_map = -1
        # It's important to find this position for the next split
        start_parameters_map_data = -1  # Sentinel value if not found

    # We need to know where the SEP_PARAMETERS_MAP was found for the next step's *end* position.
    # We use the position *where* the separator was found (not the data start)
    end_measurements_seq = start_parameters_map

    # --- 2. Extract MeasurementsSeq ---
    # From SEP_MEASUREMENTS_SEQ till SEP_PARAMETERS_MAP
    try:
        # Find the start of MeasurementsSeq
        start_measurements_seq = binary_data.index(SEP_MEASUREMENTS_SEQ)

        # Calculate the end position. If SEP_PARAMETERS_MAP wasn't found (end_measurements_seq == -1),
        # we can't reliably determine the end, but since it's the *last* one specified,
        # the entire rest of the file *might* be it. But based on the structure, we need the start position.
        if start_measurements_seq != -1 and end_measurements_seq != -1:
            # Data starts after its own separator
            start_measurements_seq_data = start_measurements_seq + len(SEP_MEASUREMENTS_SEQ)
            MeasurementsSeq = binary_data[start_measurements_seq_data:end_measurements_seq]
        else:
            MeasurementsSeq = b''
    except ValueError:
        print("Measurements separator not found")
        # Separator not found
        MeasurementsSeq = b''
        start_measurements_seq = -1

    # We need to know where the SEP_MEASUREMENTS_SEQ was found for the next step's *end* position.
    # We use the position *where* the separator was found
    end_variables_units_seq = start_measurements_seq

    # --- 3. Extract VariablesAndUnitsSeq ---
    # From SEP_VARIABLES_UNITS_SEQ to SEP_MEASUREMENTS_SEQ
    try:
        # Find the start of VariablesAndUnitsSeq
        start_variables_units_seq = binary_data.index(SEP_VARIABLES_UNITS_SEQ)
        # Calculate the end position.
        if start_variables_units_seq != -1 and end_variables_units_seq != -1:
            # Data starts after its own separator
            start_variables_units_seq_data = start_variables_units_seq + len(SEP_VARIABLES_UNITS_SEQ)
            VariablesAndUnitsSeq = binary_data[start_variables_units_seq_data:end_variables_units_seq]
        else:
            VariablesAndUnitsSeq = b''
    except ValueError:
        print("Variables and units separator not found")
        # Separator not found
        VariablesAndUnitsSeq = b''

    return {
        'ParametersMap': ParametersMap,
        'MeasurementsSeq': MeasurementsSeq,
        'VariablesAndUnitsSeq': VariablesAndUnitsSeq,
    }


if __name__ == "__main__":
    process_tc_files()
