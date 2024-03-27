import json

token_data = {
    'token': '2krOzImij41k7vJthL550hXzS_tZSRG_zat0oJ3Y7Bj41DsBdUiBmwbymQ2vPEFq',
    'expires': '1741899803769'
}

# Write the token data to token.json
with open('token.json', 'w') as file:
    json.dump(token_data, file)


