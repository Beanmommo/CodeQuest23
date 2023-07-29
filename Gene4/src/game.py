import random

import comms
from object_types import ObjectTypes
import math
import sys

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

        self.tank_current_movement_direction = None
        self.tank_current_path = None

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

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        #Update my tank and enemy tank
        self.my_tank_dict = self.objects[self.tank_id]
        self.enemy_tank_dict = self.objects[self.enemy_tank_id]

        #Update boundary
        self.top_right_boundary = self.objects[self.closing_boundaries_key]["position"][0]
        self.bot_right_boundary = self.objects[self.closing_boundaries_key]["position"][1]
        self.bot_left_boundary = self.objects[self.closing_boundaries_key]["position"][2]
        self.top_left_boundary = self.objects[self.closing_boundaries_key]["position"][3]

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
            if distance_from_object > 300:
                continue
            # DO something with it
            match object_game["type"]:
                case ObjectTypes.TANK.value:
                    print("TANK DETECTED", file=sys.stderr)
                case ObjectTypes.BULLET.value:
                    print("BULLET DETECTED", file=sys.stderr)
                case ObjectTypes.WALL.value:
                    print("WALL DETECTED", file=sys.stderr)
                case ObjectTypes.DESTRUCTIBLE_WALL.value:
                    print("DESTRUCTIBEL WALL DETECETED", file=sys.stderr)
                case ObjectTypes.BOUNDARY.value:
                    # Skip boundary object type
                    continue
                case ObjectTypes.CLOSING_BOUNDARY.value:
                    # Skip Closing Boundary object type
                    continue
                case ObjectTypes.POWERUP.value:
                    print("POWERUP DETECETD", file=sys.stderr)
                case _:
                    continue

            

            pass
        print("-----------END OF Obv----------", file=sys.stderr)
        print(self.tank_id, file=sys.stderr)
        print("-----------END OF Obv----------", file=sys.stderr)

        return True
    
    def get_target_distance_from_tank(self, target_pos):
        """
        get distance from own tank to target object
        object_type: Powerup, Tank, Bullet
        """
        x_target, y_target = target_pos[0], target_pos[1]
        
        tank_pos = self.my_tank_dict["position"]
        x_tank, y_tank = tank_pos[0], tank_pos[1]

        return math.sqrt((x_target - x_tank)**2 + (y_target - y_tank)**2)
    

    def go_random_direction(self):
        return random.randint(1,360)
    

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Write your code here... For demonstration, this bot just shoots randomly every turn.
        post_message = {}

        #Check init stage
        if self.tank_current_movement_direction is None and self.tank_current_path is None:
            self.tank_current_movement_direction = self.go_random_direction()
        
        #If Path is None keep moving
        if self.tank_current_path is None:
            post_message["move"] = self.tank_current_movement_direction

        #Check object surrounding tank
        
        #Post message
        comms.post_message(post_message)
