from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites

from random import randint, choice

# main class which handles game init, loops and logic
class Game:
    def __init__(self):
        # setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # gun timer
        self.can_shoot = True
        self.shoot_time = 0 
        self.gun_cooldown = 300

        # enemy respawn rate 
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
        self.spawn_positions = []
        
        # audio 
        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        self.music = pygame.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.5)
        # self.music.play(loops = -1)

        # setup
        self.load_images()
        self.setup()

        # Load title screen assets
        self.title_background = pygame.image.load(join('images', 'title_background.png')).convert()

        # Counter for killed enemies
        self.killed_enemies = 0 

    # loads images for bullets and enemies from specific directories
    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'gun', 'bullet.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    # handles player input for shooting bullets
    def input(self):
        # checks if the mouse button is pressed so player can shoot
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    # manages the cooldown for shooting
    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    # resets game state for every new game, loads the game map .tmx file
    def setup(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.enemy_sprites.empty()

        map = load_pygame(join('data', 'maps', 'world.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))

    # checks for collisions between bullets and enemies
    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                        self.killed_enemies += 1  # Increment the killed enemies counter
                        if self.killed_enemies > 50:
                            self.game_finished()
                    bullet.kill()

    # checks for collisions between the player and enemies
    def player_collision(self):
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.player.take_damage(10)  # Adjust the damage amount as needed
        if self.player.health <= 0:
            self.game_over()

    # displays the title screen before starting the game
    def title_screen(self):
        title_font = pygame.font.Font(None, 74)
        instruction_font = pygame.font.Font(None, 36)
        title_surface = title_font.render('Survivor', True, 'white')
        instruction_surface = instruction_font.render('Press any key to start', True, 'white')

        while True:
            # Draw the background
            self.display_surface.blit(self.title_background, (0, 0))

            # Draw the title and instructions
            self.display_surface.blit(title_surface, (WINDOW_WIDTH // 2 - title_surface.get_width() // 2, WINDOW_HEIGHT // 2 - title_surface.get_height() // 2))
            self.display_surface.blit(instruction_surface, (WINDOW_WIDTH // 2 - instruction_surface.get_width() // 2, WINDOW_HEIGHT // 2 + 20))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return  # Start the game

    # displays the game over screen when player loses
    def game_over(self):
        font = pygame.font.Font(None, 74)
        text_surface = font.render('Game Over', True, 'white')
        instruction_surface = font.render('Press R to Respawn or Q to Quit', True, 'white')

        while True:
            self.display_surface.fill('black')
            self.display_surface.blit(text_surface, (WINDOW_WIDTH // 2 - text_surface.get_width() // 2, WINDOW_HEIGHT // 2 - text_surface.get_height() // 2))
            self.display_surface.blit(instruction_surface, (WINDOW_WIDTH // 2 - instruction_surface.get_width() // 2, WINDOW_HEIGHT // 2 + 50))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Press R to restart
                        self.setup()  # Reset the game state
                        return  # Exit the game over loop
                    if event.key == pygame.K_q:  # Press Q to quit
                        pygame.quit()
                        return  # Exit the game

    # displays a screen when the player finishes the game after killing the required amount of enemies          
    def game_finished(self):
        font = pygame.font.Font(None, 74)
        text_surface = font.render('Game Finished!', True, 'white')
        instruction_surface = font.render('Press R to Restart or Q to Quit', True, 'white')

        while True:
            self.display_surface.fill('black')
            self.display_surface.blit(text_surface, (WINDOW_WIDTH // 2 - text_surface.get_width() // 2, WINDOW_HEIGHT // 2 - text_surface.get_height() // 2))
            self.display_surface.blit(instruction_surface, (WINDOW_WIDTH // 2 - instruction_surface.get_width() // 2, WINDOW_HEIGHT // 2 + 50))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Press R to restart
                        self.killed_enemies = 0  # Reset the killed enemies counter
                        self.setup()  # Reset the game state
                        return  # Exit the game finished loop
                    if event.key == pygame.K_q:  # Press Q to quit
                        pygame.quit()
                        return  # Exit the game

    def draw_health_bar(self):
        # Define health bar dimensions
        bar_width = 400  # Width of the health bar
        bar_height = 20  # Height of the health bar
        outline_thickness = 2  # Thickness of the outline

        # Calculate the width of the health fill based on current health
        fill_width = (self.player.health / 1000) * bar_width 

        # Define positions
        bar_x = 10  # X position of the health bar
        bar_y = 10  # Y position of the health bar

        # Draw the outline of the health bar (black)
        pygame.draw.rect(self.display_surface, (0, 0, 0), (bar_x - outline_thickness, bar_y - outline_thickness, bar_width + outline_thickness * 2, bar_height + outline_thickness * 2))  # Black outline

        # Draw the filled portion of the health bar (red for health)
        pygame.draw.rect(self.display_surface, (255, 0, 0), (bar_x, bar_y, fill_width, bar_height))  # Red fill for health

    # displays the kill counter
    def draw_killed_enemies_counter(self):
        font = pygame.font.Font(None, 36)  # Font for the counter
        text_surface = font.render(f'Enemies Killed: {self.killed_enemies}/50', True, 'white')
        self.display_surface.blit(text_surface, (10, 50))

    # the main game loop which runs the game
    def run(self):
        self.title_screen()
        while self.running:
            # dt 
            dt = self.clock.tick() / 1000

            # event loop 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event:
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

            # update 
            self.gun_timer()
            self.input()
            self.all_sprites.update(dt)
            self.bullet_collision()
            self.player_collision()

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            self.draw_health_bar()
            self.draw_killed_enemies_counter()
            pygame.display.update()

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()