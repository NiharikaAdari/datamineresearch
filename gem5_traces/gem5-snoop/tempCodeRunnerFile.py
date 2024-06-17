
    trace = read_trace_from_file('gem5_traces/gem5-snoop/unslicedtrace-1 copy (testing)/unsliced-cpu0-icache0.txt')
    pattern = [0,9]
    result = remove_pattern_from_trace(trace, pattern)
    print(result)