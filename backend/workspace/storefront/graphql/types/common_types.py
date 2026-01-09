# Common GraphQL types used across the schema

import graphene


class PaginationInfo(graphene.ObjectType):
    """
    Pagination metadata for cursor-based pagination
    """
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    start_cursor = graphene.String()
    end_cursor = graphene.String()
    total_count = graphene.Int()



class ErrorType(graphene.ObjectType):
    """
    Standard error type for GraphQL responses
    """
    field = graphene.String()
    message = graphene.String()
    code = graphene.String()


class MutationResult(graphene.ObjectType):
    """
    Standard mutation result type
    """
    success = graphene.Boolean(required=True)
    message = graphene.String()
    errors = graphene.List(ErrorType)


# Base connection class for pagination
class BaseConnection(graphene.Connection):
    """
    Base connection class with total count
    """
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()