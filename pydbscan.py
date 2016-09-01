'''
MIT License

Copyright (c) 2013, Ian F. Adams, University of California, Santa Cruz
Copyright (c) 2016,Ian F. Adams

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
#TODO, logging infrastructure
# TODO rejigger to handle arbitrary dimensionality.
# TODO, setup.py file

import numpy as np
import math

#Types of data points
UNCATEGORIZED = 0
CORE = 1
BORDER = 2
NOISE = 3

#Types of point colors
WHITE = 10
GREY = 11
BLACK = 12

def calc_distance(point_a, point_b):
    """
    calculates euclidean distance between two arbitrary points of n dimensions
    Yes, I know others do it well, but this is my stupid learning project, dammit.

    :param point_a: tuple describing point in space
    :param point_b: tuple describing point in space

    :raises Exception: if you try to calculate the distance between tuples
    of different dimension
    """

    if len(point_a) != len(point_b):
        raise Exception("Cannot calculate distance between points of"
                        "differing dimensionality")


    running_sum = 0
    for index in range(len(point_a)):
        running_sum += (point_a[index] - point_b[index]) ** 2
    dist = math.sqrt(running_sum)

    return dist

#TODO add check for non-tuple inputs
class DataPoint:
    """
    Heavy weight datapoint class. Meant to be clear and easy-ish to use,
    not efficient :p.
    """
    def __init__(self, location, id=None):
        """
        :param location: tuple describing the location on a plane, can be arbitrary dimensions
        """

        self.loc = location
        self.id = id

        #What type of datapoint is it, based on DBSCAN categorizations
        self.category = UNCATEGORIZED

        # contains tuples, first element is the distance, second is the datapoint
        # related to that distance
        self.distance_list = []

        #used to store core and border points within eps distance of the datapoint
        self.adjacency_list = []

        #number of other points INCLUDING SELF in the eps (neighborhood)
        self.number_in_neighborhood = 0

        #cluster identifier, if -1 it is unassigned
        self.cluster_identifer = -1

        #stores the python set/cluster it is a member of
        self.member_of_set = 0

        #vertex color, used when we do a DFS to identify the connected
        #components (clusters
        self.color = WHITE

        #used in graph searches, -1 one denotes a NIL or NULL value
        self.parent = -1
        self.time = 0

# TODO, make generic dp cluster class, subclass for additional clusterings like k-means
class DataPointCluster:
    """
    Stores our datapoints in a handy dandy central location with
    extra functionality
    """

    def __init__(self):
        self.data_list = []
        self.dimensionality = None
        self.distance_matrix = None
        self.id_counter = 0
        self.clusters = None

    def add_datapoint(self, datapoint):
        """
        :param datapoint: object of DataPoint class
        """


        # make sure all the data points are of the same dimensionality
        if self.dimensionality is None:
            self.dimensionality = len(datapoint.loc)
        elif self.dimensionality != len(datapoint.loc):
            raise Exception("Inconsistent dimension! Added data point of "
                            "dimension %s, but data list is of dimension %s  "
                            % (len(datapoint.loc), self.dimensionality))


        # Assign a unique ID to the data point, or the counter value
        # TODO change to uuid so it will never conflict with manuall IDs
        if datapoint.id is None:
            datapoint.id = self.id_counter
        self.id_counter += 1

        self.data_list.append(datapoint)

    def create_distance_matrix(self):
        """
        Creates a distance matrix using the current list of data points, if a distance matrix
        is already in existence, an error will be raised.

        :raises: Exception, distance matrix already created
        """


        # if we already created the matrix, oops, raise an error
        if self.distance_matrix is not None:
            raise Exception("Distance Matrix Already Created!")

        # calculate size of, and create, empty distance matrix
        num_dp = len(self.data_list)

        self.distance_matrix = np.zeros((num_dp, num_dp))

        # inefficient, n2, redundant work, but should be functional
        for compare_from in self.data_list:
            for compare_to in self.data_list:
                point_a = compare_from.loc
                point_b = compare_to.loc

                dist = calc_distance(point_a, point_b)
                self.distance_matrix[compare_from.id][compare_to.id] = dist

        print self.distance_matrix

    def clear_distance_matrix(self):
        """
        Clear any distance matrix thats already been calculated
        """

        self.distance_matrix = None



    def clear_datapoints(self):
        """
        Remove any data points in existence, does not clear existing distance matrix
        """

        self.data_list = []

    def db_scan(self, eps, nhood_size):
        """
        Run the DB Scan clustering algorithm
        """

        print "Calculating Core Points..."
        for dp in self.data_list:
            count_within_eps = 0

            # grab the ID of one dimension, which we then traverse and
            # grab the distance to everybody else relative to that point
            compare_from_id = dp.id

            for compare_to_id in range(self.id_counter):

                if compare_to_id == compare_from_id:
                    continue

                distance = self.distance_matrix[compare_from_id][compare_to_id]
                print "----"
                print compare_from_id
                print compare_to_id
                print distance

                if distance <= eps:
                    count_within_eps += 1

                if count_within_eps >= nhood_size:
                    print "CORE POINT"
                    dp.category = CORE
                    break


        #Next, identify all the border points-that is, points that are not core, but
        #are within eps of at least one core point
        print "Calculating Border Points..."
        for dp in self.data_list:

            #if its already been categorized as a core or border point, skip to the next datapoint
            if dp.category == CORE or dp.category == BORDER:
                continue

            # grab the ID of one dimension, which we then traverse and
            # grab the distance to everybody else relative to that point
            compare_from_id = dp.id

            for compare_to_id in range(self.id_counter):
                distance = self.distance_matrix[compare_from_id][compare_to_id]

                #if its within eps of another core point break out as we can categorize it
                if (distance <= eps) and (self.data_list[compare_to_id].category == CORE):
                    dp.category = BORDER
                    break

        print "Calculating Noise Points..."
        #finally label all the noise points (any point not already flagged as core or border)
        for dp in self.data_list:
            if dp.category == UNCATEGORIZED:
                dp.category = NOISE

        # Okay, now everyone is labeled, but because Im doing the lazy, innefficient approach, now
        # we run a graph algorithm to actually glom these together into identifable clusters
        for dp in self.data_list:
            if dp.category == CORE:
                # grab the ID of one dimension, which we then traverse and
                # grab the distance to everybody else relative to that point
                compare_from_id = dp.id

                for compare_to_id in range(self.id_counter):
                    distance = self.distance_matrix[compare_from_id][compare_to_id]


                    #don't create an edge to yourself
                    if distance == 0:
                        continue

                    #if its within eps of another core point, create an edge to that point
                    #don't worry about reciprocating it as it will be done
                    #on another iteration of the loop
                    adj_point = self.data_list[compare_to_id]
                    if (distance <= eps) and (adj_point.category == CORE):
                        dp.adjacency_list.append(adj_point)
            else:
                continue

        print "Identifying connected componenets (labeling clusters)"
        #basically, this is identifying the clusters
        set_list = identify_connected_components(self.data_list)
        print set_list

        #finally, add the border points to clusters
        #The border points arbitrarily attach to the first core cluster within EPS
        print "Connecting Border Points..."
        for dp in self.data_list:
            if dp.category == BORDER:
                add_border(dp, set_list, eps)

        self.clusters = set_list

    def print_clusters(self):
        """
        Prints out the clusters, assumes they're stored in self.clusters
        """

        #TODO, specialized exceptions
        if None:
            raise Exception("Clusters is empty!")

        # TODO pretty print
        # TODO label clusters
        counter = 0
        for cluster in self.clusters:
            print "Cluster: %d" % counter
            for dp in cluster:
                print dp.id
            counter += 1


#returns a list of sets that represent the connected components (clusters)
#Uses depth first search, ONLY RUNS ON CORE POINTS	
def identify_connected_components(dp_list):


    first_set=True
    set_list = []

    for datapoint in dp_list:

        #skip it if its not a core point
        if datapoint.category != CORE:
            continue

        #if its a datapoint thats already been visited, skip it
        #otherwise its a new root/set/connected component
        if datapoint.color != WHITE:
            continue
        else:
            current_set = set()
            current_set.add(datapoint)
            set_list.append(current_set)
            datapoint.color = GREY

        stack = []
        #initialize the stack
        for adj_point in datapoint.adjacency_list:

            #skip if it  links to itself
            if adj_point==datapoint:
                continue

            #otherwise add ALL of the adjacent points onto the stack
            stack.append(adj_point)

        #now go through the stack
        while len(stack) != 0:
            point = stack.pop()

            if point.color == WHITE:
                current_set.add(point)
                point.color = GREY

            for adj_point in point.adjacency_list:
                if adj_point.color == WHITE:
                    adj_point.color = GREY
                    stack.append(adj_point)
                    current_set.add(adj_point)

    return set_list


#adds the border point to the first set (cluster)
#if shares a core point within EPS of
def add_border(border_point, set_list, eps):

        for cur_set in set_list:
            for element in cur_set:
                if element.category == CORE and (math.fabs(element.loc-border_point.loc) <= eps):
                    cur_set.add(border_point)
                    return



if __name__ == "__main__":

    # TODO, move to unit set framework
    dp_1 = DataPoint((1,))
    dp_2 = DataPoint((2,))
    dp_3 = DataPoint((3,))
    dp_4 = DataPoint((8,))
    dp_5 = DataPoint((9,))
    dp_6 = DataPoint((10,))
    dp_7 = DataPoint((99,))

    test1d = DataPointCluster()
    test1d.add_datapoint(dp_1)
    test1d.add_datapoint(dp_2)
    test1d.add_datapoint(dp_3)
    test1d.add_datapoint(dp_4)
    test1d.add_datapoint(dp_5)
    test1d.add_datapoint(dp_6)
    test1d.add_datapoint(dp_7)
    test1d.create_distance_matrix()
    test1d.db_scan(3,2)
    test1d.print_clusters()