from utils import conexiones

class Router:
    def __init__(self, current_position, destination_position, conexiones, map):
        self.conexiones = conexiones
        
        self.current_position = current_position
        self.destination_position = destination_position

        self.current_lane = self.findLaneFromCoordinates(current_position)
        self.destination = self.findLaneFromCoordinates(destination_position)

        self.directions = {
                            "AR":  [0,  1],
                            "AL":  [0, -1],
                            "BR":  [-1, 0], 
                            "BL":  [1,  0], 
                            "CR":  [0, -1], 
                            "CL":  [0,  1], 
                            "DR":  [1,  0],
                            "DL":  [-1, 0]
                          }

        self.map = map
        self.target_direction = None
        self.target_final_direction = None
        self.target_intersection = None
        self.target_lane = None
        self.target_position = None
    

    def findConnection(self):
        sectionA = self.current_lane[:2]
        quadrantB =self.destination[:1]
        
        for i in range(1, 4):
            neighboor = f"{sectionA}{i}"
            lanes = conexiones[neighboor]["Carriles"]
            
            if self.destination in lanes:
                direction = self.directions[sectionA]
                intersection = [conexiones[neighboor][f"{quadrantB}x"], conexiones[neighboor][f"{quadrantB}y"]]
                position = [conexiones[neighboor]["end_x"], conexiones[neighboor]["end_y"]]

                self.target_direction = direction
                self.target_final_direction = self.directions[self.destination[:2]]
                self.target_intersection = intersection
                self.target_lane = neighboor
                self.target_position = position
                 

                return [neighboor, position, direction, intersection]

        print("Unable to find a route to the destination")
        return 
    
    def findLaneFromCoordinates(self, coordinates):

        for key, element in self.conexiones.items():
            start_x, end_x, start_y, end_y = element["start_x"], element["end_x"], element["start_y"], element["end_y"]
            
            bounds_x = sorted([start_x, end_x])
            bounds_y = sorted([start_y, end_y])

            is_x_in_bounds = self.isInBounds(coordinates[0], bounds_x)
            is_y_in_bounds = self.isInBounds(coordinates[1], bounds_y)


            if start_x == end_x and coordinates[0] == start_x and is_y_in_bounds:
                return key
            if start_y == end_y and coordinates[1] == start_y and is_x_in_bounds:
                return key
        return 

    def isInBounds(self, element, bounds):
        
        return (bounds[0] <= element and element <= bounds[1])

    def resetRouter(self, current_position, destination_position):
        self.current_position = current_position
        self.destination_position = destination_position

        self.current_lane = self.findLaneFromCoordinates(current_position)
        self.destination = self.findLaneFromCoordinates(destination_position)