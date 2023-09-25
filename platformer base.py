#Game Set Up
import os
import random
import math
from typing import Self
import pygame
from os import listdir
from os.path import isfile, join #helps you dynamically load things instead of typing out every file directory
pygame.init() #initializes gaame

pygame.display.set_caption("Platformer") #changes the title at the top of window

# BG_COLOR = (255, 255, 255)  #colors in pygame will always be RGB we can get rid of this because we are using the tiles as backgrounds
WIDTH, HEIGHT = 1000, 800  #this is a good width/height for 2k monitors

FPS = 60
PLAYER_VEL = 5 #speed of character


window = pygame.display.set_mode((WIDTH, HEIGHT)) #defining window varaible

def draw_health_bar(surf, pos, size, borderC, backC, healthC, progress):
    pygame.draw.rect(surf, backC, (*pos, *size))
    pygame.draw.rect(surf, borderC, (*pos, *size), 1)
    innerPos  = (pos[0]+1, pos[1]+1)
    innerSize = ((size[0]-2) * progress, size[1]-2)
    rect = (round(innerPos[0]), round(innerPos[1]), round(innerSize[0]), round(innerSize[1]))
    pygame.draw.rect(surf, healthC, rect)


#we need sprites (images) to have collision (pixel-perfect)
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites] #True here means flip in xdirection, this false is telling us to not flip in the Y direction

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))] 

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()  #load transparent background image

        sprites = []
        for i in range(sprite_sheet.get_width() // width):   #this will help us split up the images that have multiple character models in them
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)  #in position 0,0 (top left hand corner of new surface), we are drawing our sprite sheet, but only the frame we want
            sprites.append(pygame.transform.scale2x(surface))  #scaled 32x32 to 64x64

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    
    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png") 
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32) #size is the dimesion of the block
    rect = pygame.Rect(96, 0, size, size)  #image (top left of it) starts 96 pixels over in the terrain image
    surface.blit(image, (0, 0), rect) #only blit'ing at 0,0 but only the area represented by rectable
    return pygame.transform.scale2x(surface)

#from the pygame sprite class we can use a method to tell us if the sprites are colliding with each other. sprites are good for pixel-perfect collision without making things too complicated
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    PLAYER_HEALTH = 100  # starting player health
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True) #True here will make the sprites multidirectional
    ANIMATION_DELAY = 3 #accounts for the delay between changing sprites. changing sprites is important because that is what makes it look animated
    
    def __init__(self, x, y, width, height): #width and height are determined by the image we are using. this is the constructor for our player
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)  #rect is a tuple storing 4 individual values. pygame.Rect means we can use it in special equations etc
        self.x_vel = 0
        self.y_vel = 0  #we are setting the velocity that the character will move in each direction until we remove that velocity. This will be good for gravity and jumping
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8  #using negative value so we jump up in the air. changing velocity to go upwards, then letting gravity take us down
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:             #If it is the first jump we are making, we want to drop the gravity
            self.fall_count = 0    #when we jump, we reset the fall_count to 0 so we dump any gravity we have accumuluted

    
    def move(self, dx, dy):    #dx/dy means a displacement in either direction. changing the sign of each also changes direction. 
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
         
    def move_right(self, vel):
        self.x_vel = vel  #moving right adds to x coordinate. moving down adds to y coordinate
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):  #since we are making gravity realistic (accelerates over time), we need to keep track of how long we've been falling
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY) #increments by the minimum of 1, or (self.fall_count / fps) * self.GRAVITY
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2: #fps * 2 = 2 seconds
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1 #incrementing count every loop
        self.update_sprite()

    def landed(self): 
        self.fall_count = 0 #if we landed, we need to stop adding gravity. fall counter needs to get back to 0
        self.y_vel = 0      #stops moving us down
        self.jump_count = 0     #we will be including double-jumping so this will be used later.

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1    #if we hit our head, we want to reverse our velocity so we start to move down (bounce off and go downwards)
    
    def update_sprite(self):   #what sprite and when
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction  #helps us add the specific animation we want
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def set_player_health(self, augment): # the augment will be a heal (positive) or a damage (negative)
        self.PLAYER_HEALTH = self.PLAYER_HEALTH + augment

    def draw_health(self, surf): #should be drawing a health bar for us
        health_rect = pygame.Rect(0, 0, self.rect.width, 7) #this should be creating a rectangle the width of the sprite. Not sure what is needed
        health_rect.midbottom = self.rect.centerx, self.rect.top
        max_health = 100
        draw_health_bar(surf, health_rect.topleft, health_rect.size,
                        (0, 0, 0), (255, 0, 0), (0, 255, 0), self.PLAYER_HEALTH / max_health)

    def update(self):   #this method updates the rectangle that bounds are character based on the sprite we are showing
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))  #this makes sure the rect is constantly adjusted
        self.mask = pygame.mask.from_surface(self.sprite) #a mask is a mapping of all of the pixels that exist in the sprite. only part of a rectangle is filled in by the actual sprite. this map tells us where those are in the rect


    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))  #draws updated sprite on screen


class Object(pygame.sprite.Sprite):   #defines all of the properties we need for a valid sprite: rect, image, drawing the image
    def __init__(self, x, y, width, height, name=None):
        super().__init__()        #initializes "super" class
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
    
    def draw(self, win, offset_x):  #draws image for us
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image) #again. mask is necessary for collision

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")     #have to name the object so we know what object we are colliding with
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]     #self.fire is getting the animation, animation_name is "on"/"off"
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))  #have to update rect and mask for collision
        self.mask = pygame.mask.from_surface(self.image)
        
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0    #we have the animation count building earlier in the loop. We have to reset the count to prevent it building too high and causing lag. Have to divide by ANIMATION_DELAY again because we did it earlier in the loop before resetting it to 0 ~BALANCE~


#we need to create a whole grid of background tiles based on the size of the screen
#this file needs to be in the same directory as the background files to execute properly
def get_background(name):
        image = pygame.image.load(os.path.join("assets", "Background", name))         #joining assets path with background path, and then "name" is the color of the tile
        _, _, width, height = image.get_rect()            #grabs width and height. the first 2 underscores are whatever (x,y) but we dont care
        tiles = []

        for i in range(WIDTH // width + 1):           #this integer divide (WIDTH of screen // width of tile + 1) tells me approximately how many tiles I need in the x direction to fill screen
            for j in range(HEIGHT // height + 1):
                pos = (i * width, j * height)            #this is going to denote the position of the top left-hand corner of the current tile that we are adding. Instead of a list, we can make it a tuple directly which will help in the background step
                tiles.append(pos)

        return tiles, image
        
def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)      #looping through every tile we have, then we are drawing our background image at that position. blit = drawing

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)


    pygame.display.update()           #every frame we "clear" the screen so we dont have old drawings still on the string


#have to handle vertical and horizontal collision differently
def handle_vertical_collision(player, objects, dy):  #dy = displacement in y we just moved
    collided_objects = []
    for obj in objects:    #objects = all of the objects we can be colliding with
        if pygame.sprite.collide_mask(player, obj):         #this is all we need to do to determine if we are colliding with our object
            if dy > 0:
                player.rect.bottom = obj.rect.top       #if we are moving down on the screen, this places our character on top of what it is colliding with (we will collide with the top). This is problematic with horizontal collision, it will palce you on top if you collide horizontally
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom   #dy < 0 means we have negative velocity, which means we will hit the bottom the object
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects  #tells us what object we collided with - fire or another special object, for example

def collide(player, objects, dx):
    player.move(dx, 0)  #pre-emptively moves player in x direction, but not in y direction. Checking if player is hitting a block, moving left or right
    player.update() #need to update rect and mask before we check for collision
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):     #checking if they collide with something if they were to move in that direction
            collided_object = obj
            break

    player.move(-dx, 0) #moving player back to where they were
    player.update() 
    return collided_object

def handle_move(player, objects):   #objects is involved with collision
    keys = pygame.key.get_pressed()

    player.x_vel = 0   #this line here is necessary to not continuously move in one direction, only when key is pressed
    collide_left = collide(player, objects, -PLAYER_VEL * 2)    #remember sprites shift, *2 creates space between the block so there should never be a collision bug like before
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:    #checking if we should be able to move left/right (if we are not colliding)
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":        #if to_check is there because we could not be "colliding left or right" 
            player.make_hit()
            player.set_player_health(-20) #adds damage to fire collisions

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")
    
    block_size = 96
    player = Player(100, 100, 50, 50)
    player.draw_health(window) #should be drawing a health bar
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32) #HEIGHT - block_size - 64 will put us on top of a block
    fire.on()  #can turn it off later if we want
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) 
             for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)] #building the floor. this loop fills blocks to the left and right of the current screen
                    #blocks = [Block(0, HEIGHT - block_size, block_size)] *this was just a test tile, it put it in the bottom left corner - this was the "base" of the floor

    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire] #breaks floor into individual elements and passes them inside of this list. multiplying 2x to get it higher on the screen, so we can collide horizontally with it (test)
    
    offset_x = 0
    scroll_area_width = 200 #when we get to 200 pixels on the right or left, we start scrolling the background

    run = True
    while run:
        clock.tick(FPS)
        if player.PLAYER_HEALTH <= 0: #this if statement causes the game to crash if the user dies. Update to be Game Over screen instead.
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        
            if event.type == pygame.KEYDOWN:        #we want to put jumping in the event loop because if we do it in handle_move, pressing the jump key and holding it will make us jump constantly. We want to be forced to release the key and press it again to jump
                if event.key == pygame.K_SPACE and player.jump_count < 2:    #K_SPACE means space key. 
                    player.jump()

        player.loop(FPS)             #loop is what is actually moving our player every single frame
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):  #checks if we are moving right (x vel > 0) or left (x vel <0). The offset checks if we are right or left on the screen
            offset_x += player.x_vel 

    pygame.quit()
    quit() 

if __name__ == "__main__":   
    main(window)     #this makes to where we only call the main function when the game opens