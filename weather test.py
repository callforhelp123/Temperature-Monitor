import requests

# Define the API URL
owm_api_key = "5f1d3a5a193fe9ed245cd087ddc305a9"

weather = requests.get(
    f"https://api.openweathermap.org/data/2.5/onecall?lat={47.6}&lon={-122.3}&exclude=minutely&appid={owm_api_key}&units=imperial")
weather = weather.json()
temp = weather["current"]["temp"]
print(temp)

