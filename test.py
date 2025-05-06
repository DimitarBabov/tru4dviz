import requests

def get_weather_forecast(lat, lon):
    base_url = f"https://api.weather.gov/points/{lat},{lon}"
    
    # Step 1: Get the grid forecast endpoint
    response = requests.get(base_url)
    if response.status_code != 200:
        return f"Error fetching location data: {response.status_code}"
    
    data = response.json()
    forecast_url = data['properties']['forecast']

    # Step 2: Fetch the forecast data
    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        return f"Error fetching forecast data: {forecast_response.status_code}"

    forecast_data = forecast_response.json()
    periods = forecast_data['properties']['periods']

    # Step 3: Prepare forecast info
    forecast_info = []

    for period in periods:
        # Extracting necessary forecast information for each period
        info = {
            "name": period.get("name"),  # Daytime or Nighttime name
            "start_time": period.get("startTime"),
            "end_time": period.get("endTime"),
            "max_temp": period.get("temperature") if period['isDaytime'] else None,
            "min_temp": period.get("temperature") if not period['isDaytime'] else None,
            "wind_speed": period.get("windSpeed"),
            "wind_gusts": period.get("windGust"),
            "wind_direction": period.get("windDirection"),
            "weather_condition": period.get("shortForecast"),
        }
        forecast_info.append(info)

    return forecast_info


# Example usage with latitude/longitude
lat, lon = 39.3643, -74.4229 # Los Angeles, CA
forecast = get_weather_forecast(lat, lon)

# Printing the forecast
for period in forecast:
    print(f"{period['name']} (From {period['start_time']} to {period['end_time']})")
    print(f"Max Temp: {period['max_temp']}°F, Min Temp: {period['min_temp']}°F")
    print(f"Wind Speed: {period['wind_speed']}, Wind Gusts: {period['wind_gusts']}")
    print(f"Wind Direction: {period['wind_direction']}")
    print(f"Weather Condition: {period['weather_condition']}")
    print("-" * 50)
