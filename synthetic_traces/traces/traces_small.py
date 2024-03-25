
"""
Message File processing
-Read the message file. ignore # or whitespace.
-example line-> 0 : cpu0:cache0:wt:req
-so read as index: src, dest, cmd, type.
-Keys: src, dest.

-Store in a dictionary. the key is the src,dest. For example, 'cache 0' 'cpu0'
('cache0', 'cpu0', (0, 2, 25, 26))
0 : cpu0:cache0:wt:req
2 : cpu0:cache0:rd:req
25 : cache0:cpu0:wt:resp
26 : cache0:cpu0:rd:resp
Groups are tuples with the src, dest, and group of indices corresponding to that
"""



#Read in the msg file and extract the pairings in the data flow.
#1 and 2 are a pair if: src1 = dest2, dest1=src2. cmd1=cmd2. if type1 is resp, type2 must be req and vice versa.
def extract_groups_from_msg_file(file_path):
    group_indices = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            # Ignore lines that start with #
            if line.startswith('#'):
                continue  
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


"""
Read a trace txt file into a list. Ignore the delimiters, and stop at -2
"""

#Read in the trace file into a list
def read_trace_file(file_path):
    numbers = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            for part in parts:
                if part == '-1':
                    continue
                elif part == '-2':
                    return numbers
                else:
                    numbers.append(int(part))
    return numbers

"""
For each number in a trace, see if the number is in the group of indices.
for example, 0 is in ('cache0', 'cpu0', (0, 2, 25, 26))
so I will append that number into the group sequence for trace-small-5-cache0-cpu0. 

so the extracted sequence is: 
0 25 2 0 26 25 0 25 2 26 2 26 2 26 2 26 0 2 25 26 2 26 2 0 26 25 0 25 2 26 2 26 0 25 2 26 2 26 0 25 0 25 2 26 0 25 0 25 2 26 2 0 25 26 2 26 2 26 0 
25 2 2 26 26 0 25 0 25 0 25 0 25 0 25 0 25 2 0 26 25 0 25 2 26 2 26 0 25 0 25 2 26 0 25 0 25 0 25 0 25 0 25 0 25 2 2 26 26 0 2 25 26 0 25 0 25 2 2 
26 26 0 2 26 25 2 26 2 26 0 25 2 26 2 26 0 25 2 26 2 26

Write it to a file

"""
#extract the sequences and output into file names based on the src/dest
def extract_sequences(trace, groups, name):
    sequences = []
    
    # Initialize sequences for each group
    group_sequences = {group: [] for group in groups}
    
    # Iterate through the trace list
    for num in trace:
        # Check if the number belongs to any group
        for group in groups:
            if num in group[2]:  # Check if num is in group indices
                group_sequences[group].append(num)
    
    # Write sequences to files
    for group, sequence in group_sequences.items():
        src, dest = group[0], group[1]
        filename = f"{name}-{src}-{dest}.txt"
        with open(filename, "w") as file:
            file.write(" ".join(map(str, sequence)))
        sequences.append(sequence)
    
    return sequences




#functions here
####################################################################
file_path = "synthetic_traces/newLarge.msg"
groups = extract_groups_from_msg_file(file_path)
for g in groups:
    print(g)
####################################################################
# file_path = "trace-small-5.txt"
# trace_list = read_trace_file(file_path)
# print("TRACE LIST", file_path, trace_list)

# sequences = extract_sequences(trace_list, groups, 'trace-small-5')
# print(f"Extracted sequences for {file_path}")
# for seq in sequences:
#     print(seq)
# # ####################################################################
# file_path = "trace-small-10.txt"
# trace_list = read_trace_file(file_path)
# print("TRACE LIST", file_path, trace_list)

# sequences = extract_sequences(trace_list, groups, 'trace-small-10')
# print(f"Extracted sequences for {file_path}")
# for seq in sequences:
#     print(seq)
# # ####################################################################
# file_path = "trace-small-20.txt"
# trace_list = read_trace_file(file_path)
# print("TRACE LIST", file_path, trace_list)

# sequences = extract_sequences(trace_list, groups, 'trace-small-20')
# print(f"Extracted sequences for {file_path}")
# for seq in sequences:
#     print(seq)
# # ####################################################################
