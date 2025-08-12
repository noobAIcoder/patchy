---

artifact_type: global_validation_patterns.yaml
module_name: system
version: 1.0
created_date: 2025-07-24T01:00:00+03:00

email_patterns:
  standard: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Matches typical [user@domain.com](mailto:user@domain.com) addresses

phone_patterns:
  international: '^\+[0-9]{1,3}[0-9]{4,14}$'

# Matches +countrycode and national number (minimum 5 digits, max 17 total)

date_patterns:
  iso8601: '^\d{4}-\d{2}-\d{2}$'

# Matches YYYY-MM-DD dates

custom_patterns:
  property_code:
    regex: '^[A-Z0-9\-]{4,20}$'
    description: >
      Code assigned to a property (uppercase letters, digits, dashes, 4–20 chars)
    examples: ['ABCD-1234', 'A1B2-3456-XYZ']
    counter_examples: ['abcd-1234', 'A!@#-1234']
  image_tag:
    regex: '^[a-z0-9\-_ ]{2,50}$'
    description: >
      Lowercase, numbers, dash, underscore, space, 2–50 chars for tags/captions
    examples: ['balcony view', 'kitchen_island', 'open-plan']
    counter_examples: ['BalconyView', '!!kitchen']

# validations:
# * Only patterns required by project entities and UI have been included.
# * Pattern names/descriptions conform to template.
# * No creative additions; structure matches framework artifact template.

---
