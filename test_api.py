python
# In test_api.py

def validate_story_response(response: requests.Response) -> Dict[str, Any]:
    # ... (existing code for success, story_id, story, word_count, max_words validation)

    # Validate optional fields if present
    if "premise" in data:
        if not isinstance(data["premise"], dict):
            raise APIValidationError("Field 'premise' must be a dict if present")
        # Add more granular validation for premise structure
        if "idea" not in data["premise"] or not isinstance(data["premise"]["idea"], str):
            raise APIValidationError("Field 'premise.idea' must be a string")
        if "character" not in data["premise"] or not isinstance(data["premise"]["character"], dict):
            raise APIValidationError("Field 'premise.character' must be a dict")
        # Add validation for sub-fields of character within premise if relevant
        if not isinstance(data["premise"]["character"].get("name"), str):
             raise APIValidationError("Field 'premise.character.name' must be a string")
        # ... more character sub-field validation ...

    if "outline" in data:
        if not isinstance(data["outline"], dict):
            raise APIValidationError("Field 'outline' must be a dict if present")
        # Add more granular validation for outline structure (e.g., sections, plot points)
        if "sections" not in data["outline"] or not isinstance(data["outline"]["sections"], list):
            raise APIValidationError("Field 'outline.sections' must be a list")
        # ... more outline sub-field validation ...

    # If character is expected in the top-level response, add its validation here:
    # if "character" in data:
    #     if not isinstance(data["character"], dict):
    #         raise APIValidationError("Field 'character' must be a dict if present")
    #     if "name" not in data["character"] or not isinstance(data["character"]["name"], str):
    #         raise APIValidationError("Field 'character.name' must be a string")
    #     # ... other character fields ...

    return data