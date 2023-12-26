import math

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

class Player(MySprite):
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

    def collision_update(self, all_platforms, all_semi_solid_platforms, all_moving_platforms):
        if (self.rect.collidelist([obj.rect for obj in all_platforms]) == -1 and
                self.rect.collidelist([obj.rect for obj in all_semi_solid_platforms]) == -1):
            self.isGrounded = False

        # Make sure that the player is falling if they are in the air
        if not self.isGrounded:
            # Remember that down on the y-axis is positive and the top of the screen is (0,0)
            self.ySpeed += 0.3
            if self.ySpeed > self.max_vertical_speed:
                self.ySpeed = self.max_vertical_speed

        # This is the main collision detection algorithm for the player with regular platforms
        for obj in all_platforms:
            # Platform Lines format: top, left, right, bottom
            # We need to split the platform into edges so that we can push the player into the correct direction
            # (away from the edge)
            for i in range(4):
                clipped = self.rect.clipline(obj.sides[i])

                if clipped:
                    # Checking collision with top side of platform (the floor for the player)
                    if i == 0:
                        # Only stops the player if they are falling onto the platform
                        # and if the player's centre is above the platform
                        if self.ySpeed > 0 and self.rect.centery + 8 <= obj.rect.topleft[1]:
                            self.ySpeed = 0
                            self.isGrounded = True
                            diff_in_y_coord = self.rect.bottomright[1] - clipped[0][1]

                        else:
                            diff_in_y_coord = 0

                        self.rect.move_ip(0, -diff_in_y_coord)
                        self.canGroundPound = True


                    # Checking collision with left side of platform
                    # If the player is resting on the corner of the platform or jumping from below,
                    #   we want to ignore the collision with the left and right sides
                    elif i == 1:
                        if (self.rect.bottom - 1 > obj.rect.top
                                and self.rect.top < obj.rect.bottom - 3):
                            diff_in_x_coord = self.rect.topright[0] - clipped[0][0]
                            self.rect.move_ip(-diff_in_x_coord - 1, 0)
                            self.xSpeed = 0


                    # Checking collision with right side of platform
                    elif i == 2:
                        if (self.rect.bottom - 1 > obj.rect.top
                                and self.rect.top < obj.rect.bottom - 3):
                            diff_in_x_coord = self.rect.topleft[0] - clipped[0][0]
                            self.rect.move_ip(-diff_in_x_coord + 1, 0)
                            self.xSpeed = 0

                    # Checking collision with bottom side of platform
                    elif i == 3:
                        self.ySpeed = 0
                        diff_in_y_coord = clipped[0][1] - self.rect.topright[1]
                        self.rect.move_ip(0, diff_in_y_coord + 2)

                    # Damage the player if they are on a spike
                    if type(obj) is Spikes:
                        if obj.spiky_side == i and self.iframes_left == 0:
                            # The top side needs to be dealt with as a special case
                            if i == 0:
                                if obj.rect.topleft[0] < self.rect.centerx < obj.rect.topright[0]:
                                    self.take_damage()
                                    pygame.time.set_timer(self.invulnerable_event, 125, 16)
                            else:
                                self.take_damage()
                                pygame.time.set_timer(self.invulnerable_event, 125, 16)

            # See if the player is colliding with a moving platform
            if obj in all_moving_platforms:
                # Check if player is 1 or 2 pixels above platform
                if self.rect.colliderect(obj.movement_rect):
                    self.rect.move_ip(obj.velocity)


        # This is the collision detection algorithm for the player with semi-solid platforms
        for obj in all_semi_solid_platforms:
            clipped = self.rect.clipline(obj.top_side)
            # If there is a collision
            if clipped:
                # Check if the player was above the platform on the previous frame
                if self.rect.bottomleft[1] - self.ySpeed <= obj.top_side[0][1]:
                    self.rect.y += obj.top_side[0][1] - self.rect.bottomleft[1]
                    self.isGrounded = True
                    self.ySpeed = 0

class Enemy(MySprite):
    def __init__(self, size: tuple, colour, initialPos=(0, 0)):
        super().__init__(size, colour, initialPos)
        self.horizontal_speed = 1
        self.VERTICAL_SPEED = 0


class Platform(MySprite):
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

class Fool(Enemy):
    """
    This class is for the enemy called Fools.
    They are simple enemies: they will continue in 1 direction until they fall off a platform or bump into a wall
    They will also NOT target the player but will damage the player if the player walks into them
    If the player jumps on them (the bottom left of the player is above their centre), they will be squished
    """
    def __init__(self, initialPos):
        super().__init__((20, 20), (255, 0, 0), initialPos)
        self.horizontal_speed = -2  # It will always start by going left
        self.MAX_VERTICAL_SPEED = 7.5  # Allows Fool to accelerate downwards (not necessary for all enemies)
        self.internal_timer = 0  # Used for squishing animation
        self.vertical_speed = 0
        self.isBeingSquished = False


    def become_squished(self) -> None:
        """
        This function is to be used iteratively (i.e. multiple times)
        """
        self.image = pygame.transform.scale(self.image, (1, 0.5))
        self.rect.height /= 2
        if self.rect.height < 1:
            # Once the enemy is "dead", it is removed from all the groups
            self.kill()

    def collide_with_platforms(self, all_platforms, all_semi_solid_platforms, all_moving_platforms):
        """
        This function resolves collisions between the player and ordinary platforms
        and does not include interactions between the enemy and the player.
        This function helps to simplify the game loop code in Fool.update()
        :param all_platforms: The list that all platforms are in
        :param all_semi_solid_platforms: The list all semi_solid platforms are in
        """
        # Check if the enemy is falling
        all_platform_rects = [obj.rect for obj in (all_platforms + all_semi_solid_platforms)]
        colliding_platform_indices = self.rect.collidelistall(all_platform_rects)

        if len(colliding_platform_indices) == 0:
            self.vertical_speed += 0.3
            if self.vertical_speed > self.MAX_VERTICAL_SPEED:
                self.vertical_speed = self.MAX_VERTICAL_SPEED

        # Then check if the enemy is walking into a wall
        # If the enemy is in collision with ANYTHING
        else:
            # This is a near identical version of the player collision testing
            for index in colliding_platform_indices:
                currentPlatform = all_platform_rects[index]

                # Top, left, right (bottom not required since Fools can't jump)
                platform_lines = [
                    (currentPlatform.topleft, currentPlatform.topright),
                    (currentPlatform.topleft, currentPlatform.bottomleft),
                    (currentPlatform.topright, currentPlatform.bottomright)

                ]

                for i in [0, 1, 2]:
                    temp_clipped = self.rect.clipline(platform_lines[i])

                    if temp_clipped:
                        # Checking collision with top side of platform (the floor for the player)
                        if i == 0:
                            # Only stops the player if they are falling onto the platform
                            self.vertical_speed = 0
                            diff_in_y_coord = self.rect.bottomright[1] - temp_clipped[0][1]
                            self.rect.move_ip(0, -diff_in_y_coord)

                        # Checking collision with left side of platform
                        # If the player is resting on the corner of the platform,
                        #   we want to ignore the collision with the left and right sides
                        elif i == 1:
                            if self.rect.bottomleft[1] - 1 > currentPlatform.topleft[1]:
                                diff_in_x_coord = self.rect.topright[0] - temp_clipped[0][0]
                                self.rect.move_ip(-diff_in_x_coord - 1, 0)
                                self.horizontal_speed = -2


                        # Checking collision with right side of platform
                        elif i == 2:
                            if self.rect.bottomright[1] - 1 > currentPlatform.topright[1]:
                                diff_in_x_coord = self.rect.topleft[0] - temp_clipped[0][0]
                                self.rect.move_ip(-diff_in_x_coord - 1, 0)
                                self.horizontal_speed = 2

                # See if the enemy is colliding with a moving platform
                if currentPlatform in all_moving_platforms:
                    # Check if enemy is 1 or 2 pixels above platform
                    if self.rect.colliderect(currentPlatform.movement_rect):
                        self.rect.move_ip(currentPlatform.velocity)

    def update(self, all_platforms, all_semi_solid_platforms, all_moving_platforms) -> None:
        """
        This is a simple function that contains the main logic of the Fool
        but does not include interactions with the player (that's in main.py)
        """
        self.rect.move_ip(self.horizontal_speed, self.vertical_speed)
        self.collide_with_platforms(all_platforms, all_semi_solid_platforms, all_moving_platforms)

class GhostPursuer(Enemy):
    """
    This class consists of an enemy that can travel through walls and platforms.
    They will always pursue the player but very slowly.
    They do not interact with other enemies.
    When they damage the player, they disappear
    """
    def __init__(self, initialPos):
        # The ghost starts fully transparent
        GHOST_RADIUS = 10
        super().__init__((20, 20), (0, 0, 0, 255), initialPos)
        pygame.draw.circle(self.image, (255, 0, 0, 50), (GHOST_RADIUS, GHOST_RADIUS), GHOST_RADIUS)
        self.collision_rect = self.rect.copy()
        self.collision_rect.scale_by_ip(0.8, 0.8)

    def update(self, player_position: tuple):
        # Calculate difference between x and difference between y
        diff_in_x = player_position[0] - self.rect.centerx
        diff_in_y = player_position[1] - self.rect.centery
        translation = pygame.Vector2()

        translation.x = diff_in_x // 20
        if 1 < diff_in_x < 20:
            translation.x = 1
        elif -1 > diff_in_x > -20:
            translation.x = -1

        translation.y = diff_in_y // 20
        if 1 < diff_in_y < 20:
            translation.y = 1
        elif -1 > diff_in_y > -20:
            translation.y = -1

        self.rect.move_ip(translation)
        self.collision_rect.move_ip(translation)

class JumpingFool(Enemy):
    def __init__(self, initialPos):
        super().__init__((20,20), (255, 0, 0), initialPos)
        self.vertical_speed = 0
        self.isBeingSquished = False  # Might add squishing later or remove it entirely
        self.x_speed = 0
        self.MAX_VERTICAL_SPEED = 10

    def collide_with_platforms(self, all_platforms, all_semi_solid_platforms, all_moving_platforms):
        """
        This function resolves collisions between the enemy and platforms
        and does not include interactions between the enemy and the player.
        This function helps to simplify the game loop code in JumpingFool.update()
        :param all_platforms: The list that all platforms are in
        :param all_semi_solid_platforms: The list all semi_solid platforms are in
        """
        # Check if the enemy is falling
        all_platform_rects = [obj.rect for obj in (all_platforms + all_semi_solid_platforms)]
        colliding_platform_indices = self.rect.collidelistall(all_platform_rects)

        if len(colliding_platform_indices) == 0:
            self.vertical_speed += 0.3
            if self.vertical_speed > self.MAX_VERTICAL_SPEED:
                self.vertical_speed = self.MAX_VERTICAL_SPEED

        # Then check if the enemy is walking into a wall
        # If the enemy is in collision with ANYTHING
        else:
            # This is a near identical version of the player collision testing
            for index in colliding_platform_indices:
                currentPlatform = all_platform_rects[index]

                # Top, left, right and bottom
                platform_lines = [
                    (currentPlatform.topleft, currentPlatform.topright),
                    (currentPlatform.topleft, currentPlatform.bottomleft),
                    (currentPlatform.topright, currentPlatform.bottomright),
                    (currentPlatform.bottomright, currentPlatform.bottomleft)
                ]

                for i in [0, 1, 2, 3]:
                    temp_clipped = self.rect.clipline(platform_lines[i])

                    if temp_clipped:
                        # Checking collision with top side of platform (the floor for the enemy)
                        if i == 0:
                            # Stops the enemy if they are falling onto the platform
                            self.vertical_speed = 0
                            diff_in_y_coord = self.rect.bottomright[1] - temp_clipped[0][1]
                            self.rect.move_ip(0, -diff_in_y_coord)

                            # Initiate jump again
                            self.vertical_speed = -8

                        # Checking collision with left side of platform
                        # If the player is resting on the corner of the platform,
                        #   we want to ignore the collision with the left and right sides
                        elif i == 1:
                            if self.rect.bottomleft[1] - 1 > currentPlatform.topleft[1]:
                                diff_in_x_coord = self.rect.topright[0] - temp_clipped[0][0]
                                self.rect.move_ip(-diff_in_x_coord - 1, 0)
                                self.horizontal_speed = -2


                        # Checking collision with right side of platform
                        elif i == 2:
                            if self.rect.bottomright[1] - 1 > currentPlatform.topright[1]:
                                diff_in_x_coord = self.rect.topleft[0] - temp_clipped[0][0]
                                self.rect.move_ip(-diff_in_x_coord - 1, 0)
                                self.horizontal_speed = 2

                        # Checking collision with bottom side of platform
                        elif i == 3:
                            self.vertical_speed = 0
                            diff_in_y_coord = temp_clipped[0][1] - self.rect.topright[1]
                            self.rect.move_ip(0, diff_in_y_coord + 2)

                # See if the enemy is colliding with a moving platform
                if currentPlatform in all_moving_platforms:
                    # Check if enemy is 1 or 2 pixels above platform
                    if self.rect.colliderect(all_platforms[index].movement_rect):
                        self.rect.move_ip(all_platforms[index].velocity)

    def update(self, all_platforms, all_semi_solid_platforms, all_moving_platforms):
        self.rect.move_ip(self.horizontal_speed, self.vertical_speed)
        self.collide_with_platforms(all_platforms, all_semi_solid_platforms, all_moving_platforms)


class Spikes(Platform):
    """
    This is a stationary enemy that is a literally just a platform that damages the player
    Spikes are drawn in triangles. Each triangle will have a fixed width of 10
    """
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
    def __init__(self, size, position):
        super().__init__(size, (255, 0, 255), position)
        self.top_side = (self.rect.topleft, self.rect.topright)


class MovingPlatform(Platform):
    def __init__(self, size, colour, start_point: tuple[int, int], end_point: tuple[int, int]):
        super().__init__(size, colour, start_point)
        self.rect.center = start_point
        self.set_sides()

        # The below field is used to ensure the player moves with the platform
        # It is 1 pixel above the actual platform and only 1 pixel thick
        self.movement_rect = self.rect.copy()
        self.movement_rect.height = 1
        self.movement_rect.width -= 2
        self.movement_rect.topleft = (self.rect.left + 1, self.rect.top - 1)

        self.internal_timer = 0
        self.path = (start_point, end_point)
        self.dest = 0
        self.velocity = pygame.Vector2()

    def update(self, clock: pygame.time.Clock):
        # Check if the platform has arrived at its destination
        if self.rect.center == self.path[self.dest]:
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
                if self.rect.centerx < self.path[self.dest][0]:
                    self.velocity.x = 1

                elif self.rect.centerx == self.path[self.dest][0]:
                    self.velocity.x = 0

                else:
                    self.velocity.x = -1

                if self.rect.centery < self.path[self.dest][1]:
                    self.velocity.y = 1

                elif self.rect.centery == self.path[self.dest][1]:
                    self.velocity.y = 0

                else:
                    self.velocity.y = -1

        # If the platform needs to get moving
        else:
            self.rect.move_ip(self.velocity)
            self.movement_rect.move_ip(self.velocity)
            self.set_sides()
