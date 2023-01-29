from router import Router
from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import random
import numpy as np
from utils import conexiones, mapa

def getStatusGrid(model):
    result = mapa.copy()
    for (content, x, y) in model.grid.coord_iter():
        for elem in content:
            if isinstance(elem, CarAgent) and not (x==0 and y ==0):
                result[x][y] = 8
    return result

class CarAgent(Agent):
    """An agent"""
    def __init__(self, unique_id, model, final_destination):
        super().__init__(unique_id, model)
        self.temp_id = unique_id
        self.state = 0        
        self.router = Router(list(reversed(unique_id)), final_destination, conexiones, mapa)
        self.route = self.router.findConnection()
        self.route_available = self.route is not None
        self.next_step = 0
        self.final_destination = final_destination

    def step(self):
        if self.route_available:
            self.current_position = np.array(self.pos)

            """
            State 1 = Antes de interseccion
            State 2 = Durante interseccion
            State 3 = Cuando llego a su destino 
            """
            if self.state == 0:
                self.moveToTargetPosition()

            if self.state == 1 or self.state == 2:
                self.moveToIntersection()

            if self.state == 3:
                start_pos, end_pos = self.model.moveCarToStart()
                self.resetRouter(start_pos, end_pos)
                self.move(tuple(reversed(start_pos)))
                self.temp_id = (self.temp_id[0] * -1, self.temp_id[1] * -1)

    def resetRouter(self, current_position, destination_position):
        self.state = 0

        self.router.resetRouter(current_position, destination_position)
        self.route = self.router.findConnection()

        self.route_available = self.route is not None
        self.next_step = 0

        self.final_destination = destination_position

    def moveToTargetPosition(self):
        
        target = self.convertCoords(self.router.target_position)

        if (self.current_position == target).all():
            self.state = 1
            return 

        direction = self.convertCoords(self.router.target_direction)
        
        lane_vector = self.getLaneVector(target, direction)

        side_coords = self.current_position + lane_vector
        diagonal_top_coords = self.current_position + direction + lane_vector
        diagonal_bottom_coords = self.current_position + lane_vector - direction
        top_coords = self.current_position + direction

        side = self.willCrash(side_coords)
        diagonal_top = self.willCrash(diagonal_top_coords)
        diagonal_bottom = self.willCrash(diagonal_bottom_coords)
        top = self.willCrash(top_coords)
        can_move_forward = self.canMoveForward(target, direction)
       
        # Caso 1: Moverse al lado
        new_position = self.current_position
        if not side and not diagonal_bottom:
            new_position = side_coords
        # Caso 2: Moverse en diagonal
        elif not diagonal_top and not side and can_move_forward:
            new_position = diagonal_top_coords
        # Caso 3: Moverse al frente
        elif not top and can_move_forward:
            new_position = top_coords

        self.move(new_position)
        
        return 

    def moveToIntersection(self):
        
        target = self.convertCoords(self.router.target_intersection)
        direction = self.convertCoords(self.router.target_direction)
        if self.lightIsGreen():
            if self.canMoveForward(target, direction):
                new_position = self.current_position + direction
                
                if not self.willCrash(new_position):
                    self.move(new_position)
            else:
                target_final_direction = self.convertCoords(self.router.target_final_direction)
                final_target = self.convertCoords(self.router.destination_position)

                if self.canMoveForward(final_target, target_final_direction):
                    new_position = self.current_position + target_final_direction
                    
                    if not self.willCrash(new_position):
                        
                        self.move(new_position)
                else:
                    self.state = 3
        return

    def move(self, position):
        if not self.model.grid.out_of_bounds(position):
            self.model.grid.move_agent(self, tuple(position))
        return 

    def willCrash(self, position):
        position = position.astype(int)
        if self.model.grid.out_of_bounds(position) or not bool(self.router.map[position[0], position[1]]):
            return True
        
        cellmates = self.model.grid.get_cell_list_contents([position.tolist()])

        for mate in cellmates:
            if type(mate) is CarAgent:
                return True
        return False
    
    def canMoveForward(self, position, direction):
        # Caso 1: [1,0]
        # Caso 2: [-1,0]
        # Caso 3: [0,1]
        # Caso 4: [0,-1]

        if direction[0] == 1:
            return self.current_position[0] < position[0]
        if direction[0] == -1:
            return self.current_position[0] > position[0]
        if direction[1] == 1:
            return self.current_position[1] < position[1]
        if direction[1] == -1:
            return self.current_position[1] > position[1]

    def getLaneVector(self, position, direction):
        lane_vector = np.array([0,0])
        if direction[0] == 0:
            if position[0] < self.current_position[0]:
                lane_vector += np.array([-1,0])
            elif position[0] > self.current_position[0]:
                lane_vector += np.array([1, 0])
        else:
            if position[1] < self.current_position[1]:
                lane_vector += np.array([0,-1])
            elif position[1] > self.current_position[1]:
                lane_vector += np.array([0, 1])
        return lane_vector

    def convertCoords(self, coords):
        return np.array(list(reversed(coords)))
    
    def canMoveInTransition(self):
        # Revisar si el carro ya se encuentra dentro del segundo estado significa que 
        # ya no le importa que el semaforo esté en verde porque ya esta en su linea destino
        if(self.state == 2):
            return True
        # Si el semaforo activo es el mismo que el cuadrante del carro 
        if (self.router.current_lane[:2] == self.model.semaphores[self.model.current_semaphore]):
            """
            Si la diferencia de coordenadas es menor al numero de ticks restantes
            significa que el carro va a terminar en la linea direccion destino 
            sin riesgo a que le choquen (puede verse como semaforo en amarillo) 
            """
            # TODO
            self.state = 2
            return True
        return False

    def lightIsGreen(self):
        # SI ESTA EN VERDE Y LA DISTANCIA QUE LE VA A TOMAR LLEGAR al otro punto
        # es menor que el tiempo en ticks que queda entonces nos movemos
        return self.canMoveInTransition()
    
"""
Clase principal de ejecucion del modelo de simulacion
"""
class TrafficSimulator(Model):
    """A car cruise simulation model with some car agents"""
    def __init__(self, N, M, start_sections = ["A","B","C","D"] , number_of_agents= 5, ticks = 15):
        self.num_agents = 1
        self.grid = MultiGrid(N, M, False)
        self.schedule = SimultaneousActivation(self)
        self.start_sections = start_sections
        self.numberOfTicks = ticks
        self.ticks_left = ticks
        self.current_semaphore = self.random.randint(0, 3)
        self.semaphores = ["AR","BR","CR","DR"]
        
        self.num = 0

        seen = set()
        
        for index in range(number_of_agents):
            while True:
                start, end = (self.generateCoordsForCar())
                if tuple(start) not in seen:
                    seen.add(tuple(start))
                    break
                
            a = CarAgent(tuple(reversed(start)), self, end)
            self.schedule.add(a)
            self.grid.place_agent(a, tuple(reversed(start)))

        self.datacollector = DataCollector(
            model_reporters={"Grid": getStatusGrid}
        )

    """ 
    El modelo ejecuta un paso para incrementar el numero de
    la iteracion y recolectar datos del momento en el grid
    """
    def step(self):
        """Advance the model by one step."""
        
        self.ticks_left -= 1
        #Actualizar Semaforos
        if self.ticks_left == -1:
            self.ticks_left = self.numberOfTicks
            self.current_semaphore += 1
            self.current_semaphore %= 4
        self.num += 1
        self.datacollector.collect(self)
        
        self.schedule.step()
        
    """
    Genera coordenadas de inicio y final random validas con ayuda de los datos del grafo
    determinado para la instanciacion de los carros usando cualquiera de los cuadrantes y
    sus vecinos accesibles A,B,C,D (Se entiende como punto de inicio un '[Section]R' y como final un '[Section]L')
    """
    def generateCoordsForCar(self):
        start_section = random.choice(self.start_sections)
 
        possible_connections = list(conexiones.keys())
        possible_start_lanes = (list(filter(lambda x : x[:2] == f"{start_section}R", possible_connections)))

        possible_end_lanes = []
        for possible_lane in possible_start_lanes:
            possible_ends = ((conexiones[possible_lane]["Carriles"]).split(","))
            possible_ends = [possible_end.strip() for possible_end in possible_ends]
            possible_end_lanes.extend(possible_ends)

        random_start_lane =  random.choice(possible_start_lanes)
        random_end_lane = random.choice(possible_end_lanes)
        
        start_conexiones = conexiones[random_start_lane] 
        end_conexiones = conexiones[random_end_lane]

        start_range_x = sorted([start_conexiones["start_x"], start_conexiones["end_x"]])
        start_range_y = sorted([start_conexiones["start_y"], start_conexiones["end_y"]])

        end_range_x = sorted([end_conexiones["end_x"], end_conexiones["end_x"]])
        end_range_y = sorted([end_conexiones["start_y"], end_conexiones["end_y"]])

        start_x = start_conexiones["start_x"] if start_conexiones["start_x"] == start_conexiones["end_x"] else random.randint(*start_range_x) 
        start_y = start_conexiones["start_y"] if start_conexiones["start_y"] == start_conexiones["end_y"] else random.randint(*start_range_y) 

        end_x = end_conexiones["start_x"] if end_conexiones["start_x"] != end_conexiones["end_x"] else random.randint(*end_range_x)
        end_y = end_conexiones["start_y"] if end_conexiones["start_y"] != end_conexiones["end_y"] else random.randint(*end_range_y)
        
        return [start_x, start_y], [end_x, end_y]

    """
    Genera coordenadas de inicio y final  en puntos iniciales random validos con ayuda 
    de los datos del grafo determinado para la instanciacion de los carros usando 
    cualquiera de los cuadrantes y sus vecinos accesibles A,B,C,D (Se entiende como 
    punto de inicio un '[Section]R' y como final un '[Section]L')
    """
    def moveCarToStart(self):
    
        start_section = random.choice(self.start_sections)
 
        possible_connections = list(conexiones.keys())
        
        # Tomar las lineas de inicio random en un cuadrante 
        possible_start_lanes = (list(filter(lambda x : x[:2] == f"{start_section}R", possible_connections)))

        # Darnos las lineas finales de los posibles carriles validos en el grafo  
        possible_end_lanes = []
        for possible_lane in possible_start_lanes:
            possible_ends = ((conexiones[possible_lane]["Carriles"]).split(","))
            possible_ends = [possible_end.strip() for possible_end in possible_ends]
            possible_end_lanes.extend(possible_ends)

        random_start_lane =  random.choice(possible_start_lanes)
        random_end_lane = random.choice(possible_end_lanes)
        
        start_conexiones = conexiones[random_start_lane] 
        end_conexiones = conexiones[random_end_lane]

        start_x = start_conexiones["start_x"] 
        start_y = start_conexiones["start_y"]

        end_x = end_conexiones["start_x"]
        end_y = end_conexiones["start_y"]
        
        return [start_x, start_y], [end_x, end_y]

    def status_agentes(model):
        data = []

        for (content, x, y) in model.grid.coord_iter():
            for elem in content:
                if isinstance(elem, CarAgent) and not (x==0 and y ==0):
                    data.append({'carroID': elem.temp_id, 'wayPointID': 21 * x + y})
        return data

    def get_status_lights(model):
        return model.current_semaphore