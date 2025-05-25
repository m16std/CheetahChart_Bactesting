import hmac
import hashlib
import base64
import requests
from datetime import datetime, timezone

class APIChecker:
    @staticmethod
    def check_api_status(api_key, api_secret, passphrase):
        """Проверяет доступность API."""
        try:
            # Generate the current UTC timestamp with millisecond precision
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            method = "GET"
            request_path = "/api/v5/account/balance"
            body = ""

            # Generate the signature
            message = f"{timestamp}{method}{request_path}{body}"
            signature = base64.b64encode(
                hmac.new(
                    api_secret.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')

            # Set headers
            headers = {
                "OK-ACCESS-KEY": api_key,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": passphrase,
                "Content-Type": "application/json"
            }

            # Send the request
            url = f"https://www.okx.com{request_path}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Код: {response.status_code}, Текст: {response.text}"
        except Exception as e:
            return False, str(e)
