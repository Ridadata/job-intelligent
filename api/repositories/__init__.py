"""Repository layer — thin wrappers around Supabase table operations.

One repository per database table. Repositories return dicts or domain objects.
They never raise HTTP exceptions.
"""
