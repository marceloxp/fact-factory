class FactFactoryError(Exception):
    """Base error for the application."""


class InstanceNotFoundError(FactFactoryError):
    """No .fact-factory instance could be located."""


class InstanceAlreadyExistsError(FactFactoryError):
    """A .fact-factory instance already exists at the target path."""


class NotFoundError(FactFactoryError):
    """Requested resource was not found."""


class ConflictError(FactFactoryError):
    """Operation conflicts with current state."""


class ValidationError(FactFactoryError):
    """Input validation failed."""


class EmbeddingError(FactFactoryError):
    """Embedding generation failed."""
