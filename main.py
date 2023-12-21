import sys
from pygame.constants import *
from gameClasses import *

pygame.init()
SCREENWIDTH = 400
SCREENHEIGHT = 400
FPS = 60

# Define some colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Set up the main screen as well as the caption
screen: pygame.Surface = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption("Game")

# Set up game stuff here
player_is_invulnerable = pygame.USEREVENT + 1
player = Player((32, 32), BLUE, player_is_invulnerable, (0, 200))
platform = Platform((408, 200), GREEN, (-4, 300))
# platform2 = MySprite((80, 10), GREEN, initialPos=(150, 100))
platform3 = MovingPlatform((80, 15), GREEN, (210, 210), (300, 210))
platform4 = SemiSolidPlatform((80, 10), (60, 210))

spikes = Spikes(8, 20, (150, 100), 0)

fool1 = Fool((200, 0))
all_enemies = pygame.sprite.Group()
all_enemies.add(fool1)

playerHealthIcon = pygame.transform.scale(player.image, (15, 15))

# Using lists for all_platforms in order to avoid having to create MULTIPLE variables
all_platforms = [platform, spikes, platform3]
all_semi_solid_platforms = [platform4]
all_moving_platforms = [platform3]

clock = pygame.time.Clock()

game_is_running = True

#### Main game logic ####
while game_is_running:
    # Event stuff
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT or player.health <= 0:
            game_is_running = False

        elif event.type == player_is_invulnerable:
            player.iframes_left -= 1
            player.is_invisible = not player.is_invisible

        elif event.type == KEYDOWN:
            if event.key == K_c:
                if not player.isGrounded and not player.isSpinning and player.canGroundPound:
                    player.isSpinning = True
                    player.rotate(3.6)
            elif event.key == K_0:
                pass
                # FPS = 61 - FPS


    #### Player controls ####
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        if not player.isGrounded:
            player.xSpeed -= 0.2
        else:
            player.xSpeed -= 1

        # We do not want to accelerate past our max speed
        if player.xSpeed < -1 * player.max_horizontal_speed:
            player.xSpeed = -player.max_horizontal_speed

    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        if not player.isGrounded:
            player.xSpeed += 0.2
        else:
            player.xSpeed += 1

        if player.xSpeed > player.max_horizontal_speed:
            player.xSpeed = player.max_horizontal_speed

    # If neither the left/A nor the right/D key is pressed
    else:
        if player.xSpeed > 0:
            if player.isGrounded:
                player.xSpeed -= 0.32  # It takes a little while to fully decelerate
            else:
                player.xSpeed -= 0.1

            if player.xSpeed < 0:
                player.xSpeed = 0

        elif player.xSpeed < 0:
            if player.isGrounded:
                player.xSpeed += 0.32
            else:
                player.xSpeed += 0.1

            if player.xSpeed > 0:
                player.xSpeed = 0

    if keys[pygame.K_SPACE]:
        if player.isGrounded:
            if pygame.key.get_mods() & KMOD_SHIFT:
                player.max_vertical_speed = 10
            else:
                player.max_vertical_speed = 7.5

            player.ySpeed = -1 * player.max_vertical_speed
            player.isGrounded = False


    # Prevents the player moving off-screen
    if player.rect.x > SCREENWIDTH - player.rect.width:
        player.rect.x = SCREENWIDTH - player.rect.width
        player.xSpeed = 0
    elif player.rect.x < 0:
        player.rect.x = 0
        player.xSpeed = 0

    if player.rect.y > SCREENHEIGHT:
        player.rect.y = SCREENHEIGHT
        player.ySpeed = 0

    if player.isSpinning:
        player.xSpeed = 0
        player.ySpeed = 0

        if player.orientation < 360:
            player.internalTimer += clock.get_time()
            if player.internalTimer > 0.02:
                player.rotate(18)
        else:
            player.isSpinning = False
            player.orientation = 0
            player.image = player.orig_image
            player.rect = player.image.get_rect(center=player.rect.center)
            player.canGroundPound = False
            player.ySpeed = 8
            player.max_vertical_speed = 12


    player.rect.move_ip(player.xSpeed, player.ySpeed)

    #### Enemy logic ####
    for enemy in all_enemies:
        if type(enemy) is Fool:
            # Logic for fools - check the fool class
            if not enemy.isBeingSquished:
                enemy.update(all_platforms, all_semi_solid_platforms)

                # Check for collision with player
                if enemy.rect.colliderect(player.rect):
                    # Now check for where player position is relative to enemy
                    # If the player is above the enemy's centre
                    if player.rect.bottomleft[1] <= enemy.rect.centery and player.ySpeed > 0:
                        enemy.isBeingSquished = True

                    elif player.iframes_left == 0:
                        player.take_damage()

            else:
                enemy.internal_timer += clock.get_time()
                if enemy.internal_timer >= 0.15:
                    enemy.become_squished()
                    enemy.internal_timer = 0


    #### Collision detection ####
    player.collision_update(all_platforms, all_semi_solid_platforms, all_moving_platforms)

    for obj in all_moving_platforms:
        obj.update(clock)



    ##### Drawing stuff #####
    # First clear the canvas
    screen.fill("0xFFFFFF")

    # Now draw all the platforms
    for obj in all_platforms + all_semi_solid_platforms:
        obj.draw(screen)

    # And all the enemies
    for enemy in all_enemies:
        enemy.draw(screen)

    for i in range(player.health):
        screen.blit(playerHealthIcon, (30 + i*30, 10))

    # And the player
    player.draw(screen)

    # Update the screen
    pygame.display.flip()
    clock.tick(FPS)

# If the game is stopped
pygame.quit()
sys.exit()
