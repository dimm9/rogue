import random
from game_objects import GameObject, BlockType, Item

try:
    import curses
except ImportError:
    import sys
    if sys.platform == "win":
        try:
            import pip
            pip.main(['install', 'windows-curses'])
            import curses
        except Exception as e:
            print(f"Failed to install or import curses on Windows: {e}")
            sys.exit(1)
    else:
        print("curses module is not available on this system.")
        sys.exit(1)

import time

import utils
from help_obj import EntitiesList
artefact_found = False
scroll_counter = 0
max_scrolls = 11
room_showing = False

class Block(GameObject):
    def __init__(self, x, y, block_type, is_blocking):
        super().__init__(x, y, block_type)
        self.is_blocking = is_blocking
        self.object = None
        self.object_help = Item(x, y, block_type=BlockType.FLOOR)


class ExitBlock(GameObject):
    def __init__(self, x, y, block_type):
        super().__init__(x, y, block_type)


class Map:
    def __init__(self, width, height, hero, fireA, luckA, slowA):
        self.width = width
        self.height = height
        self.blocks = [[Block(x, y, block_type=BlockType.FLOOR, is_blocking=False) for y in range(height)] for x in
                       range(width)]
        self.entities_list = EntitiesList(self)
        self.entities_list.player = hero
        self.objects = []
        self.new_map = True
        self.key_door_count = 9
        self.room =  [['' for _ in range(10)] for _ in range(10)]
        self.fire = fireA
        self.luck = luckA
        self.slow= slowA
        self.slowed = False
        self.game_over = False

    def reset_map(self, stdscr):
        self.entities_list.player.x = -1
        self.entities_list.player.y = -1
        stdscr.clear()
        self.procedural_generation(stdscr)
        utils.draw_frame(self)
        self.entities_list.player.damage_seed += 1

    def procedural_generation(self, stdscr):
        self.new_map = False
        from procedural_map_gen import ProceduralGen
        generation = ProceduralGen(self)
        if 1 <= self.entities_list.player.lvl <= 4:
            generation.drunkard_walk(30, 0.7)
        elif 5 <= self.entities_list.player.lvl <= 8:
            noise_grid = generation.gen_noise_grid(45)
            final_grid = generation.cellular_automation(noise_grid, 5)
            for x in range(self.width):
                for y in range(self.height):
                    self.blocks[x][y] = final_grid[x][y]
            generation.generate_objects(self.fire, self.luck, self.slow)
        elif 9 <= self.entities_list.player.lvl <= 12:
            from BSPgeneration import BSP
            bsp = BSP(self)
            bsp.generate()
            generation.generate_objects(self.fire, self.luck, self.slow)
        else:
            self.show_ending(stdscr)
            self.game_over = True

        if not self.game_over:
            utils.draw_frame(self)
            generation.generate_objects(self.fire, self.luck, self.slow)
            self.find_exit()
            self.valid_player_location()

    def explode(self, stdscr, x, y):
        radius = self.entities_list.player.lvl * 2 + 1
        start_x = max(0, x - radius)
        end_x = min(self.width, x + radius + 1)
        start_y = max(0, y - radius)
        end_y = min(self.height, y + radius + 1)
        for curr_x in range(start_x, end_x):
            for curr_y in range(start_y, end_y):
                distance = ((curr_x - x) ** 2 + (curr_y - y) ** 2) ** 0.5
                if distance <= radius:
                    obj = self.blocks[curr_x][curr_y].object
                    if obj is not None and (
                            obj.block_type == BlockType.ENEMY or obj.block_type == BlockType.ENEMY_SHOOT or obj.block_type == BlockType.ENEMY_MAGE):
                        self.delete_entity(obj)
                    elif self.blocks[curr_x][curr_y].block_type == BlockType.WATER:
                        self.blocks[curr_x][curr_y].block_type = BlockType.FLOOR
                        self.blocks[curr_x][curr_y].is_blocking = False
                    else:
                        self.delete_obj(curr_x, curr_y)
        stdscr.addstr(20, 0, f"!EXPLOSION: RADIUS={radius}!", curses.color_pair(5))
        stdscr.refresh()
        time.sleep(2)
    def show(self, blocks, w, h, stdscr):
        global MAX_HP, MAX_SP
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        for y in range(h):
            for x in range(w):
                if self.entities_list.player.x == x and self.entities_list.player.y == y:
                    if blocks[x][y].object_help.block_type == BlockType.FLOOR:
                        stdscr.addstr(y, x * 2, f"{self.entities_list.player.player_type: <3}")
                    else:
                        stdscr.addstr(y, x * 2, f"{BlockType.PLANT.value: <3}")
                elif blocks[x][y].object is not None and blocks[x][y].block_type != BlockType.PLANT:
                    stdscr.addstr(y, x * 2, f"{blocks[x][y].object.block_type.value: <3}")
                else:
                    stdscr.addstr(y, x * 2, f"{blocks[x][y].block_type.value: <3}")

        temp = self.entities_list.player.hp
        hp_segments = int(temp / utils.MAX_HP * 10)
        armor_segments = int(temp / utils.ARMOR_HP * 10 * self.entities_list.player.lvl)
        hp_str = "HP: [" + "*" * min(hp_segments, 10) + "-" * (10 - hp_segments) + "] " + str(self.entities_list.player.hp) + "/" + str(
            utils.MAX_HP)
        armor_str = ""
        if self.entities_list.player.hasArmor:
            armor_str = "   ARMOR: [" + "*" * min(armor_segments, 10) + "-" * (10 - armor_segments) + "] " + str(self.entities_list.player.armor_hp) + "/" + str(
                utils.ARMOR_HP * self.entities_list.player.lvl)
        if self.height + 1 < max_y:
            stdscr.addstr(self.height + 1, 0, hp_str + armor_str, curses.color_pair(2))

        sp_segments = int(self.entities_list.player.sp / utils.MAX_SP * 10)
        sp_str = "SP: [" + "*" * min(sp_segments, 10) + "-" * (10 - sp_segments) + "] " + str(self.entities_list.player.sp) + "/" + str(
            utils.MAX_SP)
        if self.height + 2 < max_y:
            stdscr.addstr(self.height + 2, 0, sp_str, curses.color_pair(1))
        if self.height + 3 < max_y:
            stdscr.addstr(self.height + 3, 0, f"LVL: {self.entities_list.player.lvl}", curses.color_pair(4))
        if self.height + 4 < max_y:
            stdscr.addstr(self.height + 4, 0, f"${self.entities_list.player.money}", curses.color_pair(5))
        stdscr.addstr(self.height + 5, 0, f"STATE: {self.entities_list.player.state.value}", curses.color_pair(3))
        stdscr.refresh()

    def find_exit(self):
        x = random.randint(int(self.width / 2) - 1, self.width - 1)
        y = random.randint(int(self.height / 2) - 1, self.height - 1)
        while True:
            if (0 <= x < self.width and 0 <= y < self.height and
                    not self.blocks[x][y].is_blocking and
                    self.blocks[x][y].object is None and
                    self.blocks[x][y].block_type == BlockType.FLOOR):
                break
            x = random.randint(int(self.width / 2) - 1, self.width - 1)
            y = random.randint(int(self.height / 2) - 1, self.height - 1)
        self.blocks[x][y].object = ExitBlock(x, y, BlockType.EXIT)
        self.blocks[x][y].block_type = BlockType.EXIT

    def valid_player_location(self):
        for x in range(self.width):
            found = False
            for y in range(self.height):
                if self.is_possible_entity(x, y) and (x != 0 and y != 0) and self.blocks[x][y].block_type != BlockType.EXIT:
                    self.delete_obj(0, 0)
                    if self.is_possible_entity(x, y):
                        self.place_player(self.entities_list.player, x, y)
                        found = True
                        return
            if found:
                return

    def check_alive(self):
        for enemy in self.entities_list.entities:
            if not enemy.alive:
                self.delete_obj(enemy.x, enemy.y)

    def is_possible_item(self, x, y):
        return (not self.blocks[x][y].is_blocking
                and self.blocks[x][y].object is None or not (self.blocks[x][y].block_type == BlockType.EXIT))

    def is_possible_entity(self, x, y):
        return (0 <= x < self.width and 0 <= y < self.height
                and not self.blocks[x][y].is_blocking
                and self.blocks[x][y].block_type == BlockType.FLOOR and self.blocks[x][y].block_type != BlockType.EXIT)

    def place_object(self, item, x, y):
        if self.is_possible_item(x, y):
            self.blocks[x][y].is_blocking = False
            self.blocks[x][y].object = item
            self.objects.append(item)

    def read_scroll(self, stdscr):
        global scroll_counter
        name = f"scrolls/scroll{scroll_counter}.txt"
        max_y, max_x = stdscr.getmaxyx()
        try:
            with open(name, "r") as file:
                file_lines = file.readlines()
                stdscr.clear()
                for i, line in enumerate(file_lines):
                    if i < max_y - 1:
                        stdscr.addstr(i, 0, line[:max_x - 1].strip(), curses.color_pair(2))
                        stdscr.refresh()
                        time.sleep(0.5)
                stdscr.refresh()
        except FileNotFoundError:
            stdscr.addstr(0, 0, f"Scroll file '{name}' not found.", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)

        scroll_counter += 1

    def place_player(self, hero, x, y):
        old_x, old_y = hero.x, hero.y
        if 0 <= old_x < self.width and 0 <= old_y < self.height:
            self.blocks[old_x][old_y].is_blocking = False
            self.blocks[old_x][old_y].object = None
            self.blocks[old_x][old_y].block_type = BlockType.FLOOR
        if self.is_possible_entity(x, y):
            self.blocks[x][y].is_blocking = True
            self.blocks[x][y].object = hero
            self.blocks[x][y].block_type = hero.player_type
            hero.x, hero.y = x, y

    def place_entity(self, entity, x, y):
        if self.is_possible_entity(x, y):
            self.blocks[x][y].is_blocking = True
            self.blocks[x][y].object = entity
            self.blocks[x][y].block_type = entity.block_type
            self.entities_list.entities.append(entity)

    def delete_entity(self, entity):
        self.entities_list.delete_entity(entity)
        self.blocks[entity.x][entity.y].is_blocking = False
        self.blocks[entity.x][entity.y].object = None
        self.blocks[entity.x][entity.y].block_type = BlockType.FLOOR


    def delete_obj(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height and self.blocks[x][y].object:
            obj = self.blocks[x][y].object
            if obj in self.objects:
                self.objects.remove(obj)
            self.blocks[x][y].object = None
            self.blocks[x][y].is_blocking = False
            if self.blocks[x][y].object_help.block_type == BlockType.PLANT:
                self.blocks[x][y].block_type = BlockType.PLANT
            else:
                self.blocks[x][y].block_type = BlockType.FLOOR

    def unlock_door(self, stdscr, x, y):
        self.blocks[x][y].is_blocking = False
        stdscr.addstr(36, 0, f"NEW SHARD UNLOCKED +🔮", curses.color_pair(4))
        stdscr.refresh()
        time.sleep(2)
        self.entities_list.player.inventory.shards += 1
        reagen = Item(x, y, BlockType.REAGEN)
        self.entities_list.player.inventory.add_object(reagen)
        self.entities_list.player.hasKey = False

    def show_ending(self, stdscr):
        max_y, max_x = stdscr.getmaxyx()
        if self.entities_list.player.inventory.shards >= 5:
            file = "../endings/good.txt"
        elif 3 <= self.entities_list.player.inventory.shards < 5:
            file = "../endings/ok.txt"
        else:
            file = "../endings/bad.txt"
        try:
            with open(file, "r") as file:
                file_lines = file.readlines()
                stdscr.clear()
                for i, line in enumerate(file_lines):
                    if i < max_y - 1:
                        stdscr.addstr(i, 0, line[:max_x - 1], curses.color_pair(2))
                        stdscr.refresh()
                        time.sleep(0.5)
                stdscr.refresh()
                time.sleep(2)
                self.game_over = True
        except FileNotFoundError:
            stdscr.addstr(0, 0, f"Ending not found.", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)
        self.game_over = True



