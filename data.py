# =================================================================================================
# C950 Performance Assessment
# Name: Shane Webb
# Student ID: 001302624

# Data File - contains classes and functions needed to parse, abstract, and store the data.
# =================================================================================================

# Variables for later.
import copy
import math


def read_csv(filename):
    my_file = open(filename)
    temp_list = my_file.readlines()
    parsed_list = []
    for line in temp_list:
        parsed_list.append(line.split(','))
    my_file.close()
    return parsed_list


# Used for representing packages.
class Package:
    def __init__(self, package_id, street, city, state, zip_code, deadline, weight, special_note):
        self.package_id = int(package_id)
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.address = str(street) + " (" + str(zip_code) + ")"  # address usable w/ the distance matrix
        self.weight = int(weight)
        self.specialNote = special_note

        # The following parameters indicate constraints and other package information.
        self.availability = 0  # time is indicated in decimals, from 0 to 23.99
        self.deadline = float(deadline)
        self.tiedToPackage = []
        self.tiedToTruck = 0  # 0 To indicate "None".
        self.status = "Not delivered"  # Not delivered, In transit, and Delivered are used.
        self.delivery_time = math.inf

    def __str__(self):
        if self.status == "Delivered":
            proper_delivery_time = self.delivery_time
        else:
            proper_delivery_time = "N/A"
        return ("ID: " + str(self.package_id) + " Street: " + str(self.street) +
                " City: " + str(self.city) + " State: " + str(self.state) + " Zipcode: " +
                str(self.zip_code) + " Deadline: " + str(self.deadline) + " Weight: " + str(self.weight) +
                " Status: " + str(self.status) + " Delivery Time: " + str(proper_delivery_time))


class Truck:
    def __init__(self, truck_id):
        self.truckId = truck_id
        self.packages = None
        self.capacity = 16
        self.speed = 18
        self.miles = 0

# Class which initializes and holds the distance data, and allows for lookup of a distance by providing
# any two addresses.
class DistanceTable:
    def __init__(self):
        self.address_list = []
        self.distanceMatrix = {}
        self.prunedDistanceMatrix = {}
        self.path = {}

    def populate(self, input_str):
        distance_import = read_csv(input_str)

        # Generate the list of addresses. Order is significant, to determine index to generate keys.
        for item in distance_import:
            self.address_list.append(item[0])

        # Populate the distance matrix.
        for item1 in self.address_list:
            for item2 in self.address_list:
                # The dictionary key is the two concatenated addresses, with the lexicographically greater string
                # first. Additionally, the matrix will store a list of addresses indicating the actual fastest route.
                # This list begins with the greater address, and until pruning is done, is just the start and end given.
                if item1 > item2:
                    combined_key = item1 + item2
                    self.distanceMatrix[combined_key] = [None, [item1, item2]]
                else:
                    combined_key = item2 + item1
                    self.distanceMatrix[combined_key] = [None, [item2, item1]]

                # The matrix in the CSV file is populated at the bottom only. So the larger index must go first.
                # The second index is incremented by one to skip the address string.
                ind1 = self.address_list.index(item1)
                ind2 = self.address_list.index(item2)
                if ind1 > ind2:
                    self.distanceMatrix[combined_key][0] = float(distance_import[ind1][ind2 + 1])
                else:
                    self.distanceMatrix[combined_key][0] = float(distance_import[ind2][ind1 + 1])

        # Copy into the pruned list - all functions will reference this list even if prune is not run.
        self.prunedDistanceMatrix = copy.deepcopy(self.distanceMatrix)

    # Returns the distance between the two points
    def dist(self, address1, address2, search_pruned=True):
        if address1 > address2:
            combined_key = address1 + address2
        else:
            combined_key = address2 + address1
        if search_pruned:
            return float(self.prunedDistanceMatrix[combined_key][0])
        else:
            return float(self.distanceMatrix[combined_key][0])

    def path(self, address1, address2):
        if address1 > address2:
            combined_key = address1 + address2
        else:
            combined_key = address2 + address1
        return self.prunedDistanceMatrix[combined_key][1]

    # The direct route is not always the fastest way between two addresses. Prune eliminates such routes and generates
    # the shortest path between two points for all points.
    def prune(self):
        # Each address pair will be checked.
        for item in self.prunedDistanceMatrix.values():
            path_len = item[0]  # Set shortest known path to the direct path initially.
            route = item[1]  # The route in the item - for now just the start and end.

            # List of routes to evaluate. Will initialize with a path length of zero, and the starting point.
            candidate_routes = [[0, item[1][0]]]
            incomplete_routes = True

            # Will evaluate a list of routes. Any that have distances larger than the known best will be eliminated.
            # Routes that have a running length less than the known best will stay in consideration until the next
            # hop can be evaluated.
            while incomplete_routes:
                complete_routes = 0  # Loop control variable.
                temp_list = copy.copy(candidate_routes)  # Need a copy as the original list is being modified.

                for trialRoute in temp_list:
                    # Search for complete routes, e.g. routes that terminate at the desired address. Then perform
                    # needed operations.
                    if trialRoute[len(trialRoute) - 1] == route[len(route) - 1]:

                        # Loop control. If the list only contains completed routes - which happens when all other
                        # options have been exhausted, pruning is finished for the one item.
                        complete_routes += 1
                        if complete_routes >= len(temp_list):
                            incomplete_routes = False

                        # Remove complete routes which are worse than the known best route.
                        if trialRoute[0] > path_len + .001:
                            candidate_routes.remove(trialRoute)
                        elif trialRoute[0] < path_len + .001:
                            path_len = trialRoute[0]  # Update path_len with the new best route.

                        # A complete route must not have any trial addresses appended to the end, so skip the logic
                        # below, which creates new trial routes from incomplete routes.
                        continue

                    # Create a list of addresses which have not yet been visited in the trial route.
                    new_addresses = copy.copy(self.address_list)
                    temp_trial_route_list = copy.copy(trialRoute)
                    temp_trial_route_list.pop(0)
                    for visitedAddress in temp_trial_route_list:
                        new_addresses.remove(visitedAddress)

                    # The next destination to test may be any not visited already.
                    for address in new_addresses:

                        # Create a new route object to add to potentially add to the list of candidates.
                        new_route = copy.copy(trialRoute)

                        # Compute length of the next hop, and add that hop to the route
                        trial_segment = float(self.dist(trialRoute[len(trialRoute) - 1], address, search_pruned=False))
                        new_route[0] += trial_segment
                        new_route.append(address)

                        if new_route[0] < path_len + .001:
                            candidate_routes.append(new_route)

                    # The original, incomplete route is removed.
                    candidate_routes.remove(trialRoute)

            # It may be possible that multiple alternate routes of the exact same, optimal length are provided.
            # In this case, update only the first one.
            # print(candidate_routes)
            item[0] = round(candidate_routes[0][0], 1)
            candidate_routes[0].pop(0)
            item[1] = candidate_routes[0]


# Section 1 item E: Hashtable for package items. Uses lists for individual buckets to handle collisions.
class PackageTable:
    def __init__(self):
        # Initialize hashtable, which will be handled via nested lists.
        self.bucketSize = 10
        self.hashTable = []
        for var in range(self.bucketSize):
            self.hashTable.append([])

    # Accepts a file name, and populates the hash table.
    def populate(self, input_str):
        for line in read_csv(input_str):
            my_package = Package(line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7])
            self.insert(my_package)

    # Inserts a package into the hash table.
    def insert(self, package):
        index = package.package_id % self.bucketSize
        self.hashTable[index].append(package)

    # Remove a package from the table.
    def remove(self, package):
        bucket_list = self.hashTable[package.package_id % self.bucketSize]
        for item in bucket_list:
            if item.package_id == package.package_id:
                bucket_list.pop(bucket_list.index(item))

    # Find a package from a given field, or Id. A field may return multiple matches, an Id will return only one.
    # Search by ID utilizes fast lookup of the hashtable.
    def get_package(self, get_all=False, field=None, package_id=0):
        if package_id != 0:
            bucket_list = self.hashTable[package_id % self.bucketSize]
            for item in bucket_list:
                if item.package_id == package_id:
                    return item
        elif get_all:
            package_list = []
            for bucket_list in self.hashTable:
                for item in bucket_list:
                    package_list.append(item)
            return package_list
        else:
            package_list = []
            for bucket_list in self.hashTable:
                for item in bucket_list:
                    for par in vars(item):
                        if field != "" and field == vars(item)[par]:  # Search every field of every package for a match
                            package_list.append(item)
            return package_list
