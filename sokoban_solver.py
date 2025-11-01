import time
import os
import heapq
import threading
import tkinter as tk
from tkinter import messagebox
import tracemalloc  # Thêm thư viện đo bộ nhớ

# ----------------------- Original game logic (kept, not rewritten) -----------------------

# Biến toàn cục lưu bản đồ game
game_map = []

class GameState:
    """
    Lớp đại diện cho trạng thái của game tại một thời điểm
    Mỗi trạng thái bao gồm: vị trí người chơi, vị trí các hộp, chi phí và heuristic
    """
    def __init__(self, player, boxes, cost=0, heuristic=0):
        self.player = player  # (x, y) = (col, row) - vị trí người chơi
        self.boxes = frozenset(boxes)  # Tập hợp các vị trí hộp (dùng frozenset để có thể hash)
        self.cost = cost  # Chi phí từ trạng thái ban đầu đến trạng thái hiện tại
        self.heuristic = heuristic  # Ước lượng chi phí từ trạng thái hiện tại đến goal

    def __eq__(self, other):
        """So sánh bằng: hai trạng thái bằng nhau nếu player và boxes giống nhau"""
        return self.player == other.player and self.boxes == other.boxes

    def __hash__(self):
        """Hàm băm để có thể dùng làm key trong dictionary"""
        return hash((self.player, self.boxes))

    def __lt__(self, other):
        """So sánh nhỏ hơn: dùng cho priority queue trong A*"""
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)

    def generate_state(self):
        """
        Sinh ra các trạng thái con có thể đạt được từ trạng thái hiện tại
        Trả về danh sách các GameState mới
        """
        # Các hướng di chuyển: Lên, Xuống, Trái, Phải (dx, dy)
        moves = [(0, -1), (0, +1), (-1, 0), (+1, 0)]

        child_state = []  # Danh sách trạng thái con

        for dx, dy in moves:
            px, py = self.player
            new_player = (px + dx, py + dy)  # Vị trí người chơi mới

            # Kiểm tra nếu vị trí mới là tường
            if game_map[new_player[1]][new_player[0]] == "#":
                continue  # Không thể di chuyển vào tường

            # Trường hợp 1: Di chuyển vào ô trống
            if new_player not in self.boxes:
                child_state.append(GameState(new_player, self.boxes, self.cost + 1))

            # Trường hợp 2: Đẩy hộp
            else:
                new_box = (new_player[0] + dx, new_player[1] + dy)  # Vị trí hộp mới sau khi đẩy

                # Kiểm tra có thể đẩy hộp: không phải tường và không có hộp khác
                if game_map[new_box[1]][new_box[0]] != "#" and new_box not in self.boxes:
                    new_box_state = set(self.boxes)
                    new_box_state.remove(new_player)  # Xóa hộp ở vị trí cũ
                    new_box_state.add(new_box)  # Thêm hộp ở vị trí mới
                    child_state.append(GameState(new_player, frozenset(new_box_state), self.cost + 1))

        return child_state


class Solver:
    """
    Lớp giải thuật tìm đường cho Sokoban
    Implement BFS và A* search
    """
    
    def bfs(self, start_state, goal):
        """
        Giải thuật BFS (Breadth-First Search)
        Tìm đường đi ngắn nhất theo số bước di chuyển
        """
        q = [start_state]  # Hàng đợi cho BFS
        parents = {start_state: None}  # Dictionary lưu vết đường đi

        while q:
            state = q.pop(0)  # Lấy trạng thái đầu hàng đợi

            # Kiểm tra điều kiện chiến thắng: tất cả hộp đều ở goal
            if state.boxes == goal:
                # Truy vết đường đi từ goal về start
                path = []
                curr = state
                while curr is not None:
                    path.append(curr)
                    curr = parents[curr]
                path.reverse()  # Đảo ngược để có đường đi từ start đến goal
                return path

            # Duyệt qua các trạng thái con
            for child in state.generate_state():
                if child not in parents:
                    parents[child] = state  # Lưu parent
                    q.append(child)  # Thêm vào hàng đợi

        return []  # Không tìm thấy đường đi

    def dfs(self):
        """Giải thuật DFS (chưa implement)"""
        pass

    def a_star(self, start_state, goal):
        """
        Giải thuật A* search
        Kết hợp chi phí thực tế (cost) và heuristic để tìm đường đi tối ưu
        """
        open_set = []  # Priority queue cho các trạng thái cần xét
        heapq.heappush(open_set, (0, start_state))  # Đẩy trạng thái đầu với f_score = 0
        
        g_score = {start_state: 0}  # Chi phí thực tế từ start đến mỗi trạng thái
        parents = {start_state: None}  # Dictionary lưu vết đường đi
        
        goal_positions = set(goal)  # Tập hợp các vị trí goal

        while open_set:
            _, current = heapq.heappop(open_set)  # Lấy trạng thái có f_score nhỏ nhất

            # Kiểm tra điều kiện chiến thắng
            if current.boxes == goal:
                # Truy vết đường đi
                path = []
                curr = current
                while curr is not None:
                    path.append(curr)
                    curr = parents[curr]
                path.reverse()
                return path

            # Duyệt qua các trạng thái con
            for child in current.generate_state():
                # Tính heuristic cho trạng thái con
                child.heuristic = self.heuristic_func(child.boxes, goal_positions, child.player)
                
                # Chi phí thực tế từ start đến child (qua current)
                tentative_g_score = g_score[current] + 1
                
                # Nếu tìm được đường đi tốt hơn đến child
                if child not in g_score or tentative_g_score < g_score[child]:
                    g_score[child] = tentative_g_score
                    child.cost = tentative_g_score
                    parents[child] = current
                    # f_score = g_score + heuristic
                    f_score = tentative_g_score + child.heuristic
                    heapq.heappush(open_set, (f_score, child))

        return []  # Không tìm thấy đường đi

    def heuristic_func(self, boxes, goals, player):
        """
        Hàm heuristic cho A*
        Kết hợp nhiều yếu tố để ước lượng chi phí còn lại:
        1. Tổng khoảng cách Manhattan từ các box đến goal gần nhất
        2. Penalty cho các box ở vị trí deadlock
        3. Khoảng cách từ player đến box gần nhất
        """
        total_distance = 0
        box_list = list(boxes)
        goal_list = list(goals)
        
        # 1. Tính tổng khoảng cách Manhattan từ mỗi box đến goal gần nhất
        for box in box_list:
            min_dist = float('inf')
            for goal_pos in goal_list:
                dist = abs(box[0] - goal_pos[0]) + abs(box[1] - goal_pos[1])
                min_dist = min(min_dist, dist)
            total_distance += min_dist
        
        # 2. Thêm penalty cho deadlock đơn giản
        deadlock_penalty = 0
        for box in box_list:
            if box not in goals:
                # Kiểm tra deadlock cơ bản: box trong góc
                x, y = box
                if self.is_corner_deadlock(x, y):
                    deadlock_penalty += 100  # Penalty lớn cho vị trí deadlock
        
        # 3. Khoảng cách từ player đến box gần nhất (để ưu tiên states mà player gần boxes)
        min_player_to_box = float('inf')
        for box in box_list:
            dist = abs(player[0] - box[0]) + abs(player[1] - box[1])
            min_player_to_box = min(min_player_to_box, dist)
        
        return total_distance + deadlock_penalty + min_player_to_box * 0.1

    def is_corner_deadlock(self, x, y):
        """Kiểm tra xem box có bị kẹt trong góc không"""
        # Kiểm tra nếu ở góc map (hai hướng di chuyển bị chặn bởi tường)
        if (game_map[y-1][x] == '#' and game_map[y][x-1] == '#') or \
           (game_map[y-1][x] == '#' and game_map[y][x+1] == '#') or \
           (game_map[y+1][x] == '#' and game_map[y][x-1] == '#') or \
           (game_map[y+1][x] == '#' and game_map[y][x+1] == '#'):
            return True
        return False


class Utils:
    """Lớp tiện ích cho việc hiển thị và xử lý phụ"""
    
    def print_map(self, map_to_print):
        """In bản đồ ra console"""
        for r in map_to_print:
            print("".join(r))
        print()

    def print_path(self, init_player_pos, path):
        """Chuyển đổi đường đi thành chuỗi hướng di chuyển (U, D, L, R)"""
        if not path:
            print("No solution path to print.")
            return

        curr_pos = init_player_pos
        path_str = ""

        for state in path[1:]:
            next_pos = state.player
            dx = next_pos[0] - curr_pos[0]
            dy = next_pos[1] - curr_pos[1]

            # Xác định hướng di chuyển dựa trên vector (dx, dy)
            if (dx, dy) == (1, 0):
                path_str += "R"  # Right
            elif (dx, dy) == (-1, 0):
                path_str += "L"  # Left
            elif (dx, dy) == (0, 1):
                path_str += "D"  # Down
            elif (dx, dy) == (0, -1):
                path_str += "U"  # Up

            curr_pos = next_pos

        print(f"Path: {path_str}\n")

    def clear_screen(self):
        """Xóa màn hình console"""
        os.system("cls" if os.name == "nt" else "clear")

    def animate(self, path, goals, base_map):
        """Hiển thị animation đường đi trên console"""
        if not path:
            return

        for state in path:
            self.clear_screen()
            # Tạo bản đồ tạm thời để hiển thị
            temp_map = [list(row) for row in base_map]

            # Vẽ các hộp
            for bx, by in state.boxes:
                if (bx, by) in goals:
                    temp_map[by][bx] = "*"  # Hộp trên goal
                else:
                    temp_map[by][bx] = "$"  # Hộp thường

            # Vẽ người chơi
            px, py = state.player
            if (px, py) in goals:
                temp_map[py][px] = "+"  # Người chơi trên goal
            else:
                temp_map[py][px] = "@"  # Người chơi thường

            print("Sokoban Solution Animation")
            self.print_map(temp_map)
            time.sleep(0.2)

# ----------------------- End original logic -----------------------

# ----------------------- UI / Glue code -----------------------

CELL_SIZE = 40  # pixels per tile in canvas
COLORS = {
    '#': '#777777',  # wall: gray
    ' ': '#ffffff',  # empty: white
    'player': '#0077cc',  # player: blue
    'box': '#8B5A2B',  # box: brown
    'goal': '#FFF59D',  # goal: light yellow
    'box_on_goal': '#D2691E',  # darker box on goal
    'player_on_goal': '#3399ff',
}

class SokobanUI:
    """
    Lớp giao diện người dùng sử dụng Tkinter
    Kết nối logic game với giao diện đồ họa
    """
    def __init__(self, root, level_file="level.txt"):
        self.root = root
        self.level_file = level_file
    
        # Load level và khởi tạo trạng thái game
        self.base_map = []
        self.load_level()

        # Lưu trạng thái ban đầu để reset
        self.original_player = self.player
        self.original_boxes = set(self.boxes)
        self.goals = set(self.goals)

        # Khởi tạo các thành phần
        self.state = GameState(self.player, self.boxes)
        self.solver = Solver()
        self.utils = Utils()

        # Thông tin UI
        self.rows = len(self.base_map)
        self.cols = max(len(r) for r in self.base_map)

        # Xây dựng giao diện
        self.build_ui()

        # Vẽ bản đồ ban đầu
        self.draw_map()

        # Gán sự kiện bàn phím
        self.root.bind('<Up>', lambda e: self.move(0, -1))
        self.root.bind('<Down>', lambda e: self.move(0, 1))
        self.root.bind('<Left>', lambda e: self.move(-1, 0))
        self.root.bind('<Right>', lambda e: self.move(1, 0))
        
    def create_default_level(self):
        """Tạo testcase mặc định nếu file level không tồn tại"""
        global game_map
        
        # Testcase mặc định
        default_map = [
            "  #####  ",
            " ##   ###",
            " #      #",
            " #*#*#* #",
            " # #@$ ##",
            "## # #.# ",
            "#      # ",
            "#   #  # ",
            "######## "
        ]
        
        # Chuyển đổi từ list string sang dạng grid
        self.base_map = []
        player = (0, 0)
        boxes = set()
        goals = set()
        
        for row, line in enumerate(default_map):
            map_row = []
            for col, char in enumerate(line):
                if char == "@":
                    player = (col, row)
                    map_row.append(" ")
                elif char == "$":
                    boxes.add((col, row))
                    map_row.append(" ")
                elif char == ".":
                    goals.add((col, row))
                    map_row.append(".")
                elif char == "*":
                    boxes.add((col, row))
                    goals.add((col, row))
                    map_row.append(".")
                elif char == "+":
                    player = (col, row)
                    goals.add((col, row))
                    map_row.append(".")
                else:
                    map_row.append(char)
            self.base_map.append(map_row)
        
        # Cập nhật biến toàn cục và các thuộc tính
        game_map = self.base_map
        self.player = player
        self.boxes = frozenset(boxes)
        self.goals = frozenset(goals)
        self.original_player = player
        self.original_boxes = set(boxes)

    def load_level(self):
        """Đọc file level và khởi tạo bản đồ, người chơi, hộp, goal"""
        global game_map
        player = (0, 0)
        boxes = set()
        goals = set()

        if not os.path.exists(self.level_file):
            print(f"Level file '{self.level_file}' not found. Using default level...")
            self.create_default_level()  # Gọi phương thức tạo level mặc định
            return  # Thoát khỏi phương thức sau khi tạo level mặc định

        with open(self.level_file, 'r') as file:
            base_map = []
            for row, line in enumerate(file):
                map_row = []
                for col, char in enumerate(line.rstrip('\n')):
                    if char == "@":
                        player = (col, row)
                        map_row.append(" ")  # Thay player bằng ô trống
                    elif char == "$":
                        boxes.add((col, row))
                        map_row.append(" ")  # Thay box bằng ô trống
                    elif char == ".":
                        goals.add((col, row))
                        map_row.append(".")  # Giữ nguyên goal
                    elif char == "*":
                        boxes.add((col, row))
                        goals.add((col, row))
                        map_row.append(".")  # Box trên goal
                    elif char == "+":
                        player = (col, row)
                        goals.add((col, row))
                        map_row.append(".")  # Player trên goal
                    else:
                        map_row.append(char)  # Giữ nguyên tường, ô trống
                base_map.append(map_row)

        # Cập nhật các biến
        self.base_map = base_map
        game_map = base_map  # Cập nhật biến toàn cục
        self.player = player
        self.boxes = frozenset(boxes)
        self.goals = frozenset(goals)

    def build_ui(self):
        """Tạo canvas và các nút điều khiển"""
        # Canvas chính để vẽ game
        self.canvas = tk.Canvas(self.root, width=self.cols * CELL_SIZE, height=self.rows * CELL_SIZE, bg='black')
        self.canvas.grid(row=0, column=0, columnspan=6)

        # Các nút điều khiển di chuyển
        btn_up = tk.Button(self.root, text='Up', width=8, command=lambda: self.move(0, -1))
        btn_up.grid(row=1, column=1, pady=6)

        btn_left = tk.Button(self.root, text='Left', width=8, command=lambda: self.move(-1, 0))
        btn_left.grid(row=2, column=0, padx=6)

        btn_reset = tk.Button(self.root, text='Reset', width=8, command=self.reset_level)
        btn_reset.grid(row=2, column=1)

        btn_right = tk.Button(self.root, text='Right', width=8, command=lambda: self.move(1, 0))
        btn_right.grid(row=2, column=2, padx=6)

        btn_down = tk.Button(self.root, text='Down', width=8, command=lambda: self.move(0, 1))
        btn_down.grid(row=3, column=1, pady=6)

        # Các nút giải tự động
        btn_solve_bfs = tk.Button(self.root, text='Auto Solve (BFS)', width=15, command=lambda: self.start_auto_solve('bfs'))
        btn_solve_bfs.grid(row=1, column=3, padx=10)

        btn_solve_astar = tk.Button(self.root, text='Auto Solve (A*)', width=15, command=lambda: self.start_auto_solve('astar'))
        btn_solve_astar.grid(row=2, column=3)

        # Label hiển thị thông tin
        self.info_var = tk.StringVar()
        self.info_var.set('Moves: 0 | Memory: 0.0KB')
        self.info_label = tk.Label(self.root, textvariable=self.info_var, font=('Arial', 10))
        self.info_label.grid(row=1, column=4, columnspan=2, padx=10, sticky='w')

        # Sự kiện click trên canvas để di chuyển
        self.canvas.bind('<Button-1>', self.on_canvas_click)

        # Biến đếm số bước di chuyển
        self.move_count = 0

    def draw_map(self):
        """Vẽ toàn bộ bản đồ lên canvas"""
        self.canvas.delete('all')  # Xóa canvas cũ

        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                # Lấy ký tự tại vị trí (c, r)
                ch = ' '
                if r < len(self.base_map) and c < len(self.base_map[r]):
                    ch = self.base_map[r][c]

                # Vẽ nền (tường hoặc ô trống)
                if ch == '#':
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS['#'], outline='black')
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS[' '], outline='#cccccc')

                # Vẽ goal (nếu có)
                if (c, r) in self.goals:
                    self.canvas.create_oval(x1+8, y1+8, x2-8, y2-8, fill=COLORS['goal'], outline='')

                # Vẽ hộp
                if (c, r) in self.state.boxes:
                    if (c, r) in self.goals:
                        # Hộp trên goal
                        self.canvas.create_rectangle(x1+6, y1+6, x2-6, y2-6, fill=COLORS['box_on_goal'], outline='black')
                    else:
                        # Hộp thường
                        self.canvas.create_rectangle(x1+6, y1+6, x2-6, y2-6, fill=COLORS['box'], outline='black')

                # Vẽ người chơi
                if (c, r) == self.state.player:
                    if (c, r) in self.goals:
                        # Người chơi trên goal
                        self.canvas.create_oval(x1+10, y1+10, x2-10, y2-10, fill=COLORS['player_on_goal'], outline='black')
                    else:
                        # Người chơi thường
                        self.canvas.create_oval(x1+10, y1+10, x2-10, y2-10, fill=COLORS['player'], outline='black')

        # Cập nhật thông tin
        self.info_var.set(f'Moves: {self.move_count}')

    def on_canvas_click(self, event):
        """Xử lý click trên canvas: di chuyển đến ô được click nếu liền kề"""
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE

        px, py = self.state.player
        dx = col - px
        dy = row - py

        # Chỉ cho phép di chuyển đến ô liền kề (không chéo)
        if abs(dx) + abs(dy) == 1:
            self.move(dx, dy)

    def move(self, dx, dy):
        """Thực hiện di chuyển sử dụng logic game gốc"""
        px, py = self.state.player
        new_p = (px + dx, py + dy)  # Vị trí mới của người chơi

        # Kiểm tra tường
        if game_map[new_p[1]][new_p[0]] == '#':
            return

        boxes = set(self.state.boxes)

        # Trường hợp đẩy hộp
        if new_p in boxes:
            new_box = (new_p[0] + dx, new_p[1] + dy)  # Vị trí mới của hộp
            
            # Kiểm tra có thể đẩy: không phải tường và không có hộp khác
            if game_map[new_box[1]][new_box[0]] == '#' or new_box in boxes:
                return  # Không thể đẩy
            
            # Thực hiện đẩy hộp
            boxes.remove(new_p)
            boxes.add(new_box)

        # Cập nhật trạng thái mới
        self.state = GameState(new_p, frozenset(boxes))
        self.move_count += 1
        self.draw_map()

        # Kiểm tra chiến thắng
        if self.check_win():
            messagebox.showinfo('You win!', f'All boxes are on goals! Moves: {self.move_count}')

    def check_win(self):
        """Kiểm tra điều kiện chiến thắng: tất cả hộp đều ở goal"""
        return set(self.state.boxes) == set(self.goals)

    def reset_level(self):
        """Reset về trạng thái ban đầu của level"""
        self.state = GameState(self.original_player, frozenset(self.original_boxes))
        self.move_count = 0
        self.info_var.set('Moves: 0 | Memory: 0.0KB')  # Reset cả memory display
        self.draw_map()

    def start_auto_solve(self, method):
        """Chạy solver trong thread riêng để không làm đơ UI"""
        t = threading.Thread(target=self.auto_solve, args=(method,), daemon=True)
        t.start()

    def auto_solve(self, method):
        """Gọi solver và animate kết quả trên UI thread"""
        # Vô hiệu hóa điều khiển trong khi giải
        self.disable_controls()

        start_state = GameState(self.state.player, self.state.boxes)
        goal = frozenset(self.goals)

        # Đo thời gian và bộ nhớ
        start_time = time.time()
        tracemalloc.start()  # Bắt đầu đo bộ nhớ
        path = []
        try:
            if method == 'bfs':
                path = self.solver.bfs(start_state, goal)
            else:
                path = self.solver.a_star(start_state, goal)
        except Exception as e:
            messagebox.showerror('Solver error', str(e))
        
        end_time = time.time()
        current_memory, peak_memory = tracemalloc.get_traced_memory()  # Lấy thông tin bộ nhớ
        tracemalloc.stop()  # Dừng đo bộ nhớ

        # Xử lý kết quả
        if not path:
            messagebox.showinfo('No solution', 
                            f'No solution found by {method.upper()}\n'
                            f'Time: {end_time - start_time:.2f}s\n'
                            f'Memory used: {current_memory / 1024:.2f} KB\n'
                            f'Peak memory: {peak_memory / 1024:.2f} KB')
            self.enable_controls()
            return

        # Cập nhật label với thông tin memory
        self.info_var.set(f'Moves: {self.move_count} | Memory: {current_memory/1024:.1f}KB')

        # Animate đường đi (bỏ qua state đầu vì là state hiện tại)
        for i, state in enumerate(path[1:]):
            # Cập nhật UI trên main thread
            self.state = state
            self.move_count += 1
            # Cập nhật thông tin memory trong quá trình animate
            self.root.after(0, lambda: self.info_var.set(
                f'Moves: {self.move_count} | Memory: {current_memory/1024:.1f}KB (Peak: {peak_memory/1024:.1f}KB)'
            ))
            self.root.after(0, self.draw_map)
            time.sleep(0.12)  # Delay để có hiệu ứng animation

        self.enable_controls()
        messagebox.showinfo('Solved', 
                        f'Solution applied!\n'
                        f'Moves executed: {len(path)-1}\n'
                        f'Solver time: {end_time - start_time:.2f}s\n'
                        f'Memory used: {current_memory / 1024:.2f} KB\n'
                        f'Peak memory: {peak_memory / 1024:.2f} KB')

    def disable_controls(self):
        """Vô hiệu hóa điều khiển trong khi solver đang chạy"""
        self.root.unbind('<Up>')
        self.root.unbind('<Down>')
        self.root.unbind('<Left>')
        self.root.unbind('<Right>')
        self.canvas.unbind('<Button-1>')

    def enable_controls(self):
        """Bật lại điều khiển sau khi solver hoàn thành"""
        self.root.bind('<Up>', lambda e: self.move(0, -1))
        self.root.bind('<Down>', lambda e: self.move(0, 1))
        self.root.bind('<Left>', lambda e: self.move(-1, 0))
        self.root.bind('<Right>', lambda e: self.move(1, 0))
        self.canvas.bind('<Button-1>', self.on_canvas_click)

# ----------------------- Main entry -----------------------

def main():
    """Hàm chính khởi chạy game"""
    root = tk.Tk()
    root.title('Sokoban - Tkinter UI')

    # Tạo ứng dụng với level file
    app = SokobanUI(root, level_file='./testcases/level25.txt')

    root.mainloop()

if __name__ == '__main__':
    main()