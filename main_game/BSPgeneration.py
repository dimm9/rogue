import math
import random

from world import Block
from game_objects import BlockType

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def randomLims(min, max):
    return random.randint(min, max)

class Leaf:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = Point(x + (width / 2), y + (height / 2))
        self.room = None
        self.left = None
        self.right = None

    def addRoomT(self):
        self.room = Room(self)

class Tree:
    def __init__(self, root):
        self.root = root

    def addRoomsT(self, node):
        if isinstance(node, Leaf):
            node.addRoomT()
        if node.left is not None:
            self.addRoomsT(node.left)
        if node.right is not None:
            self.addRoomsT(node.right)

    def make_corridors(self, node):
        if node.left and node.right:
            self.connect_rooms(node.left.room, node.right.room)
            self.make_corridors(node.left)
            self.make_corridors(node.right)

    def connect_rooms(self, room1, room2):
        if room1 and room2:
            x1, y1 = room1.center.x, room1.center.y
            x2, y2 = room2.center.x, room2.center.y
            corridor = [(x1, y1), (x2, y1), (x2, y2)]
            return corridor

class Room:
    def __init__(self, container):
        self.x = container.x + randomLims(0, math.floor(container.width / 3))
        self.y = container.y + randomLims(0, math.floor(container.height / 3))
        self.width = container.width - (self.x - container.x)
        self.height = container.height - (self.y - container.y)
        self.width -= randomLims(0, self.width // 3)
        self.height -= randomLims(0, self.height // 3)
        self.width = max(3, self.width)
        self.height = max(3, self.height)


def random_split(container):
    MIN_SIZE = 5
    if container.width < MIN_SIZE or container.height < MIN_SIZE:   #mozna x2
        return None
    if container.width < MIN_SIZE:
        split_horizontal = True
    elif container.height < MIN_SIZE:
        split_horizontal = False
    else:
        split_horizontal = random.choice([True, False])

    if split_horizontal:
        min_height = MIN_SIZE
        max_height = container.height - MIN_SIZE
        if min_height >= max_height:
            return None
        split_height = randomLims(min_height, max_height)
        r1 = Leaf(container.x, container.y, container.width, split_height)
        r2 = Leaf(container.x, container.y + split_height, container.width, container.height - split_height)
    else:
        min_width = MIN_SIZE
        max_width = container.width - MIN_SIZE
        if min_width >= max_width:
            return None
        split_width = randomLims(min_width, max_width)
        r1 = Leaf(container.x, container.y, split_width, container.height)
        r2 = Leaf(container.x + split_width, container.y, container.width - split_width, container.height)
    return [r1, r2]


def split_container(container, iteration):
    if iteration == 0:
        container.addRoomT()
        return container
    sr = random_split(container)
    if sr is None:
        container.addRoomT()
        return container
    container.left = split_container(sr[0], iteration - 1)
    container.right = split_container(sr[1], iteration - 1)
    return container

class BSP:
    def __init__(self, map):
        self.map = map

    def coridors(self, leaf1, leaf2):
        if leaf2 and leaf1:
            x1 = int(leaf1.center.x)
            x2 = int(leaf2.center.x)
            y1 = int(leaf1.center.y)
            y2 = int(leaf2.center.y)
            return [x1, x2, y1, y2]
        return None

    def generate(self):
        root = Leaf(0, 0, self.map.width, self.map.height)
        tree_root = split_container(root, 15)
        self.fill_map(tree_root)

    def fill_map(self, root):
        self.fill_containers(root)

    def fill_containers(self, node):
        if node.room:
            for x in range(node.room.x, node.room.x + node.room.width):
                for y in range(node.room.y, node.room.y + node.room.height):
                    self.map.blocks[x][y] = Block(x, y, BlockType.FLOOR, False)
        else:
            for x in range(node.x, node.x + node.width):
                for y in range(node.y, node.y + node.height):
                    self.map.blocks[x][y] = Block(x, y, BlockType.WATER, True)
        if node.left:
            self.fill_containers(node.left)
        if node.right:
            self.fill_containers(node.right)

        if node.left and node.right:
            corridor = self.coridors(node.left, node.right)
            if corridor:
                self.draw_corridor(corridor[0], corridor[1], corridor[2], corridor[3])

    def draw_corridor(self, x1, x2, y1, y2):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.map.blocks[x][y1] = Block(x, y1, BlockType.FLOOR, False)

        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.map.blocks[x2][y] = Block(x2, y, BlockType.FLOOR, False)

