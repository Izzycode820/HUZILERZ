# Query complexity middleware for GraphQL
# IMPORTANT: Prevents expensive nested queries and DoS attacks

from graphql import GraphQLError


class ComplexityMiddleware:
    """
    Limit query complexity to prevent abuse

    Security: Prevents expensive nested queries
    Example: Limit depth to 10 levels
    """

    MAX_DEPTH = 10
    MAX_COMPLEXITY = 1000

    def resolve(self, next, root, info, **kwargs):
        """
        Middleware resolve method
        """
        # Calculate query depth
        if hasattr(info, 'field_asts') and info.field_asts:
            depth = self._calculate_depth(info.field_asts[0])

            if depth > self.MAX_DEPTH:
                raise GraphQLError(
                    f"Query too complex. Max depth: {self.MAX_DEPTH}, got: {depth}"
                )

        # Calculate complexity score
        complexity = self._calculate_complexity(info)
        if complexity > self.MAX_COMPLEXITY:
            raise GraphQLError(
                f"Query too complex. Max complexity: {self.MAX_COMPLEXITY}, got: {complexity}"
            )

        return next(root, info, **kwargs)

    def _calculate_depth(self, node, depth=0):
        """Recursively calculate query depth"""
        if not hasattr(node, 'selection_set') or not node.selection_set:
            return depth

        return max(
            [self._calculate_depth(field, depth + 1)
             for field in node.selection_set.selections]
        )

    def _calculate_complexity(self, info, complexity=0):
        """
        Calculate query complexity score

        Simple scoring:
        - Each field: 1 point
        - Each nested level: multiplier
        - Lists: count * complexity
        """
        if not hasattr(info, 'field_nodes') or not info.field_nodes:
            return complexity

        for field_node in info.field_nodes:
            complexity += self._calculate_node_complexity(field_node)

        return complexity

    def _calculate_node_complexity(self, node, multiplier=1):
        """Calculate complexity for a single node"""
        complexity = 1 * multiplier  # Base complexity for this field

        if hasattr(node, 'selection_set') and node.selection_set:
            for field in node.selection_set.selections:
                # Increase multiplier for nested fields
                complexity += self._calculate_node_complexity(field, multiplier * 2)

        return complexity