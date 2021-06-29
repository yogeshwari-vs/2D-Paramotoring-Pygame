import os
import queue
import pygame
import random
import time
import multiprocessing
from multiprocessing import freeze_support


import global_config
from module import background_module
from module import bird_module
from module import coins_module
from module import display_module
from module import effects_module
# from module import ending_module
from module import event_module
from module import foreground_module
from module import interface_module

# from module import interface_screens_module
from module import music_module
from module import obstacles_module
from module import player_module

from mp import process_object
from module.interface_screens_module import check_index
from module.interface_screens_module import display_no_hand_info
from mp import queue_shared
from module.player_movement_box import draw_control_screen_actual, draw_player_position


# Global variables
run = True

frame_count = 0
num_of_lives = 3
fuel_count = 0
ending_count = 0

fuel_available = global_config.speed*60
start_fuel = False

display_pop_up = False

win = None
game_window = None

def create_game_window():
	global win, game_window
	
	# Game Window
	game_window = pygame.display.set_mode((global_config.window_width, global_config.window_height), pygame.RESIZABLE)
	pygame.display.set_caption('Game Window')
	
	# Copy of game window which will be later resized according to the resolution, and blit onto the original game window.
	win = game_window.copy()

total_num_of_frames = global_config.speed*global_config.game_duration
	

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
	obstacles_module.Rock_n_Bush.imgs = [img.convert_alpha() for img in obstacles_module.Rock_n_Bush.imgs]	

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
	global fuel_available

	background_module.draw_bg(win)
	obstacles_module.draw_obstacles(win)
	coins_module.draw_coins(win)
	foreground_module.draw_fg(win)

	for spark_object in effects_module.Coin_spark_effects.coin_effects_list:
		spark_object.draw(win)
	for hit_effect_object in effects_module.Hit_effects.hit_effects_list:
		hit_effect_object.draw(win)

	if num_of_lives == 0:
		player_module.player.y += 1
		Music_Background = pygame.mixer.music.load(os.path.join('Utils\Music\BGmusic_Level1.wav'))


		pygame.mixer.music.stop()
		music_module.sound_aftercollided.play()
		player_module.propeller.draw(win)
		player_module.player.draw(win)
	else:
		player_module.draw_player(win)
		

	bird_module.draw_bird(win)
	display_module.display_lives(win, num_of_lives)
	display_module.draw_minimap(win,frame_count)

	if start_fuel:
		fuel_available -= 1
	fuel_available = display_module.fuel_bar.draw_fuel_bar(win, fuel_available, start_fuel)

	display_module.draw_fuel(win)
	cursor.draw(win)

def lost():
	"""
	The player falls if all three lives are lost
	"""
	pygame.event.set_blocked(pygame.USEREVENT+1)
	foreground_module.foreground_speed = 0
	background_module.background_speed = 0
	if player_module.player.y > foreground_module.ground_y:
		try:
			process_object.terminate()
		except: pass
		time.sleep(1)
		interface_module.display_endscreen()
		return True
	return False

# MAIN ALGORITHM
if __name__ == '__main__':
	freeze_support()

	pygame.init()

	# Home screen interface window
	volume_button_on_status = interface_module.display_homescreen()

	# Game window
	create_game_window()

	change_img_pixel_format()

	clock = pygame.time.Clock()
	event_module.setting_up_events()
	cursor = interface_module.Cursor()
	pygame.mouse.set_visible(False)
	
	#Music Variable
	Music_Background = pygame.mixer.music.load(os.path.join('Utils\Music\BGmusic_Level1.wav'))
	if volume_button_on_status:
		pygame.mixer.music.play(-1)

	# GAME LOOP
	while run:
		frame_count += 1
		
		draw_all_objects()
		

		if frame_count < 4*global_config.speed:
			display_module.countdown.draw(win)
		elif frame_count == 4*global_config.speed:
			pygame.event.set_allowed(pygame.USEREVENT+1)
			start_fuel = True
		
		event_module.event_loop()

		# Coin collection
		collected = coins_module.coin_collection(player_module.player)	# Returns bool 
		if collected:
			if volume_button_on_status:
				music_module.sound_coins.play()
			coins_module.Coin.num_coins_collected += 1
		coins_module.display_num_coins_collected(win)

		# Extra life

		num_of_coins_inexchange_for_life = 50
		if coins_module.Coin.num_coins_collected%num_of_coins_inexchange_for_life == 0 and num_of_lives!=3:
			extra_life = display_module.Extra_life()
		elif coins_module.Coin.num_coins_collected > num_of_coins_inexchange_for_life:
			try:
				extra_life.draw(win)
				player = player_module.player
				if extra_life.x < (player.x + player.img.get_width()) and (extra_life.x + extra_life.img.get_width()) > player.x:	# Check x range
					if extra_life.y < (player.y + player.img.get_height()) and (extra_life.y + extra_life.img.get_height()) > player.y:	# Check y range
						bool = extra_life.check_collision()
						if bool:
							# num = random.randint(1,1000)
							# print('collected life', num)
							del extra_life
							num_of_lives += 1
							coins_module.Coin.num_coins_collected -= num_of_coins_inexchange_for_life
			except:
				pass
		
		draw_control_screen_actual(win)

		
		#print("success")
		draw_player_position(win)		     # draws black screen
		try:
			bool_val = check_index(queue_shared)
			if bool_val:
				display_pop_up = True
				start_loop = 0


			if display_pop_up:
				# print('inside if')
				start_loop += 1
				# print('displaying')
				display_no_hand_info(win)
				if start_loop >= global_config.speed:
					display_pop_up = False
		except:
			pass

		

		# Collision with Obstacles
		collision_with_obstacle = obstacles_module.collision_with_obstacle()	# Checks collision and Returns bool 
		collision_with_bird = bird_module.collision_with_bird()
		if collision_with_obstacle or collision_with_bird:		# Dummy exit
			if volume_button_on_status:
				music_module.sound_collided.play()
			num_of_lives -= 1
			if num_of_lives <= 0:
				num_of_lives = 0
		
		if num_of_lives == 0:	# If all 3 lives are gone
			game_end = lost()
			player_module.propeller.frames_per_propeller_img += 0.01
			if game_end:
				break

		display_module.pause_play_button.check_status(cursor, win)

		# Resize and blit the copy of game window onto main game window
		game_window.blit(pygame.transform.scale(win, game_window.get_rect().size), (0,0))

		clock.tick(global_config.speed)
		pygame.display.update()

		# Dummy exit
		if frame_count >= total_num_of_frames:
			print('Game Over')
			time.sleep(1)
			break

