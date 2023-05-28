import os
import json
import datetime
import csv
from getpass import getpass
from googlemaps import Client

# Access the API key from the environment variable
API_KEY = os.getenv("GOOGLE_API_KEY")


# Cache functions
def save_cache(cache):
  with open('api_cache.json', 'w') as f:
    json.dump(cache, f)


def load_cache():
  try:
    with open('api_cache.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError:
    return {}


# Load the cache when the script starts
api_cache = load_cache()


def get_place_details(church_name):
  # Check the cache first
  if church_name in api_cache:
    return api_cache[church_name]

  gmaps = Client(key=API_KEY)
  result = gmaps.places(query=f"{church_name} in Nashville")

if result["status"] == "OK":
        place_id = result["results"][0].get("place_id")
        lat_lng = result["results"][0]["geometry"]["location"]
        address = result["results"][0].get("formatted_address")
        # remove country name from the address
        address = ', '.join(address.split(', ')[:-1])
        address_with_country = result["results"][0].get("formatted_address")

        # Save to cache
        api_cache[church_name] = (place_id, lat_lng, address, address_with_country)
        save_cache(api_cache)

        return place_id, lat_lng, address, address_with_country
    return None, None, None, None


def get_church_url_and_phone(place_id):
  if not place_id:
    return None, None

  gmaps = Client(key=API_KEY)
  result = gmaps.place(place_id=place_id,
                       fields=["website", "formatted_phone_number"])

  if result["status"] == "OK":
    website = result["result"].get("website")
    phone_number = result["result"].get("formatted_phone_number")
    return website, phone_number
  return None, None


def write_geojson(churches):
geojson = {
        "type":
        "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [church["lng"], church["lat"]]  # note the change here
            },
            "properties": church,
        } for church in churches],
    }
    with open("church_json.geojson", "w") as f:
        json.dump(geojson, f)


def main():
  with open("small church list.csv", mode="r") as infile:
    reader = csv.reader(infile)

    # Skip header row and add new columns for place ID, latitude, longitude, address, phone number, and last updated
    header = next(reader)
    header += [
      "Place ID", "Latitude", "Longitude", "Address", "Phone Number",
      "Last Updated"
    ]

    churches = []

   for row in reader:
        church_name = row[0]
        place_id, lat_lng, address, address_with_country = get_place_details(church_name)  # note the change here

        if lat_lng:
            lat, lng = lat_lng["lat"], lat_lng["lng"]  # note the change here
        else:
            lat, lng = None, None  # note the change here

        church_url, phone_number = get_church_url_and_phone(place_id)

        church = {
            "church_name": church_name,
            "website": church_url,
            "place_id": place_id,
            "lat": lat,  # note the change here
            "lng": lng,  # note the change here
            "address": address,
            "address_with_country": address_with_country,  # added this new property
            "phone_number": phone_number,
            "last_updated": datetime.datetime.now().isoformat(),
        }
        churches.append(church)

    # Write churches to a CSV file
    with open('church_data_output.csv', 'w', newline='') as outfile:
      writer = csv.DictWriter(outfile, fieldnames=churches[0].keys())
      writer.writeheader()
      writer.writerows(churches)

    # Write churches to a GeoJSON file
    write_geojson(churches)


if __name__ == "__main__":
  main()
