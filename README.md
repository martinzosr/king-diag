# Introduction
I have bought Kingbolen S800 diagnostic, because of some problems with my car. It has a possibility to record the data into the device, for later diagnostics. But to look at the data in the device is very impractical.

# How to
The logs are stored in storage/ThinkCar/ThinkTool/images/ (you can connect the diagnostic to your PC as any other android device).
If the logs you are seraching for are not there yet, try to restart the diagnostics, or disconnect and connect it back.

Copy the TC files into input directory. Run the decoder `python3 decoder.py`.

The CSV file will be generated into the output directory. You can process it with Excell (or any excell like program).

I have started to write simple ui for viewing the data (ui.py), but then I have solved my issue, so have no motivation to finish it.

# Protocol
The file is binary file, and you can use tools like `GHex` to read it.

It consists of 3 main parts

-
