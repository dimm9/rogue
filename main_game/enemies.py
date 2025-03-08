import random
import time

from game_objects import Entity, BlockType
import utils

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


class Enemy(Entity):
    def __init__(self, x, y, block_type, hp, sp):
        super().__init__(x, y, block_type, hp, sp)
        self.alive = True

    def move(self, sx, sy, map, stdscr):
        new_x = sx
        new_y = sy
        if 0 <= new_x < map.width and 0 <= new_y < map.height and not map.blocks[new_x][new_y].is_blocking and map.blocks[new_x][new_y].block_type != BlockType.EXIT:
            map.delete_entity(self)
            self.x = new_x
            self.y = new_y
            if map.blocks[new_x][new_y].block_type != BlockType.EXIT:
                map.place_entity(self, new_x, new_y)

    def move_loop(self, map, range, stdscr):
        if not self.alive:
            return
        movement = random.randint(1, range)
        pos = random.randint(0, 1)
        if pos == 1:
            new_x = self.x + movement if random.random() > 0.5 else self.x - movement
            new_x = max(0, min(new_x, map.width - 1))
            self.move(new_x, self.y, map, stdscr)
        else:
            new_y = self.y + movement if random.random() > 0.5 else self.y - movement
            new_y = max(0, min(new_y, map.height - 1))
            self.move(self.x, new_y, map, stdscr)

    def attack(self, player, stdscr):
        if self.x-1 <= player.x <= self.x+1 and self.y-1 <= player.y <= self.y+1:
            if self.sp > 0:
                damage_points = utils.dice_points(player.lvl - 1)
                actual_damage = min(damage_points, self.sp)
                player.damage(actual_damage, stdscr)
                self.sp -= actual_damage
                stdscr.addstr(37, 0, f"Player damaged: {damage_points}, Enemy SP={self.sp}", curses.color_pair(1))
                stdscr.refresh()
                time.sleep(1)

    def damage(self, scale, stdscr):
            self.hp -= scale
            if self.hp <= 0:
                self.alive = False

class ShootingEnemy(Enemy):
    def __init__(self, x, y, block_type, hp, sp, distance, lvl):
        super().__init__(x, y, block_type, hp, sp)
        self.distance = distance
        self.lvl = lvl

    def attack_shoot(self, player, map, stdscr):
        if self.in_range(player, map):
            if self.sp > 0:
                damage_points = utils.dice_points(1)
                actual_damage = min(damage_points, self.sp)
                player.damage(actual_damage, stdscr)
                self.sp -= actual_damage
                stdscr.refresh()
                return actual_damage


    def in_range(self, player, map):
        dx = abs(player.x - self.x)
        dy = abs(player.y - self.y)
        if dx <= self.distance and dy == 0:
            for i in range(1, dx):
                if player.x > self.x:
                    step = i
                else:
                    step = -i
                if map.blocks[self.x + step][self.y].is_blocking:
                    return False
            return True
        if dy <= self.distance and dx == 0:
            for i in range(1, dy):
                if player.y > self.y:
                    step = i
                else:
                    step = -i
                if map.blocks[self.x][self.y + step].is_blocking:
                    return False
            return True
        return False

    def damage(self, scale, stdscr):
            self.hp -= scale
            if self.hp <= 0:
                self.alive = False


class Mage(Entity):
    def __init__(self, x, y, block_type, hp, sp, ability):
        super().__init__(x, y, block_type, hp, sp)
        self.ability = ability
        self.teleported = False

    def move(self, sx, sy, map, stdscr):
        new_x = sx
        new_y = sy
        if 0 <= new_x < map.width and 0 <= new_y < map.height and not map.blocks[new_x][new_y].is_blocking:
            map.delete_entity(self)
            self.x = new_x
            self.y = new_y
            map.place_entity(self, new_x, new_y)

    def move_loop(self, map, range, stdscr):
        if not self.alive:
            return
        movement = random.randint(1, range)
        pos = random.randint(0, 1)
        if pos == 1:
            new_x = self.x + movement if random.random() > 0.5 else self.x - movement
            new_x = max(0, min(new_x, map.width - 1))
            self.move(new_x, self.y, map, stdscr)
        else:
            new_y = self.y + movement if random.random() > 0.5 else self.y - movement
            new_y = max(0, min(new_y, map.height - 1))
            self.move(self.x, new_y, map, stdscr)


    def attack_mage(self, player, map, stdscr):
        if self.x-1 <= player.x <= self.x+1 and self.y-1 <= player.y <= self.y+1:
            if self.sp > 0:
                damage_points = utils.dice_points(2)
                actual_damage = min(damage_points, self.sp)
                player.damage(actual_damage, stdscr)
                self.sp -= actual_damage
                stdscr.addstr(37, 0, f"Player damaged with: {damage_points}, Enemy SP: {self.sp}", curses.color_pair(1))
                stdscr.refresh()
                time.sleep(1)
                if self.ability == "F":
                    stdscr.addstr(39, 0, f"*Bio mage is flying away* -> Last X: {self.x} Last Y: {self.y}", curses.color_pair(5))
                    self.teleported = True
                    stdscr.refresh()
                    time.sleep(1)
                    map.delete_obj(self.x, self.y)
                    self.x = random.randint(self.x, self.x + 10)
                    self.y = random.randint(self.y, self.y + 10)
                    while not map.is_possible_entity(self.x, self.y):
                        self.x = random.randint(self.x, self.x+10)
                        self.y = random.randint(self.y, self.y+10)
                    map.place_entity(self, self.x, self.y)
                if self.ability == "H":
                    self.hp += random.randint(1, 5)
                    stdscr.addstr(39, 0, f"*Bio mage is healing* -> new HP = {self.hp}", curses.color_pair(5))
                    stdscr.refresh()
                    time.sleep(1)
                if self.ability == "S":
                    player.sp -= random.randint(1, 5)
                    stdscr.addstr(39, 0, f"*Bio mage is weakening player* -> Player SP = {player.hp}", curses.color_pair(5))
                    stdscr.refresh()
                    time.sleep(1)

    def damage(self, scale, stdscr):
            self.hp -= scale
            if self.hp <= 0:
                self.alive = False


class Spirit(Enemy):
    def __init__(self, x, y, block_type, hp, sp, speed, lvl):
        super().__init__(x, y, block_type, hp, sp)
        self.speed = speed
        self.lvl = lvl





