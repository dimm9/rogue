import colorama
import utils
import time

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

from world import Map

from game_objects import PlayerType, Player, BlockType

colorama.init()
quitQ = False
game_over = False


def init_curses(stdscr):
    term_height, term_width = stdscr.getmaxyx()
    min_height = 30
    min_width = 120
    if term_height < min_height or term_width < min_width:
        raise RuntimeError(f"Terminal too small. Needs {min_width}x{min_height}, got {term_width}x{term_height}")
    curses.use_default_colors()
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_MAGENTA, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)

    stdscr.clear()
    stdscr.refresh()

def save(player):  # temp
    file = open("game.txt", "w")
    for i in player.stats:
        file.write(str(i) + "\n")
    print("...Progress saved!")
    file.close()


def load_game(player):
    file = open("game.txt", "r")
    load_all = file.readlines()
    player.xp = load_all[0]
    player.sp = load_all[1]
    player.lvl = load_all[2]
    player.name = load_all[3]
    # start_game(player.xp, player.sp, player.lvl, player.name)
    print("Welcome back, " + player.name + "!")
    file.close()

def game_over_screen(stdscr):
    utils.refresh()
    game_over_text = [
        "  ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗ ",
        " ██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗",
        " ██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝",
        " ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║▄▄ ██║██║   ██║██╔══╝  ██╔═══╝ ",
        " ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝╚██████╔╝███████╗██║     ",
        "  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝     "
    ]
    height, width = stdscr.getmaxyx()
    start_y = height // 2 - len(game_over_text) // 2
    start_x = width // 2 - max(len(line) for line in game_over_text) // 2

    for i, line in enumerate(game_over_text):
        stdscr.addstr(start_y + i, start_x, line, curses.color_pair(1))
        stdscr.refresh()
        time.sleep(0.2)

    stdscr.addstr(start_y + len(game_over_text) + 2, start_x, "Better luck next time!", curses.color_pair(1))
    stdscr.refresh()

    time.sleep(3)


def draw_menu(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 5, "The Edge of Oblivion", curses.color_pair(6))
    stdscr.addstr(2, 5, "----------------", curses.color_pair(1))
    stdscr.addstr(3, 5, "1 - PLAY", curses.color_pair(1))
    stdscr.addstr(4, 5, "2 - LOAD", curses.color_pair(1))
    stdscr.addstr(5, 5, "3 - HELP", curses.color_pair(1))
    stdscr.addstr(6, 5, "4 - EXIT", curses.color_pair(1))
    stdscr.addstr(7, 5, "----------------", curses.color_pair(1))
    stdscr.refresh()

def test_fight(player, enemy, stdscr):
    player.attack(enemy, stdscr)
    enemy.attack(player, stdscr)
    stdscr.addstr(30, 0, f"Player HP: {player.hp}, Enemy HP: {enemy.hp}",
                  curses.color_pair(4))

def start_game(stdscr, player, fireA, luckA, slowA):
    global game_over
    utils.refresh()
    map = Map(40, 28, player, fireA, luckA, slowA)
    while not game_over and not map.game_over:
        if map.new_map:
            utils.refresh()
            map.reset_map(stdscr)
            map.valid_player_location()
        map.show(map.blocks, map.width, map.height, stdscr)
        map.entities_list.player.check_state(stdscr)
        map.check_alive()
        map.entities_list.move_all(map, stdscr)
        move = stdscr.getch()
        if move == ord('w'):
            player.move(0, -player.speed, map, stdscr)
        elif move == ord('s'):
            player.move(0, player.speed, map, stdscr)
        elif move == ord('d'):
            player.move(player.speed, 0, map, stdscr)
        elif move == ord('a'):
            player.move(-player.speed, 0, map, stdscr)
        elif move == ord("i"):
            utils.refresh()
            player.show_inventory(stdscr, map)
        elif move == ord("e"):
            enemy = map.entities_list.find_enemy(force_check=False)
            if enemy:
                map.entities_list.fight_loop(stdscr, map, enemy)

        elif move == ord("q"):
            enemy = map.entities_list.find_enemy(force_check=False)
            if enemy:
                map.entities_list.shoot_loop(map, stdscr, enemy)

        utils.refresh()
        if player.lvl > 1:
            enemy = map.entities_list.find_enemy(force_check=True)
            if enemy is not None and map.blocks[map.entities_list.player.x][map.entities_list.player.y].block_type != BlockType.PLANT:
                if enemy.block_type == BlockType.ENEMY or enemy.block_type == BlockType.ENEMY_MAGE or enemy.block_type == BlockType.ENEMY_SPRINT:
                    map.entities_list.fight_loop(stdscr, map, enemy)
                elif enemy.block_type == BlockType.ENEMY_SHOOT:
                    if not map.entities_list.player.weapon and map.blocks[map.entities_list.player.x][map.entities_list.player.y].object.block_type != BlockType.PLANT:
                        points = utils.dice_points(1)
                        map.entities_list.player.hp -= points
                        stdscr.addstr(36, 0, f"NO WEAPON: Enemy attack damage: {points}", curses.color_pair(3))
                        stdscr.refresh()
                        time.sleep(0.8)
                    else:
                        map.entities_list.shoot_loop(map, stdscr, enemy)

        if player.hp <= 0:
            game_over = True
            map.game_over = True
        utils.refresh()

        if game_over or map.game_over:
            game_over_screen(stdscr)


def game_loop(stdscr):
    global quitQ
    while not quitQ:
        utils.refresh()
        draw_menu(stdscr)
        stdscr.addstr(8, 5, "> ", curses.color_pair(2))
        stdscr.refresh()
        choice = stdscr.getch()
        if choice == ord('1'):
            utils.refresh()
            # name = input(Fore.GREEN + "Character's name: ")
            utils.refresh()
            file = open("../characters.txt", "r")
            file_lines = file.readlines()
            for line in file_lines:
                line = line.strip()
                stdscr.addstr(line + "\n", curses.color_pair(2))
            stdscr.refresh()
            stdscr.addstr("Type 0, 1 or 2 >", curses.color_pair(2))
            stdscr.refresh()
            choice = stdscr.getch()
            luckA = 1
            fireA = 0
            slowA = 0
            if chr(choice) == '0':
                luckA = 2
            elif chr(choice) == '1':
                fireA = 3
            elif chr(choice) == '2':
                slowA = 3
            choice = chr(choice)
            if choice in ['0', '1', '2']:
                play_type = list(PlayerType)[int(choice)]
                player = Player(utils.MAX_HP, utils.MAX_SP, 1, "default", 0, 0, play_type, 1)
                start_game(stdscr, player, fireA, luckA, slowA)
                return
            else:
                stdscr.addstr("invalid choice\n", curses.color_pair(3))
                stdscr.refresh()
                time.sleep(2)
                continue
        if choice == ord('2'):
            utils.refresh()
            # load_game()
        if choice == ord('3'):
            utils.refresh()
            file = open("../gamehelp.txt", "r")
            text = file.readlines()
            height, width = stdscr.getmaxyx()
            for line in text:
                line = line.strip()
                if len(line) >= width:
                    line = line[:width - 1]
                try:
                    stdscr.addstr(line + "\n", curses.color_pair(4))
                except curses.error:
                    pass
            file.close()
            stdscr.refresh()
            time.sleep(5)
        if choice == ord('4'):
            stdscr.clear()
            stdscr.addstr("-----EDGE OF OBLIVION-----", curses.color_pair(3))
            quitQ = True
            return


def main(stdscr):
    init_curses(stdscr)
    game_loop(stdscr)


curses.wrapper(main)
