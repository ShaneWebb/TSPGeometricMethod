# =================================================================================================
# C950 Performance Assessment
# Name: Shane Webb
# Student ID: 001302624

# Analytics file - contains the algorithm to plan routes and load trucks.
# =================================================================================================

from data import *
import copy
import math
# Handles route objects, which contain information on a planned route, and the methods to generate
# the solutions.
class Route:
    def __init__(self, distances, packages, trucks):
        self.distances = distances
        self.packages = packages
        self.trucks = trucks
        self.plan = []  # Used for holding segment objects, which describes the solution.
        self.dFlattened = {}  # Used for holding a 2D distance matrix representation.

    # Data object for holding solution components. The route must be broken up into one or more segments.
    # Validation of the solution is the responsibility of the caller.
    class Segment:
        def __init__(self):
            # The following parameters must be set by external algorithms.
            self.address_sequence = []  # List of address strings in sequential order. Hub is first and last.
            self.package_list = PackageTable()  # Must be a packageTable object.
            self.start_time = 0  # When the segment is to be executed.
            self.truck = None  # Which truck will be executing the plan.

            # After the parameters above are set, the calculate method must be called to retrieve the following
            # information
            self.meets_deadlines = True
            self.missed_deadlines = 0
            self.length = math.inf
            self.end_time = math.inf

    # Runs through the provided address sequence and computes whether or not all deadlines are met, the
    # segment length, and when the segment is over. If optimize is true, rotates the address sequence list to find
    # the shortest possible route that meets deadlines. If not all deadlines can be met, optimize
    # keeps meets_deadlines as false, and instead returns the route with the lowest number of missed deadlines.
    # If update_package_status is set to true, then the original package data will be updated.
    def calculate_segment(self, segment, optimize=False, update_package_status=False):

        # Check whether to operate on the original package list, or a copy for accounting purposes.
        if update_package_status:
            package_list = segment.package_list
        else:
            package_list = copy.deepcopy(segment.package_list)

        # Rotates the given address list by a number of items.
        def rotate_addresses(input_list, amount):
            list_len = len(input_list)

            # If the list only has one or less in between items, no rotation can be done.
            if list_len <= 3:
                return input_list

            # The start and end of the sector is preserved.
            start = [input_list[0]]
            end = [input_list[len(input_list) - 1]]

            # Remove the start and end items
            input_list.remove(start[0])
            input_list.remove(end[0])

            # Have to map input values to valid list indices.
            shift = amount % (list_len - 2)

            # Perform the rotation on all elements besides start and end.
            rotated_list = start + input_list[-shift:] + input_list[:-shift] + end
            return rotated_list

        # Recursively call calculate with optimize set to false, with a slightly changed parameter each time.
        # Otherwise directly calculate as is.
        if optimize:
            shortest_route = math.inf
            lowest_deadlines_missed = math.inf
            optimal_address_sequence = None
            address_sequence_length = len(segment.address_sequence)

            # Repeatedly rotate the address list and find a good sequence.
            rotations_remaining = address_sequence_length - 2
            while rotations_remaining > 0:

                # Calculate as is.
                self.calculate_segment(segment)
                # print("calculate segment, optimize Rotation, missed deadlines:",
                # segment.missed_deadlines, "Starting Time: ", segment.start_time)
                # print(segment.address_sequence)
                if segment.missed_deadlines <= lowest_deadlines_missed and segment.length < shortest_route:
                    optimal_address_sequence = segment.address_sequence
                    lowest_deadlines_missed = segment.missed_deadlines
                    shortest_route = segment.length

                # Rotate the address sequence for the next run.
                segment.address_sequence = rotate_addresses(segment.address_sequence, 1)
                rotations_remaining -= 1

            # If no rotation meets all deadlines, sacrifice efficiency for speed by moving addresses with earlier
            # deadlines up the queue.
            if lowest_deadlines_missed > 0:

                # Generate a unique list of deadlines in the segment, in order from short to large.
                deadlines = []
                for package in package_list.get_package(get_all=True):
                    deadlines.append(package.deadline)
                deadlines = list(dict.fromkeys(deadlines))
                deadlines.sort()

                # Search for addresses that have a package which matches the evaluated deadline, then
                # move those to front.
                new_optimal_address_sequence = []
                effective_address_deadline = []
                start_address = optimal_address_sequence[0]
                end_address = start_address
                optimal_address_sequence.remove(start_address)

                # First, build a list that includes each addresses effective deadline.
                for address in optimal_address_sequence:
                    effective_deadline = math.inf
                    for package in package_list.get_package(field=address):
                        if package.deadline < effective_deadline:
                            effective_deadline = package.deadline
                    effective_address_deadline.append([address, effective_deadline])

                # Now, build a new address sequence from the deadline list.
                for deadline in deadlines:
                    for address_deadline in effective_address_deadline:
                        if address_deadline[1] == deadline:
                            new_optimal_address_sequence.append(address_deadline[0])

                # Add back the start and end addresses.
                new_optimal_address_sequence.insert(0, start_address)
                new_optimal_address_sequence.append(end_address)
                optimal_address_sequence = new_optimal_address_sequence

            # Once the optimal address sequence has been found, update the segment and rerun calculate_segment to
            # set the variables accordingly.
            segment.address_sequence = optimal_address_sequence
            self.calculate_segment(segment, optimize=False)

            # print("calculate segment, Optimize, final missed deadlines: ", segment.missed_deadlines)
            return

        else:

            speed = float(segment.truck.speed)  # Get truck speed for time calculation.
            addresses = segment.address_sequence  # Shortened variable for the address list.
            curr_time = segment.start_time
            total_length = 0
            missed_deadlines = 0

            # Iterate through the address list.
            for i in range(len(addresses) - 1):  # Has to stop at the second-to-last item.

                # Get the distance between the addresses, and update the total route length and the time.
                trip_length = self.distances.dist(addresses[i], addresses[i + 1])
                total_length += trip_length
                curr_time += trip_length / speed

                # Update the packages to be delivered at that address.
                matching_packages = package_list.get_package(field=addresses[i + 1])
                if len(matching_packages) <= 0:
                    continue

                # Update each matching package accordingly.
                for matching_package in matching_packages:
                    matching_package.delivery_time = curr_time

                    # Check if the package deadline was met. If not, set the appropriate variables.
                    if matching_package.deadline < curr_time:
                        segment.meets_deadlines = False
                        missed_deadlines += 1

            # Once all addresses have been checked, update the segment's length and end time.
            segment.missed_deadlines = missed_deadlines
            segment.length = total_length
            segment.end_time = curr_time
            return

    # ==========================
    # Prioritization methods.
    # ==========================

    # The priority is simply the angle. Lower angles are prioritized higher.
    def address_priority_angle(self, input_list):
        angle = input_list[1]
        priority = angle
        return priority

    # Prioritize by deadline, then by angle.
    def address_priority_deadline_angle(self, input_list):
        # Find the shortest deadline.
        deadlines = [24]
        for item in self.packages.get_package(field=input_list[0]):
            deadlines.append(item.deadline)
        deadline = min(deadlines)
        angle = input_list[1]
        priority = deadline + angle / 10
        return priority

    # Prioritize similar to above, except move packages that may only be on a specific truck to the front.
    def address_priority_truck_deadline_angle(self, input_list):
        # Find the shortest deadline, and if there are any truck constraints.
        deadlines = [24]
        tied_trucks = False
        for item in self.packages.get_package(field=input_list[0]):
            deadlines.append(item.deadline)
            if item.tiedToTruck != 0:
                tied_trucks = True
        deadline = min(deadlines)
        angle = input_list[1]
        priority = deadline + angle / 10

        if tied_trucks:
            return priority / 10
        else:
            return priority

    # ==========================
    # Solution methods.
    # ==========================

    def iterative_solution(self):

        # Hard coding for now - can always procedurally generate initialization vectors.
        init_vector1 = [[self.trucks[1], 8], [self.trucks[0], 9 + 5 / 60]]
        init_vector2 = [[self.trucks[0], 8], [self.trucks[1], 9 + 5 / 60]]
        init_vector3 = [[self.trucks[1], 8], [self.trucks[0], 8]]
        init_vector4 = [[self.trucks[0], 9 + 5 / 60], [self.trucks[1], 9 + 5 / 60]]
        init_vector5 = [[self.trucks[0], 8], [self.trucks[1], 8]]
        init_vector6 = [[self.trucks[1], 9 + 5 / 60], [self.trucks[0], 9 + 5 / 60]]
        trial_init_vectors = [init_vector1, init_vector2, init_vector3, init_vector4, init_vector5, init_vector6]
        trial_sort_methods = [self.address_priority_angle,
                              self.address_priority_deadline_angle,
                              self.address_priority_truck_deadline_angle]

        # Generate a combination of all plans with the above vectors and prioritization methods.
        plans = []
        for initVector in trial_init_vectors:
            for method in trial_sort_methods:
                plans.append(self.trial_solution(initVector, method))

        # Optimize each segment.
        for plan in plans:
            for segment in plan:
                self.calculate_segment(segment, optimize=True)

        # Once each plan and their segments have been optimized, search for the route with the lowest number
        # of missed deadlines (hopefully 0), and then by lowest length.
        best_plan = []
        shortest_route = math.inf
        least_missed_deadlines = math.inf
        for plan in plans:

            # Compute the number of missed deadlines for each plan and the route length by extracting the information
            # from the associated segment, and summing them up.
            missed_deadlines = 0
            route_length = 0
            for segment in plan:
                missed_deadlines += segment.missed_deadlines
                route_length += segment.length

            # If the plan has less missed deadlines, and a shorter route, update everything.
            if missed_deadlines <= least_missed_deadlines and route_length < shortest_route:
                best_plan = plan
                least_missed_deadlines = missed_deadlines
                shortest_route = route_length
                # print("iterative solution least missed deadlines:",
                # least_missed_deadlines, "Route length:", shortest_route)

        # Finally, update the route object with the best found plan, and set the package delivery times.
        # print("Iterative Solution Shortest Route:", shortest_route, "Least missed deadlines:", least_missed_deadlines)
        self.plan = best_plan
        for segment in self.plan:
            self.calculate_segment(segment, update_package_status=True)

    # Given a set of initial variables, produce a trial solution. Returns a plan list with solution segments.
    # init_vector is a list of truck and starting time pairs
    # which indicates what truck to begin loading and when. address_priority is a function which accepts a list, and
    # provides a sorting key based off the flattened distance matrix and other constraints.
    def trial_solution(self, init_vector, address_priority):

        # ====================================================
        # Setup: Initialize Variables/Temporary Data structures
        # ====================================================

        # Make a local copy of the master package database. Packages themselves are still passed as references.
        # Note that copy() will not work due to the individual buckets being objects.
        local_package_db = PackageTable()
        for item in self.packages.get_package(get_all=True):
            local_package_db.insert(item)

        # Generate a list of address-angle pairs, for eventual use in the scanner, which determines which packages to
        # load onto the truck.
        prioritized_addresses = []
        for key, value in self.dFlattened.items():
            prioritized_addresses.append([key, value[3]])

        # Accept an input function which determines how to prioritize which packages to load.
        prioritized_addresses.sort(key=address_priority)

        # Continuously work on generating a solution until there are no more packages.
        plan = []
        while len(local_package_db.get_package(get_all=True)) > 0:

            # Initialize a new plan and segment object, which will be used to hold solution details.
            # The first available truck in the list is loaded.
            segment = self.Segment()
            segment.truck = init_vector[0][0]
            segment.start_time = init_vector[0][1]
            init_vector.pop(0)

            # ====================================================
            # Stage 1: Loop through addresses, and add packages.
            # ====================================================

            # Search the prioritized address list for packages to load.
            for item in prioritized_addresses:

                # Get all packages at the address
                address = item[0]
                matching_packages = local_package_db.get_package(field=address)
                meets_constraints = True
                tied_package_ids = []
                matching_package_ids = []
                group_package_ids = []

                # Do not consider addresses which no longer have a package
                if len(matching_packages) == 0:
                    # print(item, "No matching packages!")
                    continue

                # Find if the package can be loaded, and any tied packages.
                for package in matching_packages:

                    # Get the matching id. This will be used to load the truck later if all other constraints pass.
                    matching_package_ids.append(package.package_id)

                    # Check if all matching packages are allowed on the current truck.
                    if package.tiedToTruck != 0 and package.tiedToTruck != segment.truck.truckId:
                        meets_constraints = False
                        # print(item, "Package not allowed on truck!")
                        break

                    # Check that the package is in the hub at the current starting time.
                    if package.availability > segment.start_time:
                        # print(item, "Package not available!")
                        meets_constraints = False
                        break

                    # Find all tied package ids.
                    if len(package.tiedToPackage) != 0:
                        for tied_package_id in package.tiedToPackage:
                            tied_package_ids.append(tied_package_id)

                # The list may have duplicates (due to tied packages also being matched packages). Eliminate them.
                group_package_ids = list(dict.fromkeys(tied_package_ids + matching_package_ids))
                num_packages_in_group = len(group_package_ids)
                num_packages_already_on_truck = len(segment.package_list.get_package(get_all=True))

                # Check to see if the group fits on the truck. If the total packages in the group (tied packages and
                # packages to be delivered to one address) plus packages already on the truck exceed capacity,
                # the group may not be loaded.
                if num_packages_in_group + num_packages_already_on_truck > segment.truck.capacity:
                    # print(item, "Truck full!")
                    meets_constraints = False

                # If all matching packages do not obey constraints, skip the address.
                if not meets_constraints:
                    continue

                # The packages (and all tied packages) may now be added. Packages that are added must also be
                # removed from the local database.

                for id in group_package_ids:
                    loaded_package = local_package_db.get_package(package_id=id)
                    segment.package_list.insert(loaded_package)
                    local_package_db.remove(loaded_package)

            # print("Packages left:", len(local_package_db.get_package(all=True)), "Truck:", segment.truck.truck_id,
            #       "Start Time:", segment.start_time)
            # for item in local_package_db.get_package(all=True):
            #     print(item)

            # ====================================================
            # Stage 2: Make final checks on the truck inventory.
            # ====================================================

            # Find all visited addresses in the loading scheme above.
            visited_addresses = []
            for package in segment.package_list.get_package(get_all=True):
                if package.address in visited_addresses:
                    pass
                else:
                    visited_addresses.append(package.address)

            if len(visited_addresses) < 1 and segment.start_time < init_vector[0][1]:
                init_vector.insert(0, [segment.truck, segment.start_time + 5 / 60])
                continue
            elif len(visited_addresses) < 1 and segment.start_time >= init_vector[0][1]:
                init_vector.append([segment.truck, segment.start_time + 5 / 60])
                continue

            # print("Visited addresses:", visited_addresses)

            # ====================================================
            # Stage 3: Compute the route, add the segment to the
            # plan, and make the truck available again.
            # ====================================================

            # Compute the address sequence via the sector method. Extract the r
            address_routing = self.find_address_sequence(visited_addresses)
            route_length = address_routing[0]
            address_sequence = address_routing[1]

            # Update the plan address sequence, and then add the segment to the plan.
            segment.address_sequence = address_sequence
            plan.append(segment)

            # Compute how long the route will take, then update the initialization vector, with 5 minutes gap. This
            # puts the truck back into circulation at the time it returns to the hub.
            elapsed_time = route_length / segment.truck.speed
            init_vector.append([segment.truck, segment.start_time + elapsed_time + 30 / 60])

        return plan

    # Given a list of addresses to visit, use the flattened distance matrix to generate a sequence. The first and
    # last address will always be the hub. See documentation.

    # Note to self: the truck loader has to account for how the address sequencing works to ultimately find the
    # best solution. You may need to iteratively invoke this method.
    def find_address_sequence(self, address_list):

        # Create a new flattened distance matrix which only includes items in the address list being evaluated.
        truncated_distance_matrix = {}
        for item in address_list:
            truncated_distance_matrix[item] = self.dFlattened[item]

        # The following dict stores a parametrized length along the perimeter of the circular sector which encloses
        # the provided addresses.
        sector_position = []

        # Closest and furthest addresses to/from hub.
        min_radius_address = min(truncated_distance_matrix, key=lambda k: truncated_distance_matrix[k][2])
        max_radius_address = max(truncated_distance_matrix, key=lambda k: truncated_distance_matrix[k][2])
        min_radius = truncated_distance_matrix[min_radius_address][2]
        max_radius = truncated_distance_matrix[max_radius_address][2]

        # Lowest and greatest angles.
        min_angle_address = min(truncated_distance_matrix, key=lambda k: truncated_distance_matrix[k][3])
        max_angle_address = max(truncated_distance_matrix, key=lambda k: truncated_distance_matrix[k][3])
        min_angle = truncated_distance_matrix[min_angle_address][3] - 0.01
        max_angle = truncated_distance_matrix[max_angle_address][3] + 0.01

        # print(min_angle, max_angle)

        # Compute geometric parameters of the sector, for later computation.
        sector_sweep = max_angle - min_angle
        sector_depth = max_radius - min_radius
        sector1_len = (min_radius * sector_sweep) / 2
        sector5_len = sector1_len
        sector2_len = sector_depth
        sector4_len = sector2_len
        sector3_len = max_radius * sector_sweep
        sector_lens = [sector1_len, sector2_len, sector3_len, sector4_len, sector5_len]

        # Determine the parametrized sector position.
        for address in address_list:
            radius = truncated_distance_matrix[address][2]
            angle = truncated_distance_matrix[address][3]
            par_length = 0

            # Distance from each sector segment.
            sector1_dist = radius - min_radius
            sector5_dist = sector1_dist
            sector2_dist = (angle - min_angle) * radius
            sector4_dist = (max_angle - angle) * radius
            sector3_dist = max_radius - radius
            sector_dists = [sector1_dist, sector2_dist, sector3_dist, sector4_dist, sector5_dist]
            min_sector_dist = min(sector_dists)

            if sector_dists[0] == min_sector_dist:  # Point maps to either sector 1 or 5.
                if (angle - min_angle) / sector_sweep < 0.5:  # Sector 1
                    par_length = min_radius * (angle - min_angle)
                else:  # Sector 5
                    par_length = sum(sector_lens[0:4]) + min_radius * (max_angle - angle)
            elif sector_dists[1] == min_sector_dist:  # Sector 2.
                par_length = sector_lens[0] + radius
            elif sector_dists[2] == min_sector_dist:  # Sector 3.
                par_length = sum(sector_lens[0:2]) + max_radius * (angle - min_angle)
            elif sector_dists[3] == min_sector_dist:  # Sector 4
                par_length = sum(sector_lens[0:3]) + (max_radius - radius)

            sector_position.append([address, par_length])

        # Sort the list by parametrized positions.
        def get_par_dist(my_list):
            return my_list[1]

        sector_position.sort(key=get_par_dist)

        # Build the sequence of addresses from the parametrized distances.
        address_sequence = []
        for item in sector_position:
            address_sequence.append(item[0])

        # Add the hub address to the front and back.
        hub_address = self.distances.address_list[0]
        address_sequence.insert(0, hub_address)
        address_sequence.append(hub_address)

        route_len = 0
        for i in range(0, len(address_sequence) - 1):  # Must stop before the last element
            route_len += self.distances.dist(address_sequence[i], address_sequence[i + 1])

        # print(route_len, address_sequence)
        return [route_len, address_sequence]

    # Takes a distance matrix, and creates a 2D "flattened" representation with x-y coordinates that
    # approximates the otherwise multi-dimensional graph. This allows for geometric solutions to be applied
    # more readily, and for easy visualization. See documentation.

    # Note to self: this naive method worked surprisingly well. Didn't need to use multi-dimensional Newton-Rahpson.
    def flatten(self):

        prev_address = self.distances.address_list[
            0]  # Storing the previous item reference, needed for the calculation process.
        for currAddress in self.distances.address_list:
            self.dFlattened[currAddress] = [0,  # Initial x-coordinate
                                            0,  # Initial y-coordinate
                                            self.distances.dist(currAddress, self.distances.address_list[0]),
                                            # Radius (distance from hub)
                                            0]  # Initial bearing (from hub)

            # For convenience, get the direct reference to the coordinate list for the previous and current address.
            prev_coordinates = self.dFlattened[prev_address]
            curr_coordinates = self.dFlattened[currAddress]

            # Acquire the needed function parameters to find the valid angles for item.
            d = self.distances.dist(prev_address, currAddress)
            r_prev = prev_coordinates[2]
            r_curr = curr_coordinates[2]
            a_prev = prev_coordinates[3]

            # Compute the two possible angles for the current item.
            a_curr = self.find_angle(r_prev, r_curr, d, a_prev)

            # To find the valid angle, check which one results in the least amount of error with the other points.
            # Error is weighted quadratically, to penalize outliers. See documentation.
            error1 = 0
            error2 = 0
            for address, val in self.dFlattened.items():
                # Do not compare against self.
                if address == currAddress:
                    break
                # Radius and angle for the current item being evaluated.
                r_val = val[2]
                a_val = val[3]

                # Flattened distance represents the distance between the two points on the 2D model, which will not
                # necessarily be equal to the true distance as reported on the table. This error must be found and
                # computed.
                flattened_dist1 = self.polar_dist(r_val, r_curr, a_val, a_curr[0])
                flattened_dist2 = self.polar_dist(r_val, r_curr, a_val, a_curr[1])
                true_dist = self.distances.dist(address, currAddress)
                error1 += (true_dist - flattened_dist1) ** 2
                error2 += (true_dist - flattened_dist2) ** 2

            # Pick the angle that leads to a more accurate model.
            if error1 < error2:
                self.dFlattened[currAddress][3] = a_curr[0]
            else:
                self.dFlattened[currAddress][3] = a_curr[1]

            # Set x and y coordinates respectively
            self.dFlattened[currAddress][0] = r_curr * math.cos(self.dFlattened[currAddress][3])
            self.dFlattened[currAddress][1] = r_curr * math.sin(self.dFlattened[currAddress][3])

            # Set previous item to current for the next loop iteration.
            prev_address = currAddress

    # A basic wrapper around polar_dist, which accepts two addresses as an argument.
    def flattened_dist(self, address1, address2):
        coordinates1 = self.dFlattened[address1]
        coordinates2 = self.dFlattened[address2]
        r1 = coordinates1[2]
        r2 = coordinates2[2]
        a1 = coordinates1[3]
        a2 = coordinates2[3]
        return self.polar_dist(r1, r2, a1, a2)

    # Standard cartesian distance formula.
    def cartesian_dist(self, x1, x2, y1, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # Polar distance formula.
    def polar_dist(self, r1, r2, a1, a2):
        return math.sqrt(r1 ** 2 + r2 ** 2 - 2 * r1 * r2 * math.cos(a1 - a2))

    # With known distances from the hub, one known polar angle, and known distance from each other, find the
    # two valid polar angles of the second radius. See documentation.
    def find_angle(self, r1, r2, d, a1):
        if r1 == 0 or r2 == 0:
            return [0, 0]

        # Law of cosines to compute angle between two locations. Absolute angle has two candidates - one in the
        # clockwise direction, the other counter-clockwise.
        angle_between = math.acos((d ** 2 - (r1 ** 2 + r2 ** 2)) / (-2 * r1 * r2))
        val1 = a1 + angle_between
        val2 = a1 - angle_between

        # Strictly want angles between 0 and 360 only, for ease of readability and also to avoid errors in
        # calculations which often assume positive angles.
        return [val1 % (2 * math.pi), val2 % (2 * math.pi)]


# Evaluates route solutions, and produces the desired output.
class Report:
    def __init__(self, route):
        self.route = route

    # Sets all relevant delivery statuses at a given moment.
    def simulate(self, time):

        for segment in self.route.plan:

            # Update the delivery statuses of each package.
            for package in segment.package_list.get_package(get_all=True):
                if segment.start_time >= time:  # Status remains "Not delivered" if the time is before segment start.
                    continue
                else:
                    package.status = "In transit"
                if time >= package.delivery_time:
                    package.status = "Delivered"

    # Resets all statuses, to clean up after simulate.
    def reset(self):
        # Sets all package statuses in the route to 0, or undelivered.
        for item in self.route.packages.get_package(get_all=True):
            item.status = "Not delivered"
        # Clears all package lists from the trucks and resets the miles.
        for item in self.route.trucks:
            item.packages = None
            item.miles = 0

    # Print the routing solution.
    def print_solution(self):
        for segment in self.route.plan:
            # Print the truck associated with the segment, and when it leaves the hub.
            print("\nTruck:", segment.truck.truckId, "Start time:", segment.start_time,
                  "\n", "Segment Length:", segment.length, "Missed deadlines:", segment.missed_deadlines)

            # Generate and print a succint list of ID's indicating which packages are on the truck.
            id_list = []
            for package in segment.package_list.get_package(get_all=True):
                id_list.append(package.package_id)
            print("Packages Loaded:", id_list, "\n")

            # Print out the order of addresses to be visited, top down.
            for address in segment.address_sequence:
                print(address)

    def out(self):

        route_length = 0;
        for segment in self.route.plan:
            route_length += segment.length

        print("\nRoute Length:", route_length)

        def get_id(package):
            return package.package_id

        sorted_by_id = self.route.packages.get_package(get_all=True)
        sorted_by_id.sort(key=get_id)

        for item in sorted_by_id:
            print(item)
