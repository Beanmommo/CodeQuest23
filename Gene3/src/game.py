import random

import comms
from object_types import ObjectTypes
import sys
import math
from enum import Enum

class AvoidBoundaryAngle(Enum):
    """
    Enum to get angle move direction if close to certain vertex
    """
    TOPLEFT_V = 0
    TOPRIGHT_V = 1
    BOTLEFT_V = 2
    BOT_RIGHT= 3

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
        self.last_path_req = None
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"
                                                        ]
        self.closing_boundaries_key = None
        self.current_turn_message = None
        self.enemy_tank = None
        self.my_tank = None

        # We will store all game objects here
        self.objects = {}

        #Initialise static values
        self.UPDATED_OBJECTS = "updated_objects"
        self.DELETED_OBJECTS = "deleted_objects"
        self.MESSAGE = "message"

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

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])
        
        

        #Values that need to keep on track
        self.closing_boundaries = self.objects[self.closing_boundaries_key]
        self.enemy_tank = self.objects[self.enemy_tank_id]
        self.my_tank = self.objects[self.tank_id]

        return True
    def get_angle_direction(x_speed, y_speed):
        """
        Courtesy of ChatGPT
        get object angle direction from velocity input
        """
        # Calculate the angle in radians using atan2
        angle_rad = math.atan2(y_speed, x_speed)
        
        # Convert the angle from radians to degrees
        angle_deg = math.degrees(angle_rad)

        # Ensure the angle is within [0, 360] range
        if angle_deg < 0:
            angle_deg += 360

        return angle_deg
    
    def shoot_object_direction(self, target_object):
        """
        From our tank shoot to ;param; target_object
        target_object accepted ObjectType = Tank, Bullet, DestroyableWall
        """
        my_tank_position = self.my_tank["position"]
        target_object_position = target_object["position"]
        
        #Check if it is destructable wall
        if target_object["type"] == ObjectTypes.DESTRUCTIBLE_WALL.value:
            target_object_velocity = [0,0]
        else:
            target_object_velocity = target_object["velocity"]

        #Check distance of target in next 
        # TODO: continue after tank can see what surrounds him

        # init_distance = self.euclidean_distance(my_tank_position[0], my_tank_position[1], target_object_position[0], target_object_position[1])


    def shoot_direction(self, x1, y1, x2, y2):
        """
        Courtesy of ChatGPT
        
        """
        delta_x = x2 - x1
        delta_y = y2 - y1
        theta_radians = math.atan2(delta_y, delta_x)
        angle_degrees = math.degrees(theta_radians)
        if angle_degrees < 0:
            return 360 + angle_degrees
        return angle_degrees
    
    def euclidean_distance(self, x1, y1, x2, y2):
        """
        get distance from 2 object (1) and (2)
        """
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def get_direction_if_near_boundaries(self):
        boundary_position = self.closing_boundaries["position"]
        for vertex_index in range(len(boundary_position)):
            vx2, vy2 = boundary_position[vertex_index]
            tank_vertex_distance = self.euclidean_distance(self.my_tank[0], self.my_tank[0], vx2, vy2)
            #if tank_vertex_distance < 100:
            print(vertex_position)

        pass


    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Write your code here... For demonstration, this bot just shoots randomly every turn.

        #get game message
        post_message = {}
        

        #Find distance
        distance_from_enemytank = self.euclidean_distance(self.my_tank[0], self.my_tank[1], self.enemy_tank[0], self.enemy_tank[1])
        print(distance_from_enemytank, file=sys.stderr)

        #Find shoot angle
        if distance < 200:
            shoot_angle = self.shoot_direction(self.my_tank[0], self.my_tank[1], self.enemy_tank[0], self.enemy_tank[1])
            post_message["shoot"] = shoot_angle
        
        # print(updated_object_message, file=sys.stderr)
        # print("Start of test-------------------------------", file=sys.stderr)
        # print("END of test-------------------------------", file=sys.stderr)
        print(self.closing_boundaries)
        #Shoot 
        
        if self.last_path_req is None or self.last_path_req != self.enemy_tank:
            self.last_path_req = self.enemy_tank
            post_message["path"] = self.enemy_tank
        
        comms.post_message(post_message)
    
        


