from enum import Enum
from abc import abstractmethod
from random import random
import random

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
import threading

class State(Enum):
    IDLE = "IDLE"
    ANGRY = "ANGRY"
    DEPRESSED = "DEPRESSED"
    HAPPY = "HAPPY"
class BlockType(Enum):
    ENEMY = "👽"
    ENEMY_SHOOT = "🤖"
    ENEMY_MAGE = "🧙🏻‍♀️"
    ENEMY_SPRINT = "👻"
    FLOOR = "⚫"
    WATER = "🟪"
    PLANT = "🌿"
    WEAPON = "🔫"
    DOOR = "🚪"
    KEY = "🔑"
    TRAP = "💀"
    POTION_SP = "🍷"
    POTION_HP = "🧪"
    COIN = "🪙"
    SCROLL = "📜"
    REAGEN = "🧬"
    EXIT = "🔴"
    ARMOR = "🛡"
    SHARD = "🔮"
    FIRE = "🔥"
    SLOW = "⌛"
    CAKE = "🍰"


class PlayerType(Enum):
    OUTCAST = "O"
    BYTE = "B"
    VENOM = "V"


class GameObject:
    def __init__(self, x, y, block_type):
        self.x = x
        self.y = y
        self.block_type = block_type


class ExitBlock(GameObject):
    def __init__(self, x, y, block_type):
        super().__init__(x, y, block_type)


class Entity(GameObject):
    def __init__(self, x, y, block_type, hp, sp):
        super().__init__(x, y, block_type)
        self.hp = hp
        self.sp = sp
        self.alive = True

    @abstractmethod
    def move(self, sx, sy, map, stdscr):
        pass

    def heal(self, scale):
        self.hp += scale

    @abstractmethod
    def damage(self, scale, stdscr):
        pass

    @abstractmethod
    def attack(self, enemy, stdscr):
        pass


class Player(Entity):
    def __init__(self, hp, sp, lvl, name, x, y, player_type, speed):
        super().__init__(x, y, player_type, hp, sp)
        self.hp = hp
        self.sp = sp
        self.lvl = lvl
        self.name = name
        self.stats = {hp, sp, lvl}
        self.player_type = player_type.value
        self.speed = speed
        self.money = 0
        self.hasKey = False
        self.weapon = False
        self.hasArmor = False
        self.armor_hp = utils.ARMOR_HP
        self.visible = True
        self.state = State.IDLE
        self.inventory = Inventory()
        self.damage_seed = 1

    def move(self, sx, sy, map, stdscr):
        new_x = self.x + sx
        new_y = self.y + sy
        if 0 <= new_x < map.width and 0 <= new_y < map.height:
            if map.blocks[new_x][new_y].object is not None:
                self.check_item(map.blocks[new_x][new_y].object, map, new_x, new_y, stdscr)
            if map.blocks[new_x][new_y].object is not None:
                if map.blocks[new_x][new_y].object.block_type in [BlockType.WATER] or map.blocks[new_x][
                    new_y].is_blocking:
                    return
            if not map.blocks[new_x][new_y].is_blocking:
                map.delete_obj(self.x, self.y)
                self.x = new_x
                self.y = new_y
                map.place_player(self, new_x, new_y)

    def show_inventory(self, stdscr, map):
        i = 4
        item_map = {}
        stdscr.clear()
        stdscr.addstr(0, 0, "---------------------------- INVENTORY ----------------------------", curses.color_pair(6))
        stdscr.refresh()
        stdscr.addstr(2, 0, f"[REAGENS: [🧬][x{self.inventory.reagens}]]  [SHARDS:[🔮][x{self.inventory.shards}]  [FOOD:[🍰][x{self.inventory.pills}]" ,
                      curses.color_pair(4))
        stdscr.refresh()
        stdscr.addstr(3, 0, f"🧬 -> r; ", curses.color_pair(4))
        for idx, item in enumerate(self.inventory.objects):
            item_map[str(idx)] = item
            if item.block_type != BlockType.REAGEN:
                stdscr.addstr(i, 0, f" {item.block_type.value} -> {idx}; ", curses.color_pair(4))
            i += 1

        stdscr.addstr(i, 0, "Select item: ", curses.color_pair(4))
        stdscr.refresh()

        key = stdscr.getch()
        selected_idx = chr(key)
        if selected_idx == 'r':
            stdscr.addstr(i + 2, 0, "Craft shard or upgrade player(1/2)?", curses.color_pair(4))
            stdscr.refresh()
            choice = stdscr.getch()
            selected = chr(choice)
            if selected == '1':
                if self.inventory.reagens >= self.lvl * 2 + 1:
                    self.inventory.shards += 1
                    self.inventory.reagens -= self.lvl * 2 + 1
                    stdscr.addstr(i + 3, 0,
                                  f"NEW SHARD CRAFTED -> shards count: {self.inventory.shards}  reagens count: {self.inventory.reagens}",
                                  curses.color_pair(1))
                    stdscr.refresh()
                    time.sleep(2)
                else:
                    stdscr.addstr(i + 3, 0, f"Not enough reagens!", curses.color_pair(3))
                    stdscr.refresh()
                    time.sleep(2)

            elif selected == '2':
                points = utils.dice_points(self.lvl)
                if self.inventory.reagens >= points:
                    utils.MAX_HP += 5
                    utils.MAX_SP += 5
                    self.hp = utils.MAX_HP
                    self.sp = utils.MAX_SP
                    self.damage_seed += 2
                    self.inventory.reagens -= points
                    stdscr.addstr(i + 3, 0, f"PLAYER UPGRADED -> new HP: {self.hp} new SP: {self.sp}",
                                  curses.color_pair(1))
                    stdscr.refresh()
                    time.sleep(2)
                else:
                    stdscr.addstr(i + 3, 0, f"Not enough reagens!", curses.color_pair(3))
                    stdscr.refresh()
                    time.sleep(2)
            else:
                stdscr.addstr(i + 3, 0, "Invalid choice!", curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        if selected_idx in item_map:
            selected_item = item_map[selected_idx]
            stdscr.addstr(i + 1, 0, f"Selected: {selected_item.block_type.value}", curses.color_pair(4))
            self.use_item(stdscr, selected_item, map)
            self.inventory.delete_obj(selected_item)
            stdscr.refresh()
            time.sleep(1)
            return selected_item
        else:
            stdscr.addstr(i + 1, 0, "Invalid selection", curses.color_pair(4))
            stdscr.refresh()
            time.sleep(1)
            return None

    def reset_slowed(self, map):
        time.sleep(5)
        map.slowed = False

    def use_item(self, stdscr, item, map):
        if item.block_type == BlockType.POTION_HP:
            points = random.randint(1, self.lvl * 5)
            if utils.MAX_HP < self.hp + points:
                points = utils.MAX_HP - self.hp
            self.heal(points)
            stdscr.addstr(20, 0, f"Healing +{points}", curses.color_pair(4))
            stdscr.refresh()
            time.sleep(1)
        elif item.block_type == BlockType.POTION_SP:
            points = random.randint(1, self.lvl * 5)
            if utils.MAX_SP < self.sp + points:
                points = utils.MAX_SP - self.sp
            self.sp += points
            stdscr.addstr(20, 0, f"Strength points upgrade +{points}", curses.color_pair(4))
            stdscr.refresh()
            time.sleep(1)
        elif item.block_type == BlockType.REAGEN:
            if self.inventory.reagens > self.lvl / 2 + 1:
                self.hp += 10
                self.sp += 10
        elif item.block_type == BlockType.KEY:
            self.hasKey = True
            stdscr.addstr(20, 0, f"Key used", curses.color_pair(4))
            stdscr.refresh()
        elif item.block_type == BlockType.WEAPON:
            self.weapon = True
            stdscr.addstr(20, 0, f"Weapon taken", curses.color_pair(4))
            stdscr.refresh()
        elif item.block_type == BlockType.ARMOR:
            self.hasArmor = True
            stdscr.addstr(20, 0, f"Armor taken", curses.color_pair(4))
            stdscr.refresh()
        elif item.block_type == BlockType.FIRE:
            map.explode(stdscr, self.x, self.y)
        elif item.block_type == BlockType.SLOW:
            map.slowed = True
            threading.Thread(target=self.reset_slowed, args=(map,)).start()


    def check_item(self, item, map, x, y, stdscr):
        if item.block_type == BlockType.PLANT:
            map.blocks[x][y].is_blocking = False
            map.blocks[x][y].object = self
            map.blocks[x][y].object_help = item
        if item.block_type == BlockType.POTION_HP:
            if self.money >= self.lvl * 1:
                if self.inventory.add_object(item):
                    map.blocks[x][y].is_blocking = False
                    self.money -= self.lvl * 1
                    map.delete_obj(x, y)
                else:
                    map.blocks[x][y].is_blocking = True
                    stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                    stdscr.refresh()
                    time.sleep(1)
            else:
                map.blocks[x][y].is_blocking = True
                stdscr.addstr(36, 0, f"Not enough money! Cost: {self.lvl * 1}, Your money: {self.money}",
                              curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        elif item.block_type == BlockType.POTION_SP or item.block_type == BlockType.CAKE:
            if self.money >= self.lvl * 1:
                if item.block_type == BlockType.CAKE:
                    self.inventory.pills += 1
                    self.money -= 1
                    stdscr.addstr(36, 0, "Pills balance upgraded!", curses.color_pair(2))
                    stdscr.refresh()
                    time.sleep(1)
                    map.blocks[x][y].is_blocking = False
                    map.delete_obj(x, y)
                else:
                    if self.inventory.add_object(item):
                        self.money -= self.lvl * 1
                        map.blocks[x][y].is_blocking = False
                        map.delete_obj(x, y)
                    else:
                        map.blocks[x][y].is_blocking = True
                        stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                        stdscr.refresh()
                        time.sleep(1)
            else:
                map.blocks[x][y].is_blocking = True
                stdscr.addstr(36, 0, f"Not enough money! Cost: {self.lvl * 1}, Your money: {self.money}",
                              curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        elif item.block_type == BlockType.COIN:
            self.money += 1
            map.blocks[x][y].is_blocking = False
            map.delete_obj(x, y)
        elif item.block_type == BlockType.KEY:
            if self.inventory.add_object(item):
                map.blocks[x][y].is_blocking = False
                map.delete_obj(x, y)
            else:
                stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                stdscr.refresh()
                time.sleep(1)
        elif item.block_type == BlockType.TRAP:
            self.damage(utils.dice_points(1), stdscr)
            map.blocks[x][y].is_blocking = False
            map.delete_obj(x, y)
        elif item.block_type == BlockType.DOOR:
            if self.hasKey:
                map.unlock_door(stdscr, item.x, item.y)
                map.blocks[x][y].is_blocking = False
                map.delete_obj(x, y)
            else:
                map.blocks[x][y].is_blocking = True
                stdscr.addstr(36, 0, "You dont have a key!", curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        elif item.block_type == BlockType.WEAPON:
            if self.money >= self.lvl * 2:
                if self.inventory.add_object(item):
                    map.blocks[x][y].is_blocking = False
                    self.money -= self.lvl * 2
                    map.delete_obj(x, y)
                else:
                    map.blocks[x][y].is_blocking = True
                    stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                    stdscr.refresh()
                    time.sleep(2)
            else:
                map.blocks[x][y].is_blocking = True
                stdscr.addstr(36, 0, f"Not enough money! Cost: {self.lvl * 2}, Your money: {self.money}",
                              curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        elif item.block_type == BlockType.SCROLL:
            map.read_scroll(stdscr)
            map.blocks[x][y].is_blocking = False
            map.delete_obj(x, y)
        elif item.block_type == BlockType.EXIT or map.blocks[x][y].block_type == BlockType.EXIT:
            self.lvl += 1
            map.reset_map(stdscr)
        elif item.block_type == BlockType.REAGEN:
            if self.inventory.add_object(item):
                stdscr.addstr(36, 0, f"New Reagen found!", curses.color_pair(4))
                stdscr.refresh()
                self.inventory.reagens += 1
                time.sleep(1)
                map.delete_obj(x, y)
            else:
                stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        elif item.block_type == BlockType.ARMOR:
            if self.money >= self.lvl * 2:
                if self.inventory.add_object(item):
                    map.blocks[x][y].is_blocking = False
                    self.money -= self.lvl * 2
                    map.delete_obj(x, y)
                else:
                    map.blocks[x][y].is_blocking = True
                    stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                    stdscr.refresh()
                    time.sleep(1)
            else:
                map.blocks[x][y].is_blocking = True
                stdscr.addstr(36, 0, f"Not enough money! Cost: {self.lvl * 2}, Your money: {self.money}",
                              curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
        elif item.block_type == BlockType.FIRE or item.block_type == BlockType.SLOW:
            if self.inventory.add_object(item):
                map.delete_obj(x, y)
            else:
                stdscr.addstr(36, 0, "INVENTORY FULL!", curses.color_pair(3))
                stdscr.refresh()
                time.sleep(1)
    def check_state(self, stdscr):
        if self.sp < 10 and self.state != State.ANGRY:
            self.state = State.ANGRY
            stdscr.addstr(39, 0, "************** ENTERING ANGRY STATE *************", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)
        if self.inventory.pills > self.lvl+1 and self.state != State.HAPPY:
            self.state = State.HAPPY
            stdscr.addstr(39, 0, "************** ENTERING HAPPY STATE *************", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)
        elif self.inventory.pills < self.lvl-1 and self.state != State.DEPRESSED and self.state != State.ANGRY:
            self.state = State.DEPRESSED
            stdscr.addstr(39, 0, "************* ENTERING DEPRESSED STATE ************", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)
        elif self.lvl <= self.inventory.pills <= self.lvl+1 and self.state != State.IDLE:
            stdscr.addstr(39, 0, "************* BACK TO IDLE STATE ************", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)
    def attack(self, enemy, stdscr):
        if self.sp > 0:
            self.check_state(stdscr)
            damage_points = utils.dice_points(self.lvl + self.damage_seed)
            if self.state == State.ANGRY:
                damage_points += self.lvl
            elif self.state == State.DEPRESSED:
                damage_points -= self.lvl
            actual_damage = min(damage_points, self.sp)
            enemy.damage(actual_damage, stdscr)
            self.sp -= actual_damage
            stdscr.addstr(36, 0, f"Enemy damaged: {actual_damage}, Player SP={self.sp}", curses.color_pair(1))
            time.sleep(1)
            stdscr.refresh()

    def damage(self, scale, stdscr):
        if self.hasArmor:
            self.armor_hp -= scale
            if self.armor_hp <= 0:
                self.hasArmor = False
                self.armor_hp = self.lvl * 10
        else:
            self.hp -= scale

    def shoot(self, enemy, stdscr):
        if not self.weapon:
            return
        if self.sp <= 0:
            stdscr.addstr(36, 0, "Not enough SP to shoot", curses.color_pair(3))
            time.sleep(2)
            stdscr.refresh()
            return
        damage_points = utils.dice_points(3)
        actual_damage = min(damage_points, self.sp)
        enemy.damage(actual_damage, stdscr)
        self.sp -= actual_damage
        stdscr.refresh()
        return actual_damage


class Item(GameObject):
    def __init__(self, x, y, block_type):
        super().__init__(x, y, block_type)


class Inventory:
    def __init__(self):
        self.objects = []
        self.reagens = 0
        self.size = 0
        self.shards = 0
        self.pills = 0

    def add_object(self, item):
        if self.size < utils.INVENTORY_SIZE:
            self.objects.append(item)
            if item.block_type != BlockType.CAKE or item.block_type != BlockType.SHARD or item.block_type != BlockType.REAGEN:
                self.size += 1
            return True
        else:
            return False

    def use_object(self):
        pass

    def delete_obj(self, item):
        self.objects.remove(item)
