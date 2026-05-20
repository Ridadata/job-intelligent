"""Reset Bronze processed flags and clear Silver table for re-transformation."""
import os
from supabase import create_client

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
sb = create_client(url, key)

# 1. Clear Silver table (job_offers)
# Delete all rows — need to use a filter that matches everything
result = sb.table("job_offers").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print(f"Cleared job_offers: {len(result.data)} rows deleted")

# 2. Reset processed flag on all Bronze rows
result = sb.table("raw_job_offers").update({"processed": False}).eq("processed", True).execute()
print(f"Reset processed flag: {len(result.data)} rows")

# 3. Verify counts
raw = sb.table("raw_job_offers").select("id", count="exact").execute()
silver = sb.table("job_offers").select("id", count="exact").execute()
print(f"raw_job_offers: {raw.count}, job_offers: {silver.count}")
