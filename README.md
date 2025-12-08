# Introduction
I have bought Kingbolen S800 diagnostic, because of some problems with my car. It has a possibility to record the data into the device, for later diagnostics. But to look at the data in the device is very impractical.

# How to
The logs are stored in storage/ThinkCar/ThinkTool/images/ (you can connect the diagnostic to your PC as any other android device).
If the logs you are searching for are not there yet, try to restart the diagnostics, or disconnect and connect it back.

Copy the TC files into input directory. Run the decoder `python3 decoder.py`.

The CSV file will be generated into the output directory. You can process it with Excell (or any excell like program).

I have started to write simple ui for viewing the data (ui.py), but then I have solved my issue, so have no motivation to finish it.

# Protocol
The file is binary file, and you can use tools like `GHex` to read it.

In following text this namespace will be used: 
- *Variable* - one measured car property. `Rail pressure`, `Blower motor on`, `Brake boost pressure`, etc.
- *Measurement* - one measured value for one variable. EG. In the second sequence, `Rail pressure` was measured as `24.3MPa`.

The binary file consists of 4 main parts

1. Header of the file. Did not decode it yet
2. The map between variables and units
3. The sequence of measurements
4. The sequence of variables and units

These parts were found by creating small files (1 variable 4 measurements, 3 variables 1 measurement etc.) and finding similarities. This took a few days, but eventually by looking at walls of numbers long enough, I was able to find the basic structure. Then it took a few more days of experimenting.

All of the parts (except the header) follows this structure:
- 4 bytes separator
- 4 bytes I have no idea about
- 4 bytes of probably checksum, not confirmed yet
- length of the section
- data

The following descriptions are not in file order, just to be more understandable.

### Sequence of variables and units
Starts at separator `00 00 10 00 02 00`, continues until end of the file.

This mixes all of the variables, units, measurement values and car identification. It is one big array. After the 4 bytes of structure described above, next byte dictates the length of next variable/unit/info. Then is a zero byte. Then the variable/unit/info. Then another zero byte. Then the next lenght variable.
This is really easy to spot in the GHex. Fun fact, I guess somewhere here lies the reason, why you can not record more than 256 variables.

### Map between variables and units
Starts at `00 00 10 00 05 00`, ends at `00 00 10 00 04 00`.

This part creates a link between variables and units. It creates this link by addressing the `sequence of variables and units` array in 4 bytes little endian numbers. For example, if you measure `Rail pressure`, this parts tells you that the measurements are in `MPa`. Fun fact, even when your diagnostic is set to different units, the file always uses metric units.

### The sequence of measurements
Starts at `00 00 10 00 04 00`, ends at `00 00 10 00 02 00`.

This part creates a link between measurement value and variable. It is long array of 4 bytes little endian numbers that links to the `sequence of variables and units`. The order is Variable 1 Measurement 1, Variable 2 Measurement 1, ..., Variable 1 Measurement 2, Variable 2 Measurement2...

### Header of the file 
Starts at the file start, continues until separator `00 00 10 00 05 00`.

Some data about the file, the car, probably version of the reader/software is stored here. Not important enough for me to invest time to decode it.


# State of this project
This project was done to debug a specific problem on my car, that my ordinary repair shop, or the dealer could not solve. It is in working state, and it currently works for every saved file I have used it on.
It was written in Python, with heavy usage of AI. AI did not help with finding the correct protocol, but it was used to create the implementation.
The naming in the program is not consistent with this README file. It took me a few weeks to figure out how to properly name/describe the data in the files.
And thanks to this program I was able to find out issue with my car, so there is currently no drive for me to make it prettier. I just hope I will not have to get back to this program ever again :D

# Disclaimer
When I have started to record data with this diagnostic, I have contacted Kingbolen to find out, if there is any way to export this data to PC, to view it at large screen.
They said NO, and to use their diagnostic.
For some reason it seems that they do not want you to use their files in your PC. So I would not count on having this tool at your disposal. It takes only one update to add encryption to the files.

Also, this project is only for illustration purposes only. 