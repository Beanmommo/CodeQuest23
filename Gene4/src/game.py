import random

import comms
from object_types import ObjectTypes
import math
import sys
from enum import Enum

class TankState(Enum):
    """
    DEFENSIVE - Tank does not use path and only rely on current_movement_direction
    GO_FOR_PU - Tank uses Path to grab PU
    ATTACK - Tank uses Path to go near player (Check func create_path_to_enemy_tank) - can change radius 

    GO_FOR_PU and ATTACK state will be changed to DEFENSIVE if tank near boundary plane
    """
    DEFENSIVE = 0
    GO_FOR_PU = 1
    ATTACK = 2
    

class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """
    def __init__(self):
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]
        self.current_turn_message = None

        #Tank information
        self.my_tank_dict = None
        self.enemy_tank_dict = None
        self.tank_state = TankState.DEFENSIVE

        #Set optimal velocity to >50%
        self.optimal_velocity = 141.42 * 0.5
        #Current Tank movement
        self.tank_current_movement_direction = None
        self.tank_current_path = None
        self.tank_current_PU_target = None
    

        #Tank object detection
        self.tank_detectable_object = {}

        #Game Info
        self.tick = 0
        # We will store all game objects here
        self.objects = {}

        #Key of the closing boundary
        self.closing_boundaries_key = None

        #Store each 4 boundaries
        self.top_right_boundary = None
        self.bot_right_boundary = None
        self.bot_left_boundary = None
        self.top_left_boundary = None

        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        boundaries = []
        for key in self.objects:
            
            game_object = self.objects[key]

            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)

            if game_object["type"] == ObjectTypes.CLOSING_BOUNDARY.value:
                self.closing_boundaries_key = key

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass
            try:
                del self.tank_detectable_object[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        #Update my tank and enemy tank
        self.my_tank_dict = self.objects[self.tank_id]
        self.enemy_tank_dict = self.objects[self.enemy_tank_id]

        #Update boundary
        self.top_left_boundary = self.objects[self.closing_boundaries_key]["position"][0]
        self.bot_left_boundary = self.objects[self.closing_boundaries_key]["position"][1]
        self.bot_right_boundary = self.objects[self.closing_boundaries_key]["position"][2]
        self.top_right_boundary = self.objects[self.closing_boundaries_key]["position"][3]

        #implement algorithm for items of interest around tank
        for key_object in self.objects:
            object_game = self.objects[key_object]

            #Skip boundaries 
            if object_game["type"] == ObjectTypes.CLOSING_BOUNDARY.value or object_game["type"] == ObjectTypes.BOUNDARY.value:
                continue
            
            #Check if near 500 unit of TANK
            #TODO: Check distance of object between tank Eliminate if too far
            object_pos = object_game["position"]
            distance_from_object = self.get_target_distance_from_tank(object_pos)

            #Automaticly add Health and Damage/ Avoid Speed(try not to go there)
            if object_game["type"] is ObjectTypes.POWERUP.value:
                if object_game["powerup_type"] is "HEALTH" or object_game["powerup_type"] is "DAMAGE":
                    self.tank_detectable_object[key_object] = object_game

                    #Initialise PU target
                    if self.tank_current_PU_target is None:
                        self.tank_current_PU_target = key_object
                    continue

            #Detectable range 500, remove anything not in range
            if distance_from_object > 500:
                try:
                    del self.tank_detectable_object[key_object]
                except KeyError:
                    pass
                continue
            # DO something with it
            match object_game["type"]:
                case ObjectTypes.TANK.value:
                    if key_object == self.tank_id:
                        continue
                    else:
                        # add object to tank_detectable_object
                        self.tank_detectable_object[key_object] = object_game
                        pass
                case ObjectTypes.BULLET.value:
                    # add object to tank_detectable_object
                    continue
                case ObjectTypes.WALL.value:
                    # Detect if it is so near, get other directionn
                    # add object to tank_detectable_object
                    continue
                case ObjectTypes.DESTRUCTIBLE_WALL.value:
                    # add object to tank_detectable_object
                    self.tank_detectable_object[key_object] = object_game
                    pass
                case _:
                    continue

        return True
    
    def get_target_distance_from_tank(self, target_pos):
        """
        get distance from own tank to target object
        object_type: Powerup, Tank, Bullet
        """

        return math.sqrt((target_pos[0] - self.my_tank_dict["position"][0])**2 + (target_pos[1] - self.my_tank_dict["position"][1])**2)
    
    def create_path_to_enemy_tank(self, tank_pos):
        """
        num_points and radius is hardcoded values
        """
        num_points = 6
        radius = 80

        min_distance = 9999
        coord_out = None
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = tank_pos[0] + radius * math.cos(angle)
            y = tank_pos[1] + radius * math.sin(angle)
            distance = self.get_target_distance_from_tank([x, y])
            if distance < min_distance:
                min_distance = distance
                coord_out = [math.ceil(x), math.ceil(y)]
            
        
        return coord_out
    
    def go_random_direction(self):
        """
        Return random angle 1-360 in Int.
        """
        return random.randint(1,360)
    
    def distance_tank_to_boundary(self, first_v_pos, second_v_pos):
        """
        Check distance between tank and boundary line
        :param: Combination of param can represent TOP_PLANE of boundary consisitng:
        first_v_pos as top_left_vertex
        second_v_pos as top_right_vertex
        NOTE: There are 4 Plane (TOP, LEFT, BOT and RIGHT)
        """
        # Calculate the perpendicular distance from the point (x0, y0) to the line (x1, y1)-(x2, y2)
        x0, y0 = self.my_tank_dict["position"][0], self.my_tank_dict["position"][1]
        x1, y1 = first_v_pos[0], first_v_pos[1]
        x2, y2 = second_v_pos[0], second_v_pos[1]
        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        return numerator / denominator
        


    def get_other_direction_if_near_boundary(self):
        """
        Get other random direction if near boundary
        NOTE: Find optimal value for define_near 
        """
        define_near = 90

        #Check all 4 boundaries 
        all_boundaries = {
            "top_plane": [self.top_right_boundary, self.top_left_boundary, 220, 320],
            "left_plane": [self.top_left_boundary, self.bot_left_boundary, 410, 310],
            "bot_plane": [self.bot_left_boundary, self.bot_right_boundary, 140, 40],
            "right_plane": [self.top_right_boundary, self.bot_right_boundary, 130, 230]
        }

        near_plane = []

        for key in all_boundaries:
            vertex_position_arr = all_boundaries[key]
            distance_from_plane = self.distance_tank_to_boundary(vertex_position_arr[0], vertex_position_arr[1])
            if distance_from_plane < define_near:
                near_plane.append(key)
        
        match(len(near_plane)):
            #Values are hardcoded FOV = 100 radius
            # First priority to cancel all path and find a new random angle
            case 1:
                plane = near_plane[0]
                if self.tank_state != TankState.DEFENSIVE:
                        self.tank_state = TankState.DEFENSIVE
                        self.tank_current_path = None
                        self.tick = -1
                if self.tank_state is TankState.GO_FOR_PU:
                    try:
                        del self.tank_detectable_object[self.tank_current_PU_target]
                    except KeyError:
                        pass
                    self.tank_current_PU_target = None
                    
                match(plane):
                    case "top_plane":
                        self.tank_current_movement_direction = random.randint(220,320)
                    case "left_plane":
                        self.tank_current_movement_direction = random.randint(310, 410)
                    case "bot_plane":
                        self.tank_current_movement_direction = random.randint(40,140)
                    case "right_plane":
                        self.tank_current_movement_direction = random.randint(130, 230)
                    case _:
                        pass
            case _:
                pass
    
    def shoot_direction(self, target_pos):
        """
        Courtesy of ChatGPT
        modified to likings :)
        """
        x1, y1 = self.my_tank_dict["position"][0], self.my_tank_dict["position"][1]
        x2, y2 = target_pos[0], target_pos[1]
        delta_x = x2 - x1
        delta_y = y2 - y1
        theta_radians = math.atan2(delta_y, delta_x)
        angle_degrees = math.degrees(theta_radians)
        if angle_degrees < 0:
            return 360 + angle_degrees
        return random.uniform(angle_degrees - 3, angle_degrees + 3)
    
    def check_if_tank_in_optimal_velocity(self):
        """
        Check velocity of the tank, if they are in optimal velocity
        :return: Bool
        True if tank in optimal velocity
        False if not
        """
        tank_velocity_float = self.my_tank_dict["velocity"]
        current_tank_velocity = math.sqrt(tank_velocity_float[0]**2 + tank_velocity_float[1]**2)
        if current_tank_velocity > self.optimal_velocity:
            return True
        else:
            return False
        

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """
        pause_tick = False
        # Write your code here... For demonstration, this bot just shoots randomly every turn.
        post_message = {}

        #Check if tank is not moving on optimum speed
        if self.check_if_tank_in_optimal_velocity() is False:
            # change movement direction
            self.tank_current_movement_direction = self.go_random_direction()

        #Check if there is important powerups!! when defensive mode
        if self.tank_state is TankState.DEFENSIVE:
            for key in self.tank_detectable_object:
                object_game = self.tank_detectable_object[key]
                if object_game["type"] is ObjectTypes.POWERUP.value:
                    self.tank_current_PU_target = key
                    self.tank_state = TankState.GO_FOR_PU
                    break

        #If current path is initialised

        match(self.tank_state):
            case TankState.DEFENSIVE:
                #Check init stage - DEFENSIVE is always init
                if self.tank_current_movement_direction is None and self.tank_current_path is None:
                    self.tank_current_movement_direction = self.go_random_direction()
                
                #If Path is None keep moving
                if self.tank_current_path is None:
                    post_message["move"] = self.tank_current_movement_direction

            case TankState.ATTACK:

                #Check create path to enemy tank
                suggested_path = self.create_path_to_enemy_tank(self.enemy_tank_dict["position"])
                if self.tank_current_path is None or self.tank_current_path != suggested_path:
                    self.tank_current_path = suggested_path
                    post_message["path"] = suggested_path
                
                if self.my_tank_dict["velocity"] == [0.0,0.0]:
                    self.tank_state = TankState.DEFENSIVE

                    #re-initialise var
                    self.tick = -1
                    self.tank_current_movement_direction = None
                    self.tank_current_path = None
            
            case TankState.GO_FOR_PU:
                pause_tick = True
                if self.tank_current_path is None or self.tank_current_path != self.tank_detectable_object[self.tank_current_PU_target]:
                    self.tank_current_path = self.tank_detectable_object[self.tank_current_PU_target]
            case _:
                pass
        
        print(self.tank_state, file=sys.stderr)
        #Check object surrounding tank
        self.get_other_direction_if_near_boundary()
        #Post message
        #Check if enemy detectable -> Shoot whenever u see them
        try:
            enemy_on_site = self.tank_detectable_object[self.enemy_tank_id]
            post_message["shoot"] = self.shoot_direction(enemy_on_site["position"])
        except KeyError:
            pass
        if not pause_tick:
            self.tick += 1
        if self.tick > 15:
            self.tank_state = TankState.ATTACK
        comms.post_message(post_message)
