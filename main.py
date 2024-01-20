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
player = Player((32, 32), BLUE, player_is_invulnerable, (40, 200))
platform = Platform((408, 200), GREEN, (-4, 300))
wall = Platform((30, SCREENHEIGHT), GREEN, (0, 0))
wall2 = Platform((30, SCREENHEIGHT), GREEN, (SCREENWIDTH-10, 0))
platform3 = MovingPlatform((80, 15), GREEN, (210, 210), (300, 210))
platform4 = SemiSolidPlatform((80, 10), (60, 210))

spikes = Spikes(8, 20, (150, 100), 0)

fool1 = JumpingFool((180, 101))
pursuer1 = GhostPursuer((10, 90))
all_enemies = pygame.sprite.Group()
all_enemies.add(pursuer1, fool1)

respawn_point = (60, 100)

playerHealthIcon = pygame.transform.scale(player.image, (15, 15))

clock = pygame.time.Clock()

game_is_running = True
level1 = GameLevel("level.gdt")

all_platforms = level1.all_platforms
all_semi_solid_platforms = level1.all_semi_solid_platforms
all_enemies = level1.all_enemies

def enemy_logic():
    for enemy in all_enemies:
        if type(enemy) is Fool or type(enemy) is JumpingFool:
            # Logic for fools - check the fool class
            if not enemy.isBeingSquished:
                enemy.update(all_platforms, all_semi_solid_platforms)

                # Check for collision with player
                if enemy.rect.colliderect(player.rect):
                    # Now check for where player position is relative to enemy
                    # If the player is above the enemy's centre
                    if player.rect.bottomleft[1] <= enemy.rect.centery and player.ySpeed > 0:
                        enemy.isBeingSquished = True
                        player.ySpeed = -5
                        if type(enemy) is JumpingFool:
                            enemy.kill()

                    elif player.iframes_left == 0:
                        player.take_damage()

            else:
                if type(enemy) is Fool:
                    enemy.internal_timer += clock.get_time()
                    if enemy.internal_timer >= 20:
                        enemy.become_squished()
                        enemy.internal_timer = 0

        if type(enemy) is GhostPursuer:
            enemy.update(player.rect.center)
            if player.rect.colliderect(enemy.collision_rect) and player.iframes_left == 0:
                player.take_damage()
                enemy.kill()

def display_graphics():
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
                pygame.display.toggle_fullscreen()


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
        player.decelerate()

    if keys[pygame.K_SPACE]:
        player.jump(highJump=pygame.key.get_mods() & KMOD_SHIFT)


    # Prevents the player moving off-screen
    if player.rect.x > SCREENWIDTH - player.rect.width:
        player.float_pos.x = SCREENWIDTH - player.rect.width
        player.xSpeed = 0
    elif player.rect.x < 0:
        player.float_pos.x = 0
        player.xSpeed = 0

    # Respawn player
    if player.rect.y > SCREENHEIGHT:
        player.rect.topleft = respawn_point
        player.float_pos.x = player.rect.centerx
        player.float_pos.y = player.rect.centery
        player.take_damage()


    if player.isSpinning:
        player.ground_pound(clock)


    player.float_pos.x += player.xSpeed
    player.float_pos.y += player.ySpeed
    player.rect.x = round(player.float_pos.x)
    player.rect.y = round(player.float_pos.y)

    #### Enemy logic ####
    enemy_logic()

    #### Collision detection ####
    player.collision_update(all_platforms, all_semi_solid_platforms)

    for obj in all_platforms:
        if type(obj) is MovingPlatform:
            obj.update(clock)

    display_graphics()

    # Update the screen
    pygame.display.flip()
    clock.tick(FPS)

# If the game is stopped
pygame.quit()
sys.exit()
