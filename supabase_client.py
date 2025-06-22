from supabase import create_client, Client

url = "https://enylqxswgbvfhmhmycia.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVueWxxeHN3Z2J2ZmhtaG15Y2lhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNjI1MDQsImV4cCI6MjA2NTkzODUwNH0.aOQrlXpq5QfQPP-Q6IhWzsMW-pUe5QJcfT_r0xV0WRg"

supabase: Client = create_client(url, key)
