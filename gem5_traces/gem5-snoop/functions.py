import torch
from torch_geometric.data import Data
from collections import Counter
import os
import joblib
import pickle
import itertools
from itertools import zip_longest

"""
Reads messages from a specified file and organizes them into sections.
    Parameters:
    - file_path: Path to the file containing the messages.
    
    Returns:
    - messages: A list of messages, each represented as a tuple (index, src, dest).
    - sections: A list of sections, each containing a list of message strings.
    
"""
def read_messages_from_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip().split('#')
    sections = [section.strip().split('\n') for section in content if section.strip()]
    messages = []
    for section in sections:
        for line in section:
            if line:
                parts = line.split(':')
                index, src, dest = int(parts[0].strip()), parts[1].strip(), parts[2].strip()
                messages.append((index, src, dest))
    return messages, sections


# Read in the msg file and extract the pairings in the data flow.
# 1 and 2 are a pair if: src1 = dest2, dest1=src2. cmd1=cmd2. if type1 is resp, type2 must be req and vice versa.
def extract_groups_from_msg_file(file_path):
    group_indices = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                continue  # Ignore comments
            elif line:
                parts = [part.strip() for part in line.split(':')]
                if len(parts) == 4:
                    index, src, dest, type_ = parts
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





#Given a file, add all causal pairs to a list
def find_causal_pairs(file_path):
    pairs = set()  # Using a set to automatically handle duplicate pairs

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()  # Remove any leading/trailing whitespace
            if line:  # Check if the line is not empty
                try:
                    first, second = map(int, line.split('_'))
                    pairs.add((first, second))
                except ValueError as e:
                    print(f"Skipping line due to error: {e}")

    return pairs



"""
Constructs a causality graph from the given messages.
    
    Parameters:
    - messages: A list of messages, each represented as a tuple (index, src, dest).
    - sections: A list of sections from the file, used to determine initial and terminating nodes.
    
    Returns:
    - A Data object representing the graph, sets of initial and terminating nodes, and a dictionary of successors.
    """

def construct_causality_graph(messages, sections):
    edge_list = []
    initial_nodes = set(int(line.split(':')[0].strip()) for line in sections[0] if line)
    terminating_nodes = set(int(line.split(':')[0].strip()) for line in sections[-1] if line)
    successors_dict = {}  # Adjusted to hold more detailed info
    
    for index, src, dest in messages:
        if index not in successors_dict:
            successors_dict[index] = {'src': src, 'dest': dest, 'successors': []}
        for _, s, d in messages:
            if dest == s and index not in terminating_nodes and _ not in initial_nodes:
                edge_list.append((index, _))
                successors_dict[index]['successors'].append(_)
                if _ not in successors_dict:
                    successors_dict[_] = {'src': s, 'dest': d, 'successors': []}

    edge_index = torch.tensor(list(zip(*edge_list)), dtype=torch.long)
    return Data(edge_index=edge_index), initial_nodes, terminating_nodes, successors_dict



"""
Reads a trace from a file and returns it as a list of integers.

Parameters:
- file_path: Path to the file containing the trace.

Returns:
- A list of integers representing the trace.
"""

def read_trace_from_file(file_path):
    with open(file_path, 'r') as file:
        trace = file.read().strip().split()
    return [int(index) for index in trace]

def read_trace_file(trace_file):
    traces = joblib.load(trace_file)
    return [int(index) for index in traces[0]]

"""
    Find patterns in the trace and calculate acceptance ratios for each pattern.

    Args:
    - trace (list): List of integers representing the trace.
    - patterns (list): A list of patterns (each a list of numbers) to find in the trace.

    Returns:
    - pair_acceptance_ratios: List of tuples representing pairs and their acceptance ratios.

"""

def find_acceptance_ratios(trace, patterns):
    
    # print("initial trace", trace)
    # print("initial trace", trace)

    # List to track acceptance ratios for each pair
    pattern_acceptance_ratios = []
    pattern_acceptance_ratios = []


    # Initialize pointers for patterns
    pointers = list(range(len(patterns)))


    while pointers:

        #reset the set of used_numbers
        used_numbers = set()

        # restore original trace for each pass
        remaining_trace = trace[:]    

        # List to track the patterns to be marked as removed
        patterns_to_remove = set()


        break_outer = False
        pattern_skip_count = 0

        for pointer_index, pointer in enumerate(pointers):
            # print(remaining_trace)

            pattern = patterns[pointer]


            # Skip pattern if it has already used numbers to get through unique patterns first before refreshing trace (come back to it later)
            for num in pattern:
                if num in used_numbers:
                    # print("skip pattern")
                    break_outer = True 
                    pattern_skip_count += 1
            if break_outer and pattern_skip_count <=15:
                break_outer = False
                continue
            elif break_outer:
                break_outer = False
                break
            
            print(f"\nTrying pattern {pointer_index + 1}/{len(pointers)}: {pattern}")

            # print("removing:", pattern)
            updated_remaining_trace = remove_pattern_from_trace(remaining_trace, pattern)
           
            remaining_count = Counter(updated_remaining_trace)                                                     
            remaining_count = Counter(updated_remaining_trace)                                                     
            original_count = Counter(remaining_trace)
            orphans = sum(remaining_count[num] for num in pattern)
            original = sum(original_count[num] for num in pattern)


            remaining_trace = updated_remaining_trace


            remaining_trace = updated_remaining_trace

            # Calculate acceptance ratio for the pair
            if(original!=0):
                acceptance_ratio = 1 - (orphans / original)
                print("Acceptance ratio:", acceptance_ratio)
            else:
                acceptance_ratio = 0
                print("pattern",pattern, "dne")

            # Append the pattern and its acceptance ratio to the list
            pattern_acceptance_ratios.append((pattern, acceptance_ratio))
            pattern_acceptance_ratios.append((pattern, acceptance_ratio))

            # Update used numbers and remaining trace
            used_numbers.update(pattern)
            # print("used numbers: ", used_numbers)
        
            # Mark pair for removal
            patterns_to_remove.add(pointer)

        # Update pointers to exclude removed patterns
        pointers = [pointer for pointer in pointers if pointer not in patterns_to_remove]



    print(pattern_acceptance_ratios, len(pattern_acceptance_ratios))
    return pattern_acceptance_ratios
    print(pattern_acceptance_ratios, len(pattern_acceptance_ratios))
    return pattern_acceptance_ratios


"""
Computes acceptance ratios of each pattern from a list of patterns on a trace and writes results to an output folder.
    Parameters:
    - trace: pass in a trace file
    - output_folder: Path to the output folder to write results.
    - patterns: pass in the list of patterns to get ratios from 
"""


def compute_pattern_ratios(trace, output_folder, patterns):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    #Find the acceptance ratio for the list of patterns 
    #Find the acceptance ratio for the list of patterns 
    patterns_info = find_acceptance_ratios(trace, patterns)

    # Filter and sort pairs based on acceptance ratio
    # filtered_pairs = [(pair, ratio) for pair, ratio in causal_pairs_info if ratio > 0.5]
    filtered_patterns = [(pattern, ratio) for pattern, ratio in patterns_info]
    sorted_patterns = sorted(filtered_patterns, key=lambda x: x[1], reverse=True)

    # Write results to a separate file
    output_file_path = os.path.join(output_folder, f"Patterns_AcceptanceRatios.txt")
    number = 1
    with open(output_file_path, 'w') as f:
        f.write(f"{'-' * 25}\n")
        for pattern, acceptance_ratio in sorted_patterns:
            f.write(f"{number}. {pattern}, Acceptance Ratio: {acceptance_ratio}\n")
            number += 1

        f.write(f"{'-' * 25}\n")
        print("Processing completed for file:", file_path)

    print(f"Results written to {output_folder}")



    """
    Remove occurrences of a specified pattern from a trace list.

    Args:
    - trace (list): The trace list from which the pattern occurrences should be removed.
    - pattern (list): The pattern (sequence of numbers) to be removed from the trace.

    Returns:
    - list: A new trace list with the specified pattern occurrences removed.

    Notes:
    - hash table-based indexing and pointer manipulation for efficiency
    """

def remove_pattern_from_trace(trace, pattern):

    # Initialize buckets. Every number in pattern has a bucket to track indices
    buckets = {num: [] for num in pattern}
    
    # Fill buckets with indices
    for index, num in enumerate(trace):
        if num in buckets:
            buckets[num].append(index)
    # print("buckets", buckets)

    to_remove = set()    
    currentindices = []

    #pointer array for pattern indices in buckets (instead of pop)
    pointers = [0] * len(pattern)

    #iterate through first bucket, or first number in pattern 
    for index in buckets[pattern[0]]:

        currentindices = [index]
        # print("current indices: ", currentindices)
        valid_pattern = True

        #check subsequent buckets
        for j in range(1, len(pattern)):
            # print("checking bucket of", pattern[j], " in ", pattern)

            # Find the smallest index in the current bucket that is larger than the last index in currentindices, and greater than any already used
            while pointers[j] < len(buckets[pattern[j]]) and buckets[pattern[j]][pointers[j]] <= currentindices[-1]:
                # print("traversing bucket.", buckets[pattern[j]][pointers[j]], "which is index ", pointers[j])
                pointers[j] += 1

            #once it finds an index that is greater than the current one, add to the patern
            if pointers[j] < len(buckets[pattern[j]]):
                # print("index found from bucket.", buckets[pattern[j]][pointers[j]])
                currentindices.append(buckets[pattern[j]][pointers[j]])
                pointers[j] += 1
            else:
                valid_pattern = False
                break 
                valid_pattern = False
                break 

        # If currentindices match the pattern length, add to to_remove set
        if valid_pattern and len(currentindices) == len(pattern):
            # print("valid pattern found. indices:", currentindices)
            to_remove.update(currentindices)
       
    # Remove the pattern indices from the trace
    new_trace = [trace[i] for i in range(len(trace)) if i not in to_remove]
    return new_trace



# Function to extract patterns
def extract_patterns_from_rows(rows):
    # Create a list of lists to store patterns
    extracted_patterns = []

    # Use zip_longest to handle rows with different lengths
    for patterns in zip_longest(*rows, fillvalue=None):
        # Filter out None values
        valid_patterns = [pattern for pattern in patterns if pattern is not None]
        if valid_patterns:
            extracted_patterns.append(valid_patterns)

    return extracted_patterns




if __name__ == "__main__":
    file_path = "gem5_traces/gem5-snoop/defSnoop-RubelPrintFormat.msg"
    messages, sections = read_messages_from_file(file_path)
    data, initial_nodes, terminating_nodes, successors_dict = construct_causality_graph(messages, sections)
    
    # groups = extract_groups_from_msg_file(file_path)
    # for g in groups:
    #     print(g)


    ########### testing removal of pattern from trace
    # trace = read_trace_from_file('gem5_traces/gem5-snoop/unslicedtrace-1 copy (testing)/test.txt')
    # pattern = [1,2,3,4]
    # result = remove_pattern_from_trace(trace, pattern)
    # print(result)

    
    
    trace = read_trace_from_file('gem5_traces/gem5-snoop/unslicedtrace-1 copy (testing)/test.txt')
    output_folder = "gem5_traces/gem5-snoop/unslicedtrace-1-patterns"
    file = "gem5_traces/gem5-snoop/localPatterns.txt"


    with open('gem5_traces/gem5-snoop/allPatterns.data', 'rb') as f:
       allPatterns = pickle.load(f)

    # Extract patterns
    patterns_by_column = extract_patterns_from_rows(allPatterns)

    # Combine all pattern lists into one giant list
    allPatterns = [pattern for sublist in patterns_by_column for pattern in sublist]

    # # Iterate through the extracted patterns
    compute_pattern_ratios(trace, output_folder, allPatterns)





    

    





