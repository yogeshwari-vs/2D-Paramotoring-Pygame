import os
import pygame
import time

import global_config
from module import background_module
from module import bird_module
from module import coins_module
from module import display_module
from module import effects_module
from module import event_module
from module import foreground_module
from module import interface_module
from module import music_module
from module import obstacles_module
from module import player_module


# Global variables

speed = global_config.speed
game_duration = global_config.game_duration
run = True

frame_count = 0
num_of_lives = 3

win = None

def create_game_window():
	global win	
	win = pygame.display.set_mode((global_config.window_width, global_config.window_height))
	pygame.display.set_caption('Game Window')

def change_img_pixel_format():
	"""
	Creates a new copy of the Surface which will have the same pixel format as
	the display Surface. Necessary for blitting images to the screen faster.
	"""
	background_module.bg = background_module.bg.convert()

	foreground_module.ground = foreground_module.ground.convert_alpha()
	
	player_module.Player.imgs = [img.convert_alpha() for img in player_module.player.imgs]
	player_module.Propeller.propeller_imgs = [img.convert_alpha() for img in player_module.Propeller.propeller_imgs]

	coins_module.Coin.resized_imgs = [img.convert_alpha() for img in coins_module.Coin.resized_imgs]
	coins_module.coin_board = coins_module.coin_board.convert_alpha()

	obstacles_module.Tree.resized_imgs = [img.convert_alpha() for img in obstacles_module.Tree.imgs]
	obstacles_module.Rock_n_Bush.resized_imgs = [img.convert_alpha() for img in obstacles_module.Rock_n_Bush.resized_imgs]	

	effects_module.Coin_spark_effects.imgs = [img.convert_alpha() for img in effects_module.Coin_spark_effects.imgs]
	effects_module.Hit_effects.imgs = [img.convert_alpha() for img in effects_module.Hit_effects.imgs]

	display_module.heart = display_module.heart.convert_alpha()
	display_module.line = display_module.line.convert_alpha()
	display_module.start = display_module.start.convert_alpha()
	display_module.finish = display_module.finish.convert_alpha()
	
	bird_module.Bird.list_of_lists = [[img.convert_alpha() for img in lst] for lst in bird_module.Bird.list_of_lists]

def draw_all_objects():
	"""
	Draws the background, foreground, obstacles, coins, special effects, player, bird, lives, minimap.
	"""
	background_module.draw_bg(win)
	obstacles_module.draw_obstacles(win)
	coins_module.draw_coins(win)
	foreground_module.draw_fg(win)

	for spark_object in effects_module.Coin_spark_effects.coin_effects_list:
		spark_object.draw(win)
	for hit_effect_object in effects_module.Hit_effects.hit_effects_list:
		hit_effect_object.draw(win)

	player_module.draw_player(win)
	bird_module.draw_bird(win)
	display_module.display_lives(win, num_of_lives)
	display_module.draw_minimap(win,frame_count)


# MAIN ALGORITHM
if __name__ == '__main__':

	pygame.init()

	# Home screen interface window
	volume_button_on_status = interface_module.display_buttons()

	# Game window
	create_game_window()

	change_img_pixel_format()

	clock = pygame.time.Clock()
	event_module.setting_up_events()
	
	#Music Variable
	Music_Background = pygame.mixer.music.load(os.path.join('Utils\Music\BGmusic_Level1.wav'))
	if volume_button_on_status:
		pygame.mixer.music.play(-1)

	# GAME LOOP
	while run:
		frame_count += 1

		draw_all_objects()
		event_module.event_loop()

		# Coin collection
		collected = coins_module.coin_collection(player_module.player)	# Returns bool 
		if collected:
			if volume_button_on_status:
				music_module.sound_coins.play()
			coins_module.Coin.num_coins_collected += 1
		coins_module.display_num_coins_collected(win)

		# Collision with Obstacles
		collision_with_obstacle = obstacles_module.collision_with_obstacle()	# Checks collision and Returns bool 
		collision_with_bird = bird_module.collision_with_bird()
		if collision_with_obstacle or collision_with_bird:		# Dummy exit
			if volume_button_on_status:
				music_module.sound_collided.play()
			num_of_lives -= 1
			if num_of_lives == 0:	# If all 3 lives are gone 
				time.sleep(1)
				break

		clock.tick(speed)
		pygame.display.update()
		
		# Dummy exit
		if frame_count >= game_duration*speed:
			print('Game Over')
			time.sleep(1)
			break
