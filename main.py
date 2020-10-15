# =================================================================================================
# Main file - program runs holistically from here.
# =================================================================================================

# from data import *
from analytics import *

# ==========================================
# Import project data, then generate route.
# ==========================================

# Create distances and packages objects, which read provided data from CSV files.

# Instantiate, then populate, then prune (optimize) the distances table.
distances = DistanceTable()
distances.populate("distances.csv")
distances.prune()

# Instantiate, then populate the package list.
packages = PackageTable()
packages.populate("packages.csv")
truck1 = Truck(1)
truck2 = Truck(2)
trucks = [truck1, truck2]

# Make some manual corrections to the data. Could do this in the CSV file, but serves as a good demo.
packages.get_package(package_id=3).tiedToTruck = 2
packages.get_package(package_id=18).tiedToTruck = 2
packages.get_package(package_id=36).tiedToTruck = 2
packages.get_package(package_id=38).tiedToTruck = 2
packages.get_package(package_id=13).tiedToTruck = 2  # Indirectly tied to truck 2.
packages.get_package(package_id=14).tiedToTruck = 2  # Indirectly tied to truck 2.
packages.get_package(package_id=15).tiedToTruck = 2  # Indirectly tied to truck 2.
packages.get_package(package_id=16).tiedToTruck = 2  # Indirectly tied to truck 2.
packages.get_package(package_id=19).tiedToTruck = 2  # Indirectly tied to truck 2.
packages.get_package(package_id=6).availability = 9 + 5 / 60
packages.get_package(package_id=25).availability = 9 + 5 / 60
packages.get_package(package_id=28).availability = 9 + 5 / 60
packages.get_package(package_id=32).availability = 9 + 5 / 60
packages.get_package(package_id=9).street = "410 S State St"
packages.get_package(package_id=9).zip_code = 84111
packages.get_package(package_id=9).address = "410 S State St (84111)"
packages.get_package(package_id=9).availability = 10 + 20 / 60  # Time when address is to be fixed.
packages.get_package(package_id=13).tiedToPackage = [13, 14, 15, 16, 18, 19]
packages.get_package(package_id=14).tiedToPackage = [13, 14, 15, 16, 18, 19]
packages.get_package(package_id=15).tiedToPackage = [13, 14, 15, 16, 18, 19]
packages.get_package(package_id=16).tiedToPackage = [13, 14, 15, 16, 18, 19]
packages.get_package(package_id=19).tiedToPackage = [13, 14, 15, 16, 18, 19]

# Create a route object after providing the distance matrix, packages, and trucks. Then flatten the matrix, and
# generate a loading/routing solution.
route = Route(distances, packages, trucks)
route.flatten()
route.iterative_solution()

# Report generation.
report = Report(route)

# ==========================================
# Interactive console
# ==========================================

active = True
while active:
    print("Press X to exit | R for report | ")
    if input() == "X":
        active = False
        break
    elif input() == "R":
        print("Enter the hour for the lookup time (24 hour format): ")
        status_time_hour = float(input())
        print("Enter the minute for the lookup time (1-60): ")
        status_time_minute = float(input())
        report.simulate(status_time_hour + status_time_minute/60)
        report.print_solution()
        report.out()
        report.reset()
        continue
    else:
        continue

# =================================================================================================
