import torch
from torch_geometric.data import Data
from collections import Counter
import os
import itertools
import joblib

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





#Given a group, find all the possible causal pairings.
def find_causal_pairs(indices, successors_dict):
    causal_pairs = set()
    for i in range(len(indices)):
        for j in range(i+1, len(indices)):
            if isCausal(indices[i], indices[j], successors_dict):
                causal_pairs.add((indices[i], indices[j]))
            if isCausal(indices[j], indices[i], successors_dict):
                causal_pairs.add((indices[j], indices[i]))
    return causal_pairs






def findgroup(group_names, groups):
    group_names = group_names.split('-')
    group_indices = None
    for group in groups:
        if group_names[0] in group[0] and group_names[1] in group[1]:
            group_indices = group[2]
            break
    if group_indices is None:
        return []  # Group not found
    return group_indices

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
Gets the successors of a node in the graph.

Parameters:
- node_index: The index of the node
- successors_dict: A dictionary mapping each node to list of successors.

Returns:
- A list of tuples, each representing a successor with its index, source, and destination.
"""


def get_successors(node_index, successors_dict):
    node_info = successors_dict.get(node_index)
    if node_info:
        successors_info = [(succ, successors_dict[succ]['src'], successors_dict[succ]['dest']) for succ in node_info['successors']]
        return successors_info
    return []

""" Generate all causal pairs for a specific index, considering its successors. """
def get_causal_pairs_for_index(node_index, successors_dict):
    causal_pairs = []
    successors_info = get_successors(node_index, successors_dict)
    for succ, src, dest in successors_info:
        causal_pairs.append((node_index, succ))
    return causal_pairs
"""
Prints detailed path information for the successors of the specified node.
    
    Parameters:
    - node_index: The index of the node to query.
    - successors_dict: A dictionary mapping each node to its details and list of successors.
"""

def print_successor_info(node_index, successors_dict):

    if node_index in successors_dict:
        node_info = successors_dict[node_index]
        print(f"Node {node_index} (Source: {node_info['src']}, Destination: {node_info['dest']}) has successors:")
        for succ in node_info['successors']:
            succ_info = successors_dict.get(succ, {})
            print(f"  Successor: {succ}, Path: {succ_info.get('src', 'N/A')} -> {succ_info.get('dest', 'N/A')}")
    else:
        print(f"Node {node_index} has no successors or does not exist in the graph.")


"""
Checks if there is a causal connection between two nodes in the graph.

Parameters:
- node_index1: The index of the first node.
- node_index2: The index of the second node.
- successors_dict: A dictionary mapping each node to its details and list of successors.

Returns:
- True if there is a causal connection, False otherwise.
"""
def isCausal(node_index1, node_index2, successors_dict):
    successors_of_node1 = successors_dict.get(node_index1, {}).get('successors', [])
    successors_of_node2 = successors_dict.get(node_index2, {}).get('successors', [])
    
    if (node_index2 in successors_of_node1) or (node_index1 in successors_of_node2):
        return True
    return False

"""
Prints whether two nodes are causally connected or not.

Parameters:
- node_index1: The index of the first node.
- node_index2: The index of the second node.
- successors_dict: A dictionary mapping each node to its details and list of successors.
"""
def print_causality_info(node_index1, node_index2, successors_dict):
    successors_of_node1 = successors_dict.get(node_index1, {}).get('successors', [])
    successors_of_node2 = successors_dict.get(node_index2, {}).get('successors', [])
    
    if node_index1 in successors_of_node2:
        print(f"Node {node_index2} is causal to Node {node_index1}.")
    elif node_index2 in successors_of_node1:
        print(f"Node {node_index1} is causal to Node {node_index2}.")
    else:
        print(f"Nodes {node_index1} and {node_index2} are not connected.")



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



class Node:
    def __init__(self, remaining_trace, used_pairs=None, acceptance_ratio=None, route_index=None, used_nodes=None):
        self.remaining_trace = remaining_trace
        self.used_pairs = used_pairs or []
        self.acceptance_ratio = acceptance_ratio
        self.route_index = route_index
        self.used_nodes = used_nodes or []


def find_binary_pattern(trace, successors_dict, group_name, groups, pairs):
    route_acceptance_ratios = {}

    # Get the pairs list from indices
    group_indices = list(set(trace))
    causal_pairs = find_causal_pairs(group_indices, successors_dict)
    print("causal pairs")


    class Node:
        def __init__(self, remaining_trace, used_pairs=None, acceptance_ratio=None, used_nodes=None):
            self.remaining_trace = remaining_trace
            self.used_pairs = used_pairs if used_pairs else []
            self.acceptance_ratio = acceptance_ratio
            self.used_nodes = used_nodes if used_nodes else []


    root = Node(trace)


    def calculate_acceptance_ratio(remaining_trace, original_trace):
        orphaned_nodes = len(remaining_trace)
        return 1 - (orphaned_nodes / len(original_trace))


    def explore_node(node):
        flag = 0
        seen = []
        for index, value in enumerate(node.remaining_trace):
            if value in node.used_nodes:  # Skip exploring if value is part of used nodes
                continue
            if value in seen:
                continue
            seen.append(value)
            for pair in causal_pairs:
                if pair[0] == value:
                    if(pair[0] in node.used_nodes or pair[1] in node.used_nodes):
                        continue
                    updated_remaining_trace = remove_binary_pattern(pair, node.remaining_trace)
                    if len(updated_remaining_trace) == len(node.remaining_trace):
                        continue
                    flag = 1

                    new_used_pairs = node.used_pairs + [pair]
                    child_node = Node(remaining_trace=updated_remaining_trace, used_pairs=new_used_pairs, used_nodes=node.used_nodes)
                    child_node.used_nodes.append(pair[0])
                    child_node.used_nodes.append(pair[1])
                    explore_node(child_node)
                    
                    
            if(flag==1):
                break
                    
        # Leaf node
        if(flag==0):
            # print("leaf:\nremainingtrace:", node.remaining_trace)
            node.acceptance_ratio = calculate_acceptance_ratio(node.remaining_trace, trace)
            print("acceptance", node.acceptance_ratio)
            route_acceptance_ratios[len(route_acceptance_ratios)] = (node.used_pairs, node.acceptance_ratio)
            print((node.used_pairs, node.acceptance_ratio))

    explore_node(root)
    return route_acceptance_ratios




def compute_common_causal_pairs(folder_path, output_file, successors_dict, groups):
    with open(output_file, 'w') as f:
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".txt"):
                file_path = os.path.join(folder_path, file_name)
                trace = read_trace_from_file(file_path)
                print("\nProcessing file:", file_path)
                
                # Extract group name from the file name
                group_name = file_name.split("-")[-2] + "-" + file_name.split("-")[-1].replace(".txt", "")
                print("\nGroup:", group_name)
                
                # Find pairs for the extracted group name
                group_indices = list(set(trace))
                causal_pairs = find_causal_pairs(group_indices, successors_dict)

                causal_pairs_info = find_binary_pattern(trace, successors_dict, group_name, groups, causal_pairs)
                sorted_pairs = sorted(causal_pairs_info.items(), key=lambda x: x[1][1], reverse=True)
                top_pairs_with_ratio_1 = set()
                top_pairs_without_ratio_1 = set()
                for route_index, (route, acceptance_ratio) in sorted_pairs:
                    if acceptance_ratio == 1:
                        top_pairs_with_ratio_1.add((tuple(route), acceptance_ratio))
                    elif acceptance_ratio > 0 and len(top_pairs_without_ratio_1) < 5:
                        top_pairs_without_ratio_1.add((tuple(route), acceptance_ratio))
        
                top_pairs_without_ratio_1 = sorted(top_pairs_without_ratio_1, key=lambda x: x[1], reverse=True)
                f.write("-" * 25 + "\n")
                f.write(f"File: {file_name}, Group: {group_name}, Indices: {group_indices}\n")
                
                # Write pairs with acceptance ratio 1
                for route, acceptance_ratio in top_pairs_with_ratio_1:
                    f.write(f"BinaryPatterns: {route}, Acceptance Ratio: {acceptance_ratio}\n")
                # Write top 5 pairs without ratio 1
                for route, acceptance_ratio in top_pairs_without_ratio_1:
                    f.write(f"BinaryPatterns: {route}, Acceptance Ratio: {acceptance_ratio}\n")
                f.write("-" * 25 + "\n")
                print("Processing completed for file:", file_path)

    print(f"Results written to {output_file}")



def remove_binary_pattern(pair, trace):
    # Find all occurrences of the binary pattern and mark them
    marked_trace = [0] * len(trace)
    for i in range(len(trace)):
        if trace[i] == pair[0]:
            marked_trace[i] = 1
        elif trace[i] == pair[1]:
            marked_trace[i] = 2

    # Remove pairs from the trace
    new_trace = []
    i = 0
    pair = -1
    toremove = []
    firsthalf = []
    secondhalf = []
    remove = 0

    while i < len(trace):
        if marked_trace[i] == 1:
            firsthalf.append(i) #add index for first part of potential pair
            i+=1
            continue
        if marked_trace[i] == 2 and len(firsthalf)!=0:
            if(firsthalf[0] < i): #if the index is before this
                remove = firsthalf.pop(0) #remove first thing in popped
            toremove.append(remove) #the index of the first part of the pair
            toremove.append(i) #the index of the second part of the pair

        else:
            new_trace.append(trace[i]) #unpaired index, part of pattern but not pair.
        i+=1
    new_trace = [trace[i] for i in range(len(trace)) if i not in toremove]
    return new_trace




if __name__ == "__main__":
    file_path = "gem5_traces/gem5-snoop/defSnoop-RubelPrintFormat.msg"
    messages, sections = read_messages_from_file(file_path)
    data, initial_nodes, terminating_nodes, successors_dict = construct_causality_graph(messages, sections)
    
    groups = extract_groups_from_msg_file(file_path)
    for g in groups:
        print(g)


    ########### testing removal of pattern from trace
    # trace = [0, 0, 25, 2, 2, 25, 0, 25, 2, 2, 0, 25, 0, 25, 0, 25, 2, 2, 2, 2]
    # pair = (25,2)
    # result = remove_binary_pattern(pair,trace)
    # print(result)


    folder_path = "gem5_traces/gem5-snoop/unslicedtrace-1 copy"
    output_file = "gem5_traces/gem5-snoop/unslicedtrace-1-binarypatterns.txt"
    compute_common_causal_pairs(folder_path, output_file, successors_dict, groups)



