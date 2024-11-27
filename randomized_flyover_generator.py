import math
import random
import xml.etree.ElementTree as ET
from shapely.geometry import shape, Point, Polygon
import os
import sys

# Function to calculate the distance between two latitude/longitude points in kilometers
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Function to generate a random KML file with camera flythroughs
def generate_random_kml(region_center, radius, points_count, altitude=1000, speed=100, polygon=None):
    # speed is in km/h
    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
<Document>
    <name>Random Flythrough</name>
    <gx:Tour>
        <name>Random Tour</name>
        <gx:Playlist>
"""
    kml_footer = """
        </gx:Playlist>
    </gx:Tour>
</Document>
</kml>
"""

    # Generate random points and camera flythrough elements
    points = []
    if polygon is None:
        lat_center, lon_center = region_center
        for _ in range(points_count):
            rand_lat = lat_center + random.uniform(-radius, radius) / 111  # ~111 km per degree of latitude
            rand_lon = lon_center + random.uniform(-radius, radius) / (111 * abs(math.cos(math.radians(lat_center))))
            points.append((rand_lat, rand_lon))
    else:
        # Generate random points within the polygon
        minx, miny, maxx, maxy = polygon.bounds
        while len(points) < points_count:
            random_point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if polygon.contains(random_point):
                points.append((random_point.y, random_point.x))

    # Generate KML FlyTo elements for each point
    flytos = []
    for i in range(len(points)):
        lat, lon = points[i]
        if i == 0:
            duration = 5  # Initial duration can be arbitrary
        else:
            prev_lat, prev_lon = points[i - 1]
            distance = haversine(prev_lat, prev_lon, lat, lon)  # Distance in km
            duration = distance / speed * 3600  # Duration in seconds (distance / speed)

        flytos.append(f"""
            <gx:FlyTo>
                <gx:duration>{duration}</gx:duration>
                <gx:flyToMode>smooth</gx:flyToMode>
                <LookAt>
                    <longitude>{lon}</longitude>
                    <latitude>{lat}</latitude>
                    <altitude>{altitude}</altitude>
                    <heading>0</heading>
                    <tilt>45</tilt>
                    <range>2000</range>
                    <altitudeMode>relativeToGround</altitudeMode>
                </LookAt>
            </gx:FlyTo>
        """)

    # Combine header, points, and footer
    kml_content = kml_header + "\n".join(flytos) + kml_footer
    return kml_content

# Function to parse a polygon from a KML file
def parse_polygon_from_kml(kml_file_path):
    if not os.path.exists(kml_file_path):
        print(f"Error: File '{kml_file_path}' not found.")
        return None

    tree = ET.parse(kml_file_path)
    root = tree.getroot()
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    for placemark in root.findall(".//kml:Placemark", namespace):
        polygon_element = placemark.find(".//kml:Polygon", namespace)
        if polygon_element is not None:
            coordinates_text = polygon_element.find(".//kml:coordinates", namespace).text.strip()
            coordinates = [tuple(map(float, coord.split(",")[:2])) for coord in coordinates_text.split()]
            return Polygon(coordinates)
    print("Error: No polygon found in the KML file.")
    return None

# Parameters for the KML
def main():
    if len(sys.argv) < 2:
        print("""
Usage Instructions:

This script generates a Google Earth KML file with random flythroughs.

Options:
1. Radius-based exploration:
   $ python3 randomized_flyover_generator.py radius <latitude> <longitude> <radius_in_km> <points_count> <altitude_in_meters> <speed_in_kmh>
   - <altitude_in_meters>: Altitude in meters above ground level.
   - <speed_in_kmh>: Speed in kilometers per hour for the camera flyover.
   Example:
   $ python3 randomized_flyover_generator.py radius 37.7749 -122.4194 10 10 1500 100

2. Polygon-based exploration:
   $ python3 randomized_flyover_generator.py polygon <path_to_kml> <points_count> <altitude_in_meters> <speed_in_kmh>
   - <altitude_in_meters>: Altitude in meters above ground level.
   - <speed_in_kmh>: Speed in kilometers per hour for the camera flyover.
   Example:
   $ python3 randomized_flyover_generator.py polygon path/to/your/polygon.kml 10 1500 100
        """)
        return

    option = sys.argv[1].lower()
    if option == 'radius' and len(sys.argv) == 8:
        try:
            lat = float(sys.argv[2])
            lon = float(sys.argv[3])
            radius = float(sys.argv[4])
            points_count = int(sys.argv[5])
            altitude = float(sys.argv[6])
            speed = float(sys.argv[7])
            region_center = (lat, lon)
            # Generate KML for radius-based exploration
            random_kml_content = generate_random_kml(region_center, radius, points_count, altitude, speed)
            file_path = f"Flythrough_{lat}_{lon}_radius_{radius}_flyover.kml"
            with open(file_path, "w") as kml_file:
                kml_file.write(random_kml_content)
            print(f"Radius-based flythrough KML saved to {file_path}")
        except ValueError:
            print("Error: Invalid numerical input. Please provide valid latitude, longitude, radius, points count, altitude, and speed.")

    elif option == 'polygon' and len(sys.argv) == 6:
        polygon_kml_path = sys.argv[2]
        try:
            points_count = int(sys.argv[3])
            altitude = float(sys.argv[4])
            speed = float(sys.argv[5])
            polygon = parse_polygon_from_kml(polygon_kml_path)
            if polygon is not None:
                random_kml_content_polygon = generate_random_kml(None, None, points_count, altitude, speed, polygon=polygon)
                file_path_polygon = f"flythrough_{os.path.splitext(os.path.basename(polygon_kml_path))[0]}.kml"
                with open(file_path_polygon, "w") as kml_file:
                    kml_file.write(random_kml_content_polygon)
                print(f"Polygon-based flythrough KML saved to {file_path_polygon}")
        except ValueError:
            print("Error: Invalid input. Please provide a valid points count, altitude, and speed.")
    elif len(sys.argv) == 7:
        try:
            # Allow user to omit the 'radius' keyword
            lat = float(sys.argv[1])
            lon = float(sys.argv[2])
            radius = float(sys.argv[3])
            points_count = int(sys.argv[4])
            altitude = float(sys.argv[5])
            speed = float(sys.argv[6])
            region_center = (lat, lon)
            # Generate KML for radius-based exploration
            random_kml_content = generate_random_kml(region_center, radius, points_count, altitude, speed)
            file_path = f"flythrough_{lat}_{lon}_radius_{radius}.kml"
            with open(file_path, "w") as kml_file:
                kml_file.write(random_kml_content)
            print(f"Radius-based flythrough KML saved to {file_path}")
        except ValueError:
            print("Error: Invalid numerical input. Please provide valid latitude, longitude, radius, points count, altitude, and speed.")
    else:
        print("Error: Invalid arguments provided.")
        print("Run the script without arguments for usage instructions.")

if __name__ == "__main__":
    main()
