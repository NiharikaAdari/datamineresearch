def generate_routes(indices, pairs):
    routes = []
    used_indices = set()
    memo = {}

    def backtrack(current_route):
        if len(current_route) == (len(indices)//2):
            routes.append(current_route)
            return

        last_index = current_route[-1][1] if current_route else None

        for pair in pairs:
            if pair[0] == last_index or pair[1] == last_index:
                continue

            if pair[0] in used_indices or pair[1] in used_indices:
                continue

            used_indices.add(pair[0])
            used_indices.add(pair[1])
            
            new_route = tuple(sorted(current_route + [pair]))
            if new_route not in memo:
                memo[new_route] = True
                backtrack(current_route + [pair])

            used_indices.remove(pair[0])
            used_indices.remove(pair[1])

    backtrack([])
    return routes