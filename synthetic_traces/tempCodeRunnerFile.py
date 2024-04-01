                                    # Temporarily sort the trace to handle removal correctly
                    sorted_trace = sorted(remaining_trace)
                    initial_index = sorted_trace.index(initial_node)
                    end_index = sorted_trace.index(end_node)

                    # Ensure the end node is removed after the initial node
                    if initial_index < end_index:
                        sorted_trace.remove(initial_node)
                        sorted_trace.remove(end_node)
                    else:
                        sorted_trace.remove(end_node)
                        sorted_trace.remove(initial_node)

                    updated_remaining_trace = sorted(sorted_trace)  # Sort it back