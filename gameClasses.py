import struct

import numpy as np
import pygame
from math import cos, sin

# This is the base class of all objects in my game that have no image (they are just rectangles)
class MySprite(pygame.sprite.Sprite):
    def __init__(self, size: tuple, colour, initialPos=(0, 0)):
        super().__init__()
        self.rect: pygame.Rect = pygame.Rect(initialPos, size)
        self.image: pygame.Surface = pygame.Surface(size).convert_alpha()
        self.image.fill(colour)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect.topleft)

class CollisionCharacter(MySprite):
    """
    Characters with programmed collision. Gravity applies to them.
    Their physics are the exact same as the main player
    """
    def __init__(self, size: tuple, colour, initialPos=(0, 0)):
        super().__init__(size, colour, initialPos)
        self.xSpeed = 1
        self.ySpeed = 0
        self.isGrounded: bool = False

    def fall(self, *args, **kwargs):
        pass

    def on_top_collision(self, *args, **kwargs):
        """
        What happens when character lands on top of a platform
        """
        pass

    def on_left_collision(self, *args, **kwargs):
        """
        What happens when character collides with the left of a platform
        """
        pass

    def on_right_collision(self, *args, **kwargs):
        """
        What happens when character collides with the right of a platform
        """
        pass

    def on_bottom_collision(self, *args, **kwargs):
        """
        What happens when character collides with the bottom of a platform
        """
        pass

    def on_spike_collision(self, *args, **kwargs):
        pass

    def collision_update(self, all_platforms, all_semi_solid_platforms):
        if (self.rect.collidelist([obj.rect for obj in all_platforms]) == -1 and
                self.rect.collidelist([obj.rect for obj in all_semi_solid_platforms]) == -1):
            self.isGrounded = False

        # Make sure that the character is falling if they are in the air
        if not self.isGrounded:
            self.fall()

        # This is the main collision detection algorithm for a character with regular platforms
        for obj in all_platforms:
            # Platform Lines format: top, left, right, bottom
            # We need to split the platform into edges so that we can push the player into the correct direction
            # (away from the edge)
            for i in range(4):
                clipped = self.rect.clipline(obj.sides[i])

                if clipped:
                    # Checking collision with top side of platform (the floor for the character)
                    if i == 0:
                        # Only stops the character if they are falling onto the platform
                        # and if the character's centre is above the platform
                        if self.ySpeed > 0 and self.rect.centery <= obj.rect.topleft[1]:
                            self.ySpeed = 0
                            self.isGrounded = True
                            diff_in_y_coord = self.rect.bottomright[1] - clipped[0][1]
                            # Now do anything extra that is required for the specific character
                            self.on_top_collision()

                        else:
                            diff_in_y_coord = 0

                        self.rect.move_ip(0, -diff_in_y_coord)


                    # Checking collision with left side of platform
                    # If the character is resting on the corner of the platform or jumping from below,
                    # we want to ignore the collision with the left and right sides
                    elif i == 1:
                        if (self.rect.bottom - 1 > obj.rect.top
                                and self.rect.top < obj.rect.bottom - 3):
                            diff_in_x_coord = self.rect.topright[0] - clipped[0][0]
                            self.rect.move_ip(-diff_in_x_coord - 1, 0)
                            self.xSpeed = 0
                            self.on_left_collision()


                    # Checking collision with right side of platform
                    elif i == 2:
                        if (self.rect.bottom - 1 > obj.rect.top
                                and self.rect.top < obj.rect.bottom - 3):
                            diff_in_x_coord = self.rect.topleft[0] - clipped[0][0]
                            self.rect.move_ip(-diff_in_x_coord + 1, 0)
                            self.xSpeed = 0
                            self.on_right_collision()

                    # Checking collision with bottom side of platform
                    elif i == 3:
                        self.ySpeed = 0
                        diff_in_y_coord = clipped[0][1] - self.rect.topright[1]
                        self.rect.move_ip(0, diff_in_y_coord + 2)
                        self.on_bottom_collision()

                    # Deal with spikes for the character
                    if type(obj) is Spikes:
                        if obj.spiky_side == i:
                            self.on_spike_collision(isTopSide=i == 0, platform=obj)

            # See if character player is colliding with a moving platform
            if type(obj) is MovingPlatform:
                # Check if character is 1 pixel above platform
                if self.rect.colliderect(obj.movement_rect):
                    self.rect.move_ip(obj.velocity)


        # This is the collision detection algorithm for a character with semi-solid platforms
        for obj in all_semi_solid_platforms:
            clipped = self.rect.clipline(obj.top_side)
            # If there is a collision
            if clipped:
                # Check if the character was above the platform on the previous frame
                if self.rect.bottomleft[1] - self.ySpeed <= obj.top_side[0][1]:
                    self.rect.y += obj.top_side[0][1] - self.rect.bottomleft[1]
                    self.isGrounded = True
                    self.ySpeed = 0
                    self.on_top_collision()


class Player(CollisionCharacter):
    # Some constants for the player
    def __init__(self, size: tuple, colour, is_invulnerable_eventID, initialPos):
        super().__init__(size, colour, initialPos)
        self.orig_image = self.image.copy()
        self.xSpeed = 0
        self.ySpeed = 0
        self.health = 4
        self.orientation = 0
        self.max_horizontal_speed = 5
        self.max_vertical_speed = 7.5
        self.isGrounded: bool = False
        self.isSpinning: bool = False
        self.canGroundPound: bool = True
        self.invulnerable_event = is_invulnerable_eventID
        self.iframes_left = 0  # This is used for triggering i_frames
        self.is_invisible: bool = False  # Used for iFrame animation
        self.internalTimer = 0  # Used purely for small animations (like ground pounds)

    def rotate(self, angle):
        self.orientation += angle
        self.image = pygame.transform.rotozoom(self.orig_image, self.orientation, 1)
        # Create a new rect with the center of the old rect.
        # Otherwise, the image will scale up and distort
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, amount=1):
        self.health -= amount
        self.iframes_left = 16
        pygame.time.set_timer(self.invulnerable_event, 125, 16)

    def draw(self, screen):
        if not self.is_invisible:
            super().draw(screen)

    def on_top_collision(self, *args, **kwargs):
        # The only extra thing the player needs to do is reset
        # the canGroundPound flag
        self.canGroundPound = True

    def on_spike_collision(self, *args, **kwargs):
        if self.iframes_left == 0:
            # Deal with the special case of the top side
            if kwargs['isTopSide']:
                if kwargs['platform'].rect.topleft[0] < self.rect.centerx < kwargs['platform'].rect.topright[0]:
                    self.take_damage()
                    pygame.time.set_timer(self.invulnerable_event, 125, 16)
            else:
                self.take_damage()
                pygame.time.set_timer(self.invulnerable_event, 125, 16)

    def fall(self):
        # Remember that down on the y-axis is positive and the top of the screen is (0,0)
        self.ySpeed += 0.3
        if self.ySpeed > self.max_vertical_speed:
            self.ySpeed = self.max_vertical_speed

    def ground_pound(self, clock):
        self.xSpeed = 0
        self.ySpeed = 0

        if self.orientation < 360:
            self.internalTimer += clock.get_time()
            if self.internalTimer > 0.02:
                self.rotate(18)
        else:
            self.isSpinning = False
            self.orientation = 0
            self.image = self.orig_image
            self.rect = self.image.get_rect(center=self.rect.center)
            self.canGroundPound = False
            self.ySpeed = 8
            self.max_vertical_speed = 12

    def decelerate(self):
        if self.xSpeed > 0:
            if self.isGrounded:
                self.xSpeed -= 0.32  # It takes a little while to fully decelerate
            else:
                self.xSpeed -= 0.1

            if self.xSpeed < 0:
                self.xSpeed = 0

        elif self.xSpeed < 0:
            if self.isGrounded:
                self.xSpeed += 0.32
            else:
                self.xSpeed += 0.1

            if self.xSpeed > 0:
                self.xSpeed = 0

    def jump(self, highJump):
        if self.isGrounded:
            if highJump:
                self.max_vertical_speed = 10
            else:
                self.max_vertical_speed = 7.5

            self.ySpeed = -1 * self.max_vertical_speed
            self.isGrounded = False

class Fool(CollisionCharacter):
    """
    This class is for the enemy called Fools.
    They are simple enemies: they will continue in 1 direction until they fall off a platform or bump into a wall
    They will also NOT target the player but will damage the player if the player walks into them
    If the player jumps on them (the bottom left of the player is above their centre), they will be squished
    """
    character_code = "0"

    def __init__(self, initialPos):
        super().__init__((20, 20), (255, 0, 0), initialPos)
        self.MAX_VERTICAL_SPEED = 7.5  # Allows Fool to accelerate downwards (not necessary for all enemies)
        self.internal_timer = 0  # Used for squishing animation
        self.isBeingSquished = False
        self.isGrounded = True


    def become_squished(self) -> None:
        """
        This function is to be used iteratively (i.e. multiple times)
        """
        self.image = pygame.transform.scale(self.image, (1, 0.5))
        self.rect.height /= 2
        if self.rect.height < 1:
            # Once the enemy is "dead", it is removed from all the groups
            self.kill()

    def fall(self):
        self.ySpeed += 0.3
        if self.ySpeed > self.MAX_VERTICAL_SPEED:
            self.ySpeed = self.MAX_VERTICAL_SPEED

    def on_left_collision(self, *args, **kwargs):
        self.xSpeed = -2

    def on_right_collision(self, *args, **kwargs):
        self.xSpeed = 2

    def update(self, all_platforms, all_semi_solid_platforms) -> None:
        """
        This is a simple function that contains the main logic of the Fool
        but does not include interactions with the player (that's in main.py)
        """
        self.rect.move_ip(self.xSpeed, self.ySpeed)
        self.collision_update(all_platforms, all_semi_solid_platforms)

class GhostPursuer(MySprite):
    """
    This class consists of an enemy that can travel through walls and platforms.
    They will always pursue the player but very slowly.
    They do not interact with other enemies.
    When they damage the player, they disappear
    """
    character_code = "1"

    def __init__(self, initialPos):
        # The ghost starts fully transparent
        GHOST_RADIUS = 10
        super().__init__((20, 20), (0, 0, 0, 255), initialPos)
        pygame.draw.circle(self.image, (255, 0, 0, 50), (GHOST_RADIUS, GHOST_RADIUS), GHOST_RADIUS)
        self.collision_rect = self.rect.copy()
        self.collision_rect.scale_by_ip(0.8, 0.8)
        self.floatingPointCenter: pygame.Vector2 = pygame.Vector2(self.rect.center)
        self.MAX_SPEED = 1.7

    def update(self, player_position: tuple):
        # Calculate difference between x and difference between y
        diff_in_x: float = player_position[0] - self.rect.centerx
        diff_in_y: float = player_position[1] - self.rect.centery
        translation = pygame.Vector2()

        if diff_in_x != 0:
            gradient = diff_in_y / diff_in_x
            translation.update(1, gradient)

        else:
            translation.update(diff_in_x, diff_in_y)

        if translation.length_squared() != 0:
            translation.scale_to_length(self.MAX_SPEED)

        if player_position[0] < self.rect.centerx:
            translation.update(-1 * translation.x, -1 * translation.y)

        self.floatingPointCenter += translation
        self.rect.center = round(self.floatingPointCenter.x), round(self.floatingPointCenter.y)
        self.collision_rect.center = self.rect.center

class JumpingFool(Fool):
    character_code = "2"

    def __init__(self, initialPos):
        super().__init__(initialPos)
        self.isBeingSquished = False  # Might add squishing later or remove it entirely
        self.MAX_VERTICAL_SPEED = 10

    def on_top_collision(self, *args, **kwargs):
        # Initiate jump again
        self.ySpeed = -8

class Platform(MySprite):
    code = "0"

    def __init__(self, size, colour, position, orientation=0):
        super().__init__(size, colour, position)
        self.orientation = orientation  # obsolete/ will not use (for now)

        # Rotate the image of the platform and update the rectangle
        # self.image = pygame.transform.rotozoom(self.image, -self.orientation, 1)
        # self.rect = self.image.get_rect(center=self.rect.center)

        # Top, left, right, bottom
        self.sides: list = []

        # Top left, top right, bottom left, bottom right
        self.orig_corners = [
            (-0.5 * self.rect.w, 0.5 * self.rect.h),
            (0.5 * self.rect.w, 0.5 * self.rect.h),
            (-0.5 * self.rect.w, -0.5 * self.rect.h),
            (0.5 * self.rect.w, -0.5 * self.rect.h)
        ]

        self.set_sides()

    def set_sides(self):
        """
        Identifies which corners are the top-left, top-right, etc.
        Then it uses that data to set the top sides
        """
        new_corners = []

        if self.orientation % 90 != 0:
            # Formula:
            # new_x = xcosθ - ysinθ
            # new_y = xsinθ + ycosθ
            for i in range(4):
                x = (self.rect.centerx + (self.orig_corners[i][0] * cos(self.orientation))
                     - (self.orig_corners[i][1] * sin(self.orientation)))
                y = (self.rect.centery + (self.orig_corners[i][0]*sin(self.orientation))
                     + (self.orig_corners[i][1] * cos(self.orientation)))
                new_corners.append((x, y))

            self.sides = [
                (new_corners[0], new_corners[1]),
                (new_corners[0], new_corners[2]),
                (new_corners[1], new_corners[3]),
                (new_corners[2], new_corners[3])
            ]

        else:
            temp_rect = self.image.get_rect(center=self.rect.center)
            self.sides = [
                (temp_rect.topleft, temp_rect.topright),
                (temp_rect.topleft, temp_rect.bottomleft),
                (temp_rect.topright, temp_rect.bottomright),
                (temp_rect.bottomright, temp_rect.bottomleft)
            ]


class Spikes(Platform):
    """
    This is a stationary enemy that is a literally just a platform that damages the player
    Spikes are drawn in triangles. Each triangle will have a fixed width of 10
    """
    code = "1"

    def __init__(self, noTriangles, height, position: tuple, orientation):
        """
        :param noTriangles: The number of triangles long
        :param height: The height of each triangle
        :param position: A tuple in the form (x, y)
        :param orientation: Clockwise rotation of object when upright. Must be either 0, 90, 180 or 270
        """
        TOP = 0
        LEFT = 1
        RIGHT = 2
        BOTTOM = 3

        triangle_width = 20
        offset = triangle_width / 2
        self.sides = []  # Doing this to ensure there's no errors later down the line

        # Create the image of triangles based on the orientation of the spikes specified
        # Must raise an error to catch invalid orientations since it makes debugging easier
        if orientation % 90 != 0:
            raise ValueError("The orientation of this object is not a multiple of 90")

        elif orientation > 270 or orientation < 0:
            raise ValueError("The orientation is either too low (below 0) or too high (above 270)")

        elif orientation == 0:
            # Spikes will generate upright
            super().__init__((noTriangles * triangle_width, height), (0, 0, 0, 0), position)
            self.spiky_side = TOP

            for i in range(noTriangles + 1):
                points: list = [
                    ((triangle_width * i) - offset, height),
                    (triangle_width / 2 + (triangle_width * i) - offset, 0),
                    (triangle_width + (triangle_width * i) - offset, height)
                ]

                pygame.draw.polygon(self.image, (255, 0, 0), points)

        elif orientation == 90:
            # Spikes face towards the right
            super().__init__((height, noTriangles * triangle_width), (0, 0, 0, 0), position)
            self.spiky_side = RIGHT

            for i in range(noTriangles + 1):
                points: list = [
                    (0, i * triangle_width - offset),
                    (height, (i * triangle_width) + (triangle_width / 2) - offset),
                    (0, triangle_width + (i * triangle_width) - offset)
                ]

                pygame.draw.polygon(self.image, (255, 0, 0), points)

        elif orientation == 180:
            # Spikes face downwards
            super().__init__((noTriangles * triangle_width, height), (0, 0, 0, 0), position)
            self.spiky_side = BOTTOM

            for i in range(noTriangles + 1):
                points: list = [
                    (triangle_width * i - offset, 0),
                    (triangle_width / 2 + (triangle_width * i) - offset, height),
                    (triangle_width + (triangle_width * i) - offset, 0)
                ]
                pygame.draw.polygon(self.image, (255, 0, 0), points)

        else:
            # Spikes face towards the left
            super().__init__((height, noTriangles * triangle_width), (0, 0, 0, 0), position)
            self.spiky_side = LEFT

            for i in range(noTriangles + 1):
                points: list = [
                    (height, i * triangle_width - offset),
                    (0, (i * triangle_width) + (triangle_width / 2) - offset),
                    (height, triangle_width + (i * triangle_width) - offset)
                ]

                pygame.draw.polygon(self.image, (255, 0, 0), points)

        self.rect = self.image.get_rect(topleft=position)  # Now get the rect of the image

        # Order: top, left, right, bottom
        self.sides = [(self.rect.topleft, self.rect.topright),
                      (self.rect.topleft, self.rect.bottomleft),
                      (self.rect.topright, self.rect.bottomright),
                      (self.rect.bottomleft, self.rect.bottomright)
                      ]


class SemiSolidPlatform(MySprite):
    """
    This class is used to represent platforms that only have one way collision:
    you can enter from the bottom and land on the top
    """

    code = "2"

    def __init__(self, size, position):
        super().__init__(size, (255, 0, 255), position)
        self.top_side = (self.rect.topleft, self.rect.topright)
        self.orientation = 0


class MovingPlatform(Platform):
    def __init__(self, size, colour, start_point: tuple[int, int], end_point: tuple[int, int]):
        super().__init__(size, colour, start_point)
        self.rect.topleft = start_point
        self.set_sides()

        # The below field is used to ensure the player moves with the platform
        # It is 1 pixel above the actual platform and only 1 pixel thick
        self.movement_rect = self.rect.copy()
        self.movement_rect.height = 1
        self.movement_rect.width -= 2
        self.movement_rect.topleft = (self.rect.left + 1, self.rect.top - 1)
        self.orientation = 0  # may add sloped platforms later
        self.internal_timer = 0
        self.path = (start_point, end_point)
        self.dest = 0
        self.velocity = pygame.Vector2()

    def update(self, clock: pygame.time.Clock):
        # Check if the platform has arrived at its destination
        if self.rect.topleft == self.path[self.dest]:
            # Set the timer and new destination
            self.internal_timer = 3000
            self.velocity.update((0, 0))
            self.dest = 1-self.dest

        elif self.internal_timer != 0:
            # Wait until the time is up
            self.internal_timer -= clock.get_time()
            if self.internal_timer <= 0:
                self.internal_timer = 0
                # Set the velocities of the platform
                if self.rect.left < self.path[self.dest][0]:
                    self.velocity.x = 1

                elif self.rect.left == self.path[self.dest][0]:
                    self.velocity.x = 0

                else:
                    self.velocity.x = -1

                if self.rect.top < self.path[self.dest][1]:
                    self.velocity.y = 1

                elif self.rect.top == self.path[self.dest][1]:
                    self.velocity.y = 0

                else:
                    self.velocity.y = -1

        # If the platform needs to get moving
        else:
            self.rect.move_ip(self.velocity)
            self.movement_rect.move_ip(self.velocity)
            self.set_sides()


class GameLevel:
    """
    This class represents a full level, and all the data associated with it.
    """
    def __init__(self, filePath):
        """
        Takes a set of text or binary data (haven't decided which to do yet) extracted from a file.
        It then unpacks the data and stores it accordingly
        :param filePath: a string that is the path to the file
        """


        self.all_platforms = [Spikes(8, 20, (150, 100), 0)]
        self.all_semi_solid_platforms = []
        self.all_enemies = pygame.sprite.Group()
        self.respawn_point: tuple = (0, 0)
        self.objectiveType = 0  # Not used for now

        # Time to read the file
        with open(filePath, "rt") as file:
            split_data = file.readline().split()
            self.respawn_point = (int(split_data[0]), int(split_data[1]))
            self.objectiveType = int(split_data[2])
            noEnemies = int(split_data[3])
            noPlatforms = int(split_data[4])

            # Record enemy data
            for i in range(noEnemies):
                split_data = file.readline().split()

                if int(split_data[0]) == 0:
                    # Record fool data
                    self.all_enemies.add(Fool((int(split_data[1]), int(split_data[2]))))

                elif int(split_data[0]) == 1:
                    # Record ghost pursuer
                    self.all_enemies.add(GhostPursuer((int(split_data[1]), int(split_data[2]))))

                elif int(split_data[0]) == 2:
                    # Record jumping fool
                    self.all_enemies.add(JumpingFool((int(split_data[1]), int(split_data[2]))))

            # Record platform data
            for i in range(noPlatforms):
                # Split the data up
                split_data = file.readline().split()
                if split_data[0] == "00":
                    # We are dealing with a stationary solid platform
                    self.all_platforms.append(
                        Platform(size=(int(split_data[1]), int(split_data[2])),
                                 colour=(0, 255, 0),
                                 orientation=int(split_data[3]),
                                 position=(int(split_data[4]), int(split_data[5]))
                                 )
                    )

                elif split_data[0] == "10":
                    # We are dealing with spikes
                    # Calculate the number of triangles
                    noTriangles = int(split_data[1])/20
                    self.all_platforms.append(
                        Spikes(noTriangles=noTriangles,
                               height=int(split_data[2]),
                               orientation=int(split_data[3]),
                               position=(int(split_data[4]), int(split_data[5]))
                               )
                    )


                elif split_data[0] == "20":
                    # We are dealing with a stationary semi-solid platform
                    self.all_semi_solid_platforms.append(
                        SemiSolidPlatform(size=(int(split_data[1]), int(split_data[2])),
                                          position=(int(split_data[4]), int(split_data[5]))
                                          )
                    )
                elif split_data[0] == "01":
                    # We are dealing with a moving solid platform
                    platform = MovingPlatform(
                            size=(int(split_data[1]), int(split_data[2])),
                            colour=(0, 255, 0),
                            start_point=(int(split_data[4]), int(split_data[5])),
                            end_point=(int(split_data[6]), int(split_data[7]))
                                 )
                    self.all_platforms.append(platform)


    def to_file(self, filePath) -> None:
        """
        Transforms level data into a file format. This is useful for a potential level
        creator in the future
        :param filePath: A string that is the path to the file, including the file name
        """

        # Format of file:
        # Metadata: respawn point (2), objective (1), no enemies (1), no platforms (1)
        # Enemies: type, initial position, etc.
        # Platforms: Type (solid, spikes, or semisolid), isMoving, width, height,
        # orientation, startPos, endPos (if moving)

        with open(filePath, "wt") as myFile:
            # METADATA
            myFile.write(str(self.respawn_point[0]) + " ")
            myFile.write(str(self.respawn_point[1]) + " ")
            myFile.write(str(self.objectiveType) + " ")
            myFile.write(str(len(self.all_enemies)) + " ")
            noPlatforms = len(self.all_platforms) + len(self.all_semi_solid_platforms)
            myFile.write(str(noPlatforms) + "\n")

            # Enemy data (just enemy type + initialPos)
            for enemy in self.all_enemies:
                # Write the enemy type (already in bytes)
                myFile.write(enemy.character_code + " ")
                # Write the enemy data here
                # For now, all enemies just have an initial position
                myFile.write(str(enemy.rect.left) + " ")
                myFile.write(str(enemy.rect.top) + "\n")

            # Platform data
            for platform in self.all_platforms + self.all_semi_solid_platforms:
                # There is no space after platform code on purpose
                myFile.write(platform.code)


                # Determine whether the platform is moving or not
                isMoving = type(platform) is MovingPlatform
                myFile.write(str(int(isMoving)) + " ")

                # Write the dimensions, orientation and starting position
                myFile.write(str(platform.rect.width) + " " + str(platform.rect.height) + " ")
                myFile.write(str(platform.orientation) + " ")
                myFile.write(str(platform.rect.left) + " " + str(platform.rect.top) + " ")

                if isMoving:
                    # Write the end positions of the platforms as well
                    myFile.write(str(platform.path[1][0]) + " " +
                                 str(platform.path[1][1]) + "\n")

                else:
                    # If it is not finished
                    myFile.write("\n")


