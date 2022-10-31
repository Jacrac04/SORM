from email import message


class BaseError(Exception):
    """Base class for all SORM errors."""

    def __init__(self, message=None):
        if message:
            self.message = message
        
            
    def __str__(self):
        return self.message
    
class PrimaryKeyError(BaseError):
    """Raised when the primary key is being attempted to be modified."""
    message = "Primary key cannot be modified."

class ForeignKeyError(BaseError):
    """Raised when the foreign key is being attempted to be modified without using the relationship"""
    message = "Foreign key cannot be modified directly. Use the relationship."