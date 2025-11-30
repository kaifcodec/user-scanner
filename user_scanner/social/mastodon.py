from ..core.orchestrator import status_validade

def validate_mastodon(user):
    url = f"https://mastodon.social/@{user}"

    return status_validade(url, 404, 200, follow_redirects = True)

if __name__ == "__main__":
   try:
       import httpx
   except ImportError:
       print("Error: 'httpx' library is not installed.")
       exit()

   user = input ("Username?: ").strip()
   result = validate_mastodon(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
