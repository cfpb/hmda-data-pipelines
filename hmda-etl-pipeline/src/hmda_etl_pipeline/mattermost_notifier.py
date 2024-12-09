import requests
import json

def post_mm_message(mm_url: str, msg: str) -> None:
  """ Post a mattermost message.

  Args:
      msg (str): The message to post in mattermost
  """
  
  url = mm_url
  message = {
        'username': 'kedro-data-publisher',
        'text': msg
      }
    
  # Send payload as HTTP Post Request to Webhook URL
  r = requests.post(url, data=json.dumps(message))
  r.raise_for_status()