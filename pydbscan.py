'''
MIT License

Copyright (c) 2013 University of California, Santa Cruz
Copyright (c) Ian F. Adams

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

class D1_data_point:
    def __init__(self, location):

        self.loc = location

        #What type of datapoint is it, based on DBSCAN categorizations
        self.category = UNCATEGORIZED

        #contains tuples, first is the distance, second is the datapoint related
        #to that distance
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

#Expects an (potentially unordered) list of integers and or floats
#epsilon (search radius for any given point)
#and the min neighborhood size
#returns dictionary of clusters, indexed by tuples denoting the start
#and end value of the cluster
def dim_1_dbscan(data_list, eps, nhood_size):

    #stores the datapoints
    dp_list = []

    #put each point in the list into a 1D data point, and save that point in a list
    for entry in data_list:
        new_dp = D1_data_point(entry)
        dp_list.append(new_dp)

    #now create a list of distances from ALL points for each data point. Inefficient, but
    #this is meant to be simple and visible, not fast
    print "Creating Distance Matrices..."

    for cur_dp in dp_list:
        for compare_to_dp in dp_list:

            #pull out the positions of each
            position_1 = cur_dp.loc
            position_2 = compare_to_dp.loc

            #difference/distance between them
            dist=math.fabs(position_2-position_1)
            distance_tuple=(dist,compare_to_dp)
            cur_dp.distance_list.append(distance_tuple)

        #now sort the distance list. This will provide some speedup when we are checking
        # distances for categorizing the points
        cur_dp.distance_list.sort()


    #DEBUG
    '''for dp in dp_list:
        print "---INIT DP---:",dp.loc
        for dist_tuple in dp.distance_list:
            distance=dist_tuple[0]
            compared_to_dp=dist_tuple[1]

            print "Initial Point Location:",dp.loc
            print "Compared to Point Location:",compared_to_dp.loc
            print "Distance between calced:",distance
            print "Distance between re-calced:",math.fabs(compared_to_dp.loc-dp.loc)
            print ""

        print "---"
    exit()'''


    #Now, label all core points, that is, any point with at least nhood_size
    #points within eps distance
    print "Calculating Core Points..."
    for dp in dp_list:
        count_within_eps = 0
        for distance_tuple in dp.distance_list:
            distance = distance_tuple[0]
            if distance <= eps:
                count_within_eps += 1


            if count_within_eps >= nhood_size:
                dp.category = CORE
                break

    #Next, identify all the border points-that is, points that are not core, but
    #are within eps of at least one core point
    print "Calculating Border Points..."
    for dp in dp_list:

        #if its already been categorized as a core point, skip to the next datapoint
        if dp.category == CORE:
            continue

        #if its not a core point, its uncategorized at this point, so examine
        #the distances from other points
        for distance_tuple in dp.distance_list:
            dist = distance_tuple[0]
            adj_point = distance_tuple[1]

            #if its within eps of another core point break out as we can categorize it
            if (dist <= eps) and (adj_point.category == CORE):
                dp.category = BORDER
                break



    print "Calculating Noise Points..."
    #finally label all the noise points (any point not already flagged as core or border)
    for dp in dp_list:
        if dp.category == UNCATEGORIZED:
            dp.category = NOISE

    #DEBUG
    '''for dp in dp_list:
        print "-----"
        print dp.loc
        print dp.category'''


    print "Removing Noise Points..."
    #Now lets remove the noise points from consideration
    flagged_for_removal = []
    for dp in dp_list:
        if dp.category == NOISE:
            flagged_for_removal.append(dp)

    print len(flagged_for_removal)
    for item in flagged_for_removal:
        dp_list.remove(item)

    #DEBUG
    '''for dp in dp_list:

        if dp.category==NOISE:
            print "-----"
            print dp.loc
            print dp.category'''

    print "Linking Core Points..."
    #create edges between all core points within eps of one another
    for dp in dp_list:
        if dp.category == CORE:
            for distance_tuple in dp.distance_list:

                dist = distance_tuple[0]
                adj_point = distance_tuple[1]

                #don't create an edge to yourself
                if adj_point == dp:
                    continue

                #if its within eps of another core point, create an edge to that point
                #don't worry about reciprocating it as it will be done
                #on another iteration of the loop
                if (dist <= eps) and (adj_point.category == CORE):
                    dp.adjacency_list.append(adj_point)

        elif dp.category == NOISE:
            print "WARNING: Found a noise point that shouldn't be there..."
            print "Exiting..."
            exit()
        else:
            continue

    #DEBUG
    '''for dp in dp_list:
        print "-----"
        print "Location",dp.loc
        print "Category:",dp.category
        for adj_point in dp.adjacency_list:
            print "     Adj Point Loc:",adj_point.loc
            print "     Adj Point Cat:",adj_point.category
            print ""
        print " "

    exit()'''



    print "Identifying connected componenets (labeling clusters)"
    #basically, this is identifying the clusters
    set_list = identify_connected_components(dp_list)

    #DEBUG
    '''for current_set in set_list:
        print "----"
        for element in current_set:
            print element.loc'''


    #finally, add the border points to clusters
    #The border points arbitrarily attach to the first core cluster within EPS
    print "Connecting Border Points..."
    for dp in dp_list:
        if dp.category == BORDER:
            add_border(dp, set_list, eps)



    #now go through each set and find the smallest and largest value
    #this wil become the cluster bounds that we use
    cluster_list=[]

    print "Outputting as 'gap' estimations..."
    for current_set in set_list:
        largest_val = 0
        smallest_val = 999999999999

        for dp in current_set:

            value = dp.loc

            if value > largest_val:
                largest_val = value

            if value < smallest_val:
                smallest_val = value


        tuple=(smallest_val, largest_val)

        cluster_list.append(tuple)



    return cluster_list

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




