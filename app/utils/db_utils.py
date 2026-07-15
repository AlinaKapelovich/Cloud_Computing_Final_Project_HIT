"""Small MongoDB helpers shared across models."""
from bson import ObjectId
from bson.errors import InvalidId


def to_object_id(value):
    """Convert a string to an ObjectId, or return None if it is not a valid id."""
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def serialize_id(document):
    """Return a copy of a Mongo document with `_id` exposed as a string `id` field."""
    if not document:
        return document
    document = dict(document)
    if "_id" in document:
        document["id"] = str(document["_id"])
    return document
