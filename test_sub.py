from supabase import create_client

SUPABASE_URL = "https://uzjhqouxrendjwvhndrq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV6amhxb3V4cmVuZGp3dmhuZHJxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMyNDAzMDcsImV4cCI6MjA4ODgxNjMwN30.O4vmzgQq7QSjxV5bVsdW42TMvnBRfhMFq--UWaeC4Nk"  # From app.py

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    response = supabase.table('subscriptions').insert({
        'phone': '1234567890',
        'plan': 'weekly',
        'amount': 165,
        'status': 'pending'
    }).execute()
    print("SUCCESS INSERT:", response)
except Exception as e:
    print("ERROR INSERT:", e)

