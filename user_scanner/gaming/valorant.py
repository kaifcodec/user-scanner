import httpx
from httpx import ConnectError, TimeoutException
import json;

def validate_valorant(user):
    """
    Checks if a valorant username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """
    
    valorant_name = user.replace("#", "%23"); # this replaces valorant tags, with %23
    url = "https://api.tracker.gg/api/v2/valorant/standard/profile/riot"; # track.gg endpoint
    complete_url = f"{url}/{valorant_name}"; # forms a compelte url
    
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
        'sec-fetch-dest': "document",
    }
    
    try:
        response = httpx.get(complete_url, headers = headers, timeout = 3)
        status = response.status_code
        result = response.json(); # endpoint results
        
        if "errors" in result: # if a user is private or available
            if "We could not find the player" in result["errors"][0]["message"]: # if the user is available
                return 1
            elif "This profile is still private." in result["errors"][0]["message"]: # if the user is taken, but private
                return 0
        
        if "data" in result: # if there was a existing player
            return 0 
            
    except (ConnectError, TimeoutException):
        return 2
    except Exception as e:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_valorant(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
