import os
import random

MAX_HP = 30
MAX_SP = 50
ARMOR_HP = 20

MAP_WIDTH = 40
MAP_HEIGHT = 28

from game_objects import BlockType
from world import Map, Block

INVENTORY_SIZE = 10
def draw_frame(map):
    for x in range(0, map.width):
        for y in range(0, map.height):
            if x == 0 or y == 0 or y == map.height-1 or x == map.width-1:
                    map.blocks[x][y] = Block(x, y, BlockType.WATER, True)
def refresh():
    os.system('cls' if os.name == 'nt' else 'clear')

def dice_points(base_damage):
    dice_roll = random.randint(1, 6)
    if dice_roll <= 2:
        multiplier = 1
    elif dice_roll <= 4:
        multiplier = 2
    else:
        multiplier = 3
    damage = random.randint(base_damage, base_damage * multiplier)
    return max(damage, 1)




