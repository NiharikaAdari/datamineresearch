import os
#Read in the msg file and extract the pairings in the data flow.
#1 and 2 are a pair if: src1 = dest2, dest1=src2. cmd1=cmd2. if type1 is resp, type2 must be req and vice versa.
def extract_groups_from_msg_file(file_path):
    group_indices = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                continue  # Ignore comments
            elif line:
                parts = [part.strip() for part in line.split(':')]
                if len(parts) == 5:
                    index, src, dest, cmd, type_ = parts
                    key = tuple(sorted((src, dest)))  # Sorting to consider src, dest and dest, src as the same
                    if key not in group_indices:
                        group_indices[key] = []
                    group_indices[key].append(int(index))

    groups = set()  # Avoid duplicates
    for key, indices in group_indices.items():
        src, dest = key
        group = (src, dest, tuple(sorted(indices)))  # Include the indices
        groups.add(group)

    return sorted(groups)  # Return sorted groups




# Read in the trace file into a list of traces
def read_trace_file(file_path):
    traces = []
    with open(file_path, 'r') as file:
        trace = []
        for line in file:
            parts = line.strip().split()
            if not parts:  # If line is empty
                if trace:
                    traces.append(trace)
                    trace = []  # Start a new trace
                continue
            for part in parts:
                if part == '-1':
                    continue
                elif part == '-2':
                    if trace:
                        traces.append(trace)
                        trace = []  # Start a new trace
                else:
                    trace.append(int(part))
        if trace:  # If there's any remaining trace
            traces.append(trace)
    return traces


# Extract the sequences and output into filenames based on the src/dest
def extract_sequences(traces, groups, folder_name_prefix):
    parent_folder = f"multipleTraces-synthetic"
    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)

    for i, trace in enumerate(traces, start=1):
        trace_folder = os.path.join(parent_folder, f"{folder_name_prefix}trace-{i}")
        os.makedirs(trace_folder)

        group_sequences = {group: [] for group in groups}

        # Iterate through the trace list
        for num in trace:
            # Check if the number belongs to any group
            for group in groups:
                if num in group[2]:  # Check if num is in group indices
                    group_sequences[group].append(num)

        # Write sequences to files for each trace
        for group, sequence in group_sequences.items():
            src, dest = group[0], group[1]
            filename = os.path.join(trace_folder, f"{folder_name_prefix}-{src}-{dest}.txt")
            with open(filename, "w") as file:
                file.write(" ".join(map(str, sequence)))





#functions here
####################################################################
file_path = "synthetic_traces/newLarge.msg"
groups = extract_groups_from_msg_file(file_path)
for g in groups:
    print(g)
####################################################################
file_path = "synthetic_traces/multipleTraces-synthetic.txt"
traces = read_trace_file(file_path)
extract_sequences(traces, groups, 'multipleTraces-synthetic')

####################################################################
file_path = "synthetic_traces/multipleTraces-syntheticSmall.txt"
traces = read_trace_file(file_path)
extract_sequences(traces, groups, 'multipleTraces-syntheticSmall')

####################################################################
file_path = "synthetic_traces/multipleTraces-syntheticLarge.txt"
traces = read_trace_file(file_path)
extract_sequences(traces, groups, 'multipleTraces-syntheticLarge')

####################################################################
file_path = "synthetic_traces/RubelMultiTrace.txt"
traces = read_trace_file(file_path)
extract_sequences(traces, groups, 'RubelMultiTrace')

