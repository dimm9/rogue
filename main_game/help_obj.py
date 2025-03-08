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

import time
import random

from game_objects import BlockType, State

class EntitiesList:
    def __init__(self, player):
        self.player = player
        self.entities = []

    def move_all(self, map, stdscr):
        if not map.slowed:
            for e in self.entities:
                if e.block_type == BlockType.ENEMY_SPRINT:
                    range = random.randint(3, 7)
                else:
                    range = 1
                e.move_loop(map, range, stdscr)

    def find_enemy(self, force_check=False):
        closest = None
        min_distance = float('inf')
        for entity in self.entities:
            if entity.block_type in [BlockType.ENEMY, BlockType.ENEMY_MAGE, BlockType.ENEMY_SHOOT, BlockType.ENEMY_SPRINT]:
                distance = abs(self.player.x - entity.x) + abs(self.player.y - entity.y)
                if distance < min_distance:
                    min_distance = distance
                    closest = entity
        if not closest:
            return None

        if force_check:
            if closest.block_type in [BlockType.ENEMY, BlockType.ENEMY_MAGE, BlockType.ENEMY_SPRINT] and min_distance < 2:
                return closest
            elif closest.block_type == BlockType.ENEMY_SHOOT and min_distance < 3:
                return closest
        else:
            if closest.block_type in [BlockType.ENEMY, BlockType.ENEMY_MAGE] and min_distance < 1.5:
                return closest
            elif closest.block_type == BlockType.ENEMY_SHOOT and min_distance < 2:
                return closest
        return None

    def get_entity(self, entity):
        return self.entities.index(entity)
    def place_entity(self, entity):
        self.entities.append(entity)

    def delete_entity(self, entity):
        self.entities.remove(entity)

    def fight_loop(self, stdscr, map, enemy):
        # utils.getWorldSize(W, H, map)
        tura = 1
        if not enemy:
            stdscr.addstr(35, 0, "No enemies nearby to fight", curses.color_pair(3))
            stdscr.refresh()
            time.sleep(2)
            return
        while enemy.alive and self.player.hp > 0:
            map.show(map.blocks, map.width, map.height, stdscr)
            stdscr.addstr(35, 0, f"Tura {tura}", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(1)
            tura += 1
            if self.player.alive:
                self.player.attack(enemy, stdscr)
            if enemy.alive:
                if enemy.block_type == BlockType.ENEMY or enemy.block_type == BlockType.ENEMY_SHOOT:
                    enemy.attack(self.player, stdscr)
                elif enemy.block_type == BlockType.ENEMY_MAGE:
                    enemy.attack_mage(self.player, map, stdscr)
                    if enemy.teleported:
                        break
            stdscr.addstr(38, 0, f"Player HP: {int(self.player.hp)}, Enemy HP: {int(enemy.hp)}", curses.color_pair(4))
            stdscr.refresh()
            time.sleep(1)
            if enemy.hp <= 0 or not enemy.alive:
                stdscr.addstr(39, 0, f"Enemy defeated!", curses.color_pair(2))
                stdscr.refresh()
                time.sleep(1)
                stdscr.addstr(40, 0, f"1 Pills lost! Pills balance:  {self.player.inventory.pills}  Money acquired: +5",
                              curses.color_pair(2))
                stdscr.refresh()
                time.sleep(1)
                self.player.state = State.IDLE
                self.player.money += 5
                self.player.inventory.pills -= 1
                enemy.alive = False
                map.delete_obj(enemy.x, enemy.y)
                break

    def shoot_loop(self, map, stdscr, enemy):
        if enemy is None:
            stdscr.addstr(35, 0, "No enemies nearby to shoot", curses.color_pair(3))
            return
        tura = 1
        while True:
            map.show(map.blocks, map.width, map.height, stdscr)
            stdscr.addstr(35, 0, f"Shooting Tura {tura}", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(2)

            damageP = enemy.attack_shoot(self.player, map, stdscr)
            stdscr.addstr(36, 0,
                          f"Shot: Player takes {damageP} damage. Enemy SP={enemy.sp} Player HP={self.player.hp}",
                          curses.color_pair(1))
            stdscr.refresh()
            time.sleep(2)

            damageE = self.player.shoot(enemy, stdscr)
            stdscr.addstr(37, 0,
                          f"Shot: Enemy takes {damageE} damage. Player SP={self.player.sp} Enemy HP={enemy.hp}",
                          curses.color_pair(1))
            stdscr.refresh()
            time.sleep(2)

            tura += 1
            if self.player.hp <= 0:
                break
            elif enemy.hp <= 0:
                stdscr.addstr(39, 0, "Enemy is dead", curses.color_pair(2))
                stdscr.refresh()
                time.sleep(1)
                stdscr.addstr(39, 0, f"1 Pill lost! Pills balance:  {self.player.inventory.pills}", curses.color_pair(2))
                stdscr.refresh()
                time.sleep(1)
                stdscr.addstr(39, 0, f"Money acquired: +7", curses.color_pair(2))
                stdscr.refresh()
                time.sleep(1)
                self.player.state = State.IDLE
                self.player.money += 7
                self.player.inventory.pills -= 1
                break
            stdscr.refresh()
            time.sleep(1)
            self.player.weapon = False






