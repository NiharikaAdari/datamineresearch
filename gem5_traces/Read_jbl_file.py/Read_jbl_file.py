# For reading a .jbl trace file you need to install joblib library
#   pip install joblib
# The file may contain several traces, when loading the file the traces will be loaded into an array 
# which each index of array is an array of message numbers
# Each message number is associated with a message in the message definition file.

import joblib

def read_trace_file(trace_file):
    traces = 0
    if '.jbl' in trace_file:
        file = joblib.load(trace_file)
        for i in file: # there might be several traces in a single file
            print("\n****************** Trace number :", traces, "***********************\n")
            #file[i] includes all the messages in a single trace
            traces = traces + 1

trace_file_path = "/Users/bardianadimi/Desktop/unsliced-RubelPrintFormat.jbl" # change this to the path of the trace file
read_trace_file(trace_file_path)
