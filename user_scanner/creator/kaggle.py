from ..core.orchestrator import status_validade

def validate_kaggle(user):
   url = f"https://www.kaggle.com/{user}"

   return status_validade(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_kaggle(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
