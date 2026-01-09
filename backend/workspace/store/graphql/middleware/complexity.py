"""
Query Complexity Middleware for GraphQL API

Prevents DoS attacks by limiting query complexity
Critical for production security and performance
"""

from graphql import GraphQLError


class ComplexityMiddleware:
    """
    Limit query complexity to prevent DoS attacks

    Security: Prevents overly complex queries that could overload the server
    Performance: Ensures predictable query execution times
    """

    MAX_COMPLEXITY = 1000

    def resolve(self, next, root, info, **kwargs):
        # Calculate query complexity
        complexity = self._calculate_complexity(info.field_nodes)

        if complexity > self.MAX_COMPLEXITY:
            raise GraphQLError(
                f"Query complexity {complexity} exceeds maximum {self.MAX_COMPLEXITY}"
            )

        return next(root, info, **kwargs)

    def _calculate_complexity(self, nodes, depth=0):
        """
        Simple complexity calculation based on field count and depth

        In production, consider using graphql-query-complexity library
        for more sophisticated calculations
        """
        complexity = 0

        for node in nodes:
            # Base complexity for each field
            complexity += 1

            # Add depth penalty
            complexity += depth * 2

            # Recursively calculate complexity for nested fields
            if hasattr(node, 'selection_set') and node.selection_set:
                complexity += self._calculate_complexity(
                    node.selection_set.selections,
                    depth + 1
                )

        return complexity