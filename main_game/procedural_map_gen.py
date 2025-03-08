from collections import deque

import world
from world import *
from enemies import *

class ProceduralGen:
    def __init__(self, map):
        self.map = map

    def gen_empty_room(self):
        return [[BlockType.FLOOR for _ in range(self.map.width)] for _ in range(self.map.height)]

    def gen_noise_grid(self, density):
        noise_grid = [[None for _ in range(self.map.height)] for _ in range(self.map.width)]
        for i in range(self.map.width):
            for j in range(self.map.height):
                scale = random.randint(1, 100)
                if scale > density:
                    noise_grid[i][j] = Block(i, j, BlockType.FLOOR, False)
                else:
                    noise_grid[i][j] = Block(i, j, BlockType.WATER, True)
        return noise_grid

    def cellular_automation(self, grid, iterations):
        for _ in range(iterations):
            from copy import deepcopy
            temp_grid = deepcopy(grid)
            for j in range(self.map.width):
                for k in range(self.map.height):
                    neighbour_count_wall = 0
                    for x in range(j-1, j+2):
                        for y in range(k-1, k+2):
                            if 0 <= x < self.map.width and 0 <= y < self.map.height:
                                if temp_grid[x][y].block_type == BlockType.WATER:
                                    neighbour_count_wall += 1
                            else:
                                neighbour_count_wall += 1
                    if neighbour_count_wall > 4:
                        grid[j][k] = Block(j, k, BlockType.WATER, True)
                    else:
                        grid[j][k] = Block(j, k, BlockType.FLOOR, False)
        start_x, start_y = self.find_floor_tile(grid)
        if start_x is not None:
            visited = set()
            self.flood_fill(grid, start_x, start_y, visited)
            self.convert_unreachable_tiles(grid, visited)
        return grid

    def count_neighbors(self, grid, x, y):
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                ny, nx = y + dy, x + dx
                if not (0 <= nx < self.map.width and 0 <= ny < self.map.height):
                    count += 1
                elif grid[ny][nx].block_type == BlockType.WATER:
                    count += 1
        return count

    def find_floor_tile(self, grid):
        for x in range(self.map.width):
            for y in range(self.map.height):
                if grid[x][y].block_type == BlockType.FLOOR:
                    return x, y
        return None, None

    def flood_fill(self, grid, x, y, visited):
        if not (0 <= y < self.map.height and 0 <= x < self.map.width):
            return
        if grid[x][y].block_type != BlockType.FLOOR or (x, y) in visited:
            return
        visited.add((x, y))
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            self.flood_fill(grid, x + dx, y + dy, visited)

    def convert_unreachable_tiles(self, grid, visited):
        for x in range(self.map.width):
            for y in range(self.map.height):
                if grid[x][y].block_type == BlockType.FLOOR and (x, y) not in visited:
                    grid[x][y] = Block(x, y, BlockType.WATER, True)


    def helpXY(self):
        possible = False
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        x = -1
        y = -1
        while not possible:
            x = random.randint(0, self.map.width - 1)
            y = random.randint(0, self.map.height - 1)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.map.width and 0 <= ny < self.map.height:
                    if self.map.blocks[nx][ny].block_type == BlockType.FLOOR:
                        possible = True
                        break
        return x, y

    def generate_objects(self, fire, luck, slow):
        block_types = list(BlockType)
        item_count = random.randint(25, 50)
        mage_probability = 1
        if self.map.entities_list.player.lvl < 3:
            mage_probability = 0
        elif self.map.entities_list.player.lvl > 7:
            mage_probability = 2
        weights = [2, 1, mage_probability, 1, 0, 0, 35, 2, 1, 1, 5, 3, 3, 30, 1, luck*1, 0, 1, 0, fire, slow, 5]
        for _ in range(item_count):
            while True:
                item_type = random.choices(block_types, weights=weights, k=1)[0]
                x, y = self.helpXY()
                if self.map.is_possible_item(x, y):
                    if item_type == BlockType.ENEMY:
                        enemy = Enemy(x, y, BlockType.ENEMY, utils.MAX_HP, utils.MAX_SP)
                        self.map.place_entity(enemy, x, y)
                        self.map.entities_list.place_entity(enemy)
                    elif item_type == BlockType.ENEMY_MAGE:
                        abilities = ["F", "S", "H"]
                        ability = abilities[random.randint(0, 2)]
                        enemy = Mage(x, y, BlockType.ENEMY_MAGE, self.map.entities_list.player.lvl*10-5, self.map.entities_list.player.lvl*10, ability)
                        self.map.place_entity(enemy, x, y)
                        self.map.entities_list.place_entity(enemy)
                    elif item_type == BlockType.ENEMY_SHOOT:
                        enemy = ShootingEnemy(x, y, BlockType.ENEMY_SHOOT, self.map.entities_list.player.lvl*10-5, self.map.entities_list.player.lvl*10, 3,
                                              self.map.entities_list.player.lvl)
                        self.map.place_entity(enemy, x, y)
                        self.map.entities_list.place_entity(enemy)
                    elif item_type == BlockType.ENEMY_SPRINT:
                        enemy = Spirit(x, y, BlockType.ENEMY_SPRINT, self.map.entities_list.player.lvl*10-10, self.map.entities_list.player.lvl*10, random.randint(self.map.entities_list.player.lvl, self.map.entities_list.player.lvl+3),
                                              self.map.entities_list.player.lvl)
                        self.map.place_entity(enemy, x, y)
                        self.map.entities_list.place_entity(enemy)
                    elif item_type == BlockType.PLANT:
                        self.place_plant_cluster(x, y)
                    elif item_type == BlockType.KEY:
                        if self.map.key_door_count > 0:
                            item = Item(x, y, BlockType.KEY)
                            self.map.place_object(item, x, y)
                    elif item_type == BlockType.DOOR:
                        if self.map.key_door_count > 0:
                            item = Item(x, y, BlockType.DOOR)
                            self.map.place_object(item, x, y)
                    else:
                        item = Item(x, y, item_type)
                        if not (item_type == BlockType.SCROLL and world.scroll_counter > world.max_scrolls):
                            self.map.place_object(item, x, y)
                    break
        r_count = 0
        reagen_max = random.randint(3, 7)
        while r_count < reagen_max:
            x = random.randint(0, self.map.width - 1)
            y = random.randint(0, self.map.height - 1)
            if self.map.blocks[x][y].block_type == BlockType.PLANT or self.map.blocks[x][y].object is not None and self.map.blocks[x][y].object.block_type == BlockType.PLANT:
                reagen = Item(x, y, BlockType.REAGEN)
                self.map.place_object(reagen, x, y)
                self.map.blocks[x][y].object = reagen
                r_count +=1


    def place_plant_cluster(self, x, y):
        cluster_size = random.randint(3, 7)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for _ in range(cluster_size):
            if self.map.is_possible_item(x, y):
                plant = Item(x, y, BlockType.PLANT)
                self.map.place_object(plant, x, y)
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.map.width and 0 <= ny < self.map.height and self.map.is_possible_item(nx, ny):
                    x, y = nx, ny
                    break

    def drunkard_walk(self, max_distance, density):
        for i in range(self.map.width):
            for j in range(self.map.height):
                self.map.blocks[i][j] = Block(i, j, BlockType.WATER, True)

        w, h = self.map.width, self.map.height
        total = w * h
        open_cells = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        while open_cells / total < density:
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            distance = 0
            while distance < max_distance:
                if 0 <= x < self.map.width and 0 <= y < self.map.height:
                    if self.map.blocks[x][y].block_type == BlockType.WATER:
                        self.map.blocks[x][y] = Block(x, y, BlockType.FLOOR, False)
                        open_cells += 1
                dx, dy = random.choice(directions)
                x += dx
                y += dy
                distance += 1

        w, h = self.map.width, self.map.height
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        visited = [[False for _ in range(h)] for _ in range(w)]
        start_found = False
        start_x = 0
        start_y = 0
        for i in range(w):
            for j in range(h):
                if self.map.blocks[i][j].block_type == BlockType.FLOOR:
                    start_x, start_y = i, j
                    start_found = True
                    break
            if start_found:
                break

        queue = deque([(start_x, start_y)])
        visited[start_x][start_y] = True

        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if not visited[nx][ny] and self.map.blocks[nx][ny].block_type == BlockType.FLOOR:
                        visited[nx][ny] = True
                        queue.append((nx, ny))
        for i in range(w):
            for j in range(h):
                if not visited[i][j]:
                    self.map.blocks[i][j] = Block(i, j, BlockType.WATER, True)
        return self.map.blocks

