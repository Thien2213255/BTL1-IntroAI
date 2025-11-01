import time
import os
import heapq
import tracemalloc  # ✅ Thêm thư viện đo bộ nhớ

# Biến toàn cục lưu bản đồ game
game_map = []


class GameState:
    """
    Lớp đại diện cho một trạng thái trong game Sokoban
    Mỗi trạng thái bao gồm vị trí người chơi và vị trí các hộp
    """
    
    def __init__(self, player, boxes, cost=0, heuristic=0):
        # Vị trí người chơi dạng tuple (x, y)
        self.player = player
        # Tập hợp các vị trí hộp, dùng frozenset để có thể hash được
        self.boxes = frozenset(boxes)
        # Chi phí từ trạng thái ban đầu đến trạng thái hiện tại (g(n))
        self.cost = cost
        # Ước tính chi phí từ trạng thái hiện tại đến đích (h(n))
        self.heuristic = heuristic

    def __eq__(self, other):
        """So sánh bằng: hai trạng thái bằng nhau nếu người chơi và hộp giống nhau"""
        return self.player == other.player and self.boxes == other.boxes

    def __hash__(self):
        """Hàm băm để có thể lưu trạng thái vào dictionary hoặc set"""
        return hash((self.player, self.boxes))

    def __lt__(self, other):
        """So sánh nhỏ hơn: dùng cho hàng đợi ưu tiên trong A*"""
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)

    def generate_state(self):
        """
        Sinh ra các trạng thái kế tiếp từ trạng thái hiện tại
        Trả về danh sách các trạng thái con hợp lệ
        """
        # 4 hướng di chuyển: Lên, Xuống, Trái, Phải
        moves = [(0, -1), (0, +1), (-1, 0), (+1, 0)]
        child_state = []

        for dx, dy in moves:
            # Lấy vị trí hiện tại của người chơi
            px, py = self.player
            # Tính vị trí mới sau khi di chuyển
            new_player = (px + dx, py + dy)

            # Kiểm tra nếu vị trí mới là tường thì bỏ qua
            if game_map[new_player[1]][new_player[0]] == "#":
                continue

            # TRƯỜNG HỢP 1: Di chuyển không đẩy hộp
            if new_player not in self.boxes:
                # Tạo trạng thái mới với vị trí người chơi mới, hộp giữ nguyên
                child_state.append(GameState(new_player, self.boxes, self.cost + 1))
            
            # TRƯỜNG HỢP 2: Di chuyển đẩy hộp
            else:
                # Tính vị trí mới của hộp sau khi bị đẩy
                new_box = (new_player[0] + dx, new_player[1] + dy)
                
                # Kiểm tra điều kiện đẩy hộp hợp lệ:
                # - Vị trí mới của hộp không phải là tường
                # - Vị trí mới của hộp không trùng với hộp khác
                if game_map[new_box[1]][new_box[0]] != "#" and new_box not in self.boxes:
                    # Tạo tập hợp hộp mới
                    new_box_state = set(self.boxes)
                    # Xóa vị trí hộp cũ (vị trí mà người chơi đang đẩy)
                    new_box_state.remove(new_player)
                    # Thêm vị trí hộp mới
                    new_box_state.add(new_box)
                    # Tạo trạng thái mới với vị trí người chơi và hộp đã cập nhật
                    child_state.append(GameState(new_player, frozenset(new_box_state), self.cost + 1))

        return child_state


class Solver:
    """Lớp chứa các thuật toán giải game Sokoban"""
    
    def bfs(self, start_state, goal):
        """
        Thuật toán Breadth-First Search (Tìm kiếm theo chiều rộng)
        Đảm bảo tìm được đường đi ngắn nhất về số bước
        """
        # Hàng đợi cho BFS (First-In-First-Out)
        q = [start_state]
        # Dictionary lưu trạng thái cha để truy vết đường đi
        parents = {start_state: None}

        while q:
            # Lấy trạng thái đầu tiên từ hàng đợi (FIFO)
            state = q.pop(0)
            
            # Kiểm tra nếu đã đến trạng thái mục tiêu (tất cả hộp ở vị trí đích)
            if state.boxes == goal:
                # Truy vết đường đi từ goal về start
                path = []
                curr = state
                while curr is not None:
                    path.append(curr)
                    curr = parents[curr]
                # Đảo ngược để có đường đi từ start đến goal
                path.reverse()
                return path

            # Duyệt qua tất cả trạng thái con từ trạng thái hiện tại
            for child in state.generate_state():
                # Nếu trạng thái con chưa được visited
                if child not in parents:
                    # Đánh dấu đã visited và lưu trạng thái cha
                    parents[child] = state
                    # Thêm vào hàng đợi
                    q.append(child)
        
        # Không tìm thấy đường đi
        return []

    def a_star(self, start_state, goal):
        """
        Thuật toán A* Search (Tìm kiếm A*)
        Kết hợp chi phí thực tế và heuristic để tìm đường đi tối ưu
        """
        # Hàng đợi ưu tiên cho A* (ưu tiên trạng thái có f(n) nhỏ nhất)
        open_set = []
        heapq.heappush(open_set, (0, start_state))
        
        # Chi phí thực tế từ start đến trạng thái n (g(n))
        g_score = {start_state: 0}
        # Dictionary lưu trạng thái cha
        parents = {start_state: None}
        # Chuyển goal thành set để dễ xử lý
        goal_positions = set(goal)

        while open_set:
            # Lấy trạng thái có f(n) nhỏ nhất từ hàng đợi ưu tiên
            _, current = heapq.heappop(open_set)
            
            # Kiểm tra nếu đã đến trạng thái mục tiêu
            if current.boxes == goal:
                # Truy vết đường đi tương tự BFS
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
                # Chi phí thực tế từ start đến child (g(child))
                tentative_g_score = g_score[current] + 1

                # Nếu tìm thấy đường đi tốt hơn đến child
                if child not in g_score or tentative_g_score < g_score[child]:
                    # Cập nhật chi phí thực tế
                    g_score[child] = tentative_g_score
                    child.cost = tentative_g_score
                    # Lưu trạng thái cha
                    parents[child] = current
                    # Tính f(n) = g(n) + h(n)
                    f_score = tentative_g_score + child.heuristic
                    # Thêm vào hàng đợi ưu tiên
                    heapq.heappush(open_set, (f_score, child))
        
        # Không tìm thấy đường đi
        return []

    def heuristic_func(self, boxes, goals, player):
        """
        Hàm heuristic ước tính chi phí từ trạng thái hiện tại đến goal
        Sử dụng tổ hợp nhiều yếu tố để đánh giá
        """
        total_distance = 0
        box_list = list(boxes)
        goal_list = list(goals)
        
        # 1. Tổng khoảng cách Manhattan từ mỗi hộp đến điểm đích gần nhất
        for box in box_list:
            min_dist = float("inf")
            for goal_pos in goal_list:
                # Khoảng cách Manhattan: |x1-x2| + |y1-y2|
                dist = abs(box[0] - goal_pos[0]) + abs(box[1] - goal_pos[1])
                min_dist = min(min_dist, dist)
            total_distance += min_dist

        # 2. Phạt các trạng thái deadlock (bế tắc)
        deadlock_penalty = 0
        for box in box_list:
            # Chỉ xét deadlock cho hộp chưa ở vị trí đích
            if box not in goals:
                x, y = box
                if self.is_corner_deadlock(x, y):
                    # Phạt nặng các trạng thái deadlock
                    deadlock_penalty += 100

        # 3. Khoảng cách từ người chơi đến hộp gần nhất
        min_player_to_box = float("inf")
        for box in box_list:
            dist = abs(player[0] - box[0]) + abs(player[1] - box[1])
            min_player_to_box = min(min_player_to_box, dist)

        # Kết hợp tất cả yếu tố với trọng số
        return total_distance + deadlock_penalty + min_player_to_box * 0.1

    def is_corner_deadlock(self, x, y):
        """
        Kiểm tra xem hộp có rơi vào trạng thái deadlock ở góc không
        Deadlock góc xảy ra khi hộp nằm ở góc tường
        """
        # Kiểm tra 4 trường hợp góc:
        # - Góc trên-trái, trên-phải, dưới-trái, dưới-phải
        if (game_map[y - 1][x] == "#" and game_map[y][x - 1] == "#") or \
           (game_map[y - 1][x] == "#" and game_map[y][x + 1] == "#") or \
           (game_map[y + 1][x] == "#" and game_map[y][x - 1] == "#") or \
           (game_map[y + 1][x] == "#" and game_map[y][x + 1] == "#"):
            return True
        return False


class Utils:
    """Lớp tiện ích cho việc hiển thị và xử lý giao diện"""
    
    def print_map(self, map_to_print):
        """In bản đồ ra màn hình"""
        for r in map_to_print:
            print("".join(r))
        print()

    def print_path(self, init_player_pos, path):
        """
        Chuyển đổi đường đi thành chuỗi hướng di chuyển
        U: Up, D: Down, L: Left, R: Right
        """
        if not path:
            print("No solution path to print.")
            return

        curr_pos = init_player_pos
        path_str = ""

        # Duyệt qua từng bước di chuyển trong path (bỏ qua trạng thái đầu)
        for state in path[1:]:
            next_pos = state.player
            # Tính vector di chuyển
            dx = next_pos[0] - curr_pos[0]
            dy = next_pos[1] - curr_pos[1]

            # Ánh xạ vector thành ký tự hướng di chuyển
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
        """
        Hiển thị animation đường đi từng bước
        Giúp visualize quá trình giải game
        """
        if not path:
            return
        for state in path:
            self.clear_screen()
            # Tạo bản đồ tạm thời để hiển thị
            temp_map = [list(row) for row in base_map]
            
            # Vẽ các hộp lên bản đồ
            for bx, by in state.boxes:
                # Nếu hộp ở vị trí đích thì vẽ '*', ngược lại vẽ '$'
                temp_map[by][bx] = "*" if (bx, by) in goals else "$"
            
            # Vẽ người chơi lên bản đồ
            px, py = state.player
            # Nếu người chơi ở vị trí đích thì vẽ '+', ngược lại vẽ '@'
            temp_map[py][px] = "+" if (px, py) in goals else "@"
            
            print("Sokoban Solution Animation")
            self.print_map(temp_map)
            # Tạm dừng để người dùng có thể theo dõi
            time.sleep(0.2)


def main():
    """
    Hàm chính của chương trình
    Điều khiển luồng thực thi từ đầu đến cuối
    """
    global game_map
    # Khởi tạo các biến lưu trữ thông tin game
    player = (0, 0)
    boxes = set()
    goals = set()

    # Đọc và parse file bản đồ
    with open("./testcases/level27.txt", "r") as file:
        base_map = []
        # Duyệt qua từng dòng trong file
        for row, line in enumerate(file):
            map_row = []
            # Duyệt qua từng ký tự trong dòng
            for col, char in enumerate(line.rstrip("\n")):
                if char == "@":
                    # '@': Người chơi trên ô trống
                    player = (col, row)
                    map_row.append(" ")
                elif char == "$":
                    # '$': Hộp trên ô trống
                    boxes.add((col, row))
                    map_row.append(" ")
                elif char == ".":
                    # '.': Điểm đích không có hộp
                    goals.add((col, row))
                    map_row.append(".")
                elif char == "*":
                    # '*': Hộp đang ở điểm đích
                    boxes.add((col, row))
                    goals.add((col, row))
                    map_row.append(".")
                elif char == "+":
                    # '+': Người chơi đang ở điểm đích
                    player = (col, row)
                    goals.add((col, row))
                    map_row.append(".")
                else:
                    # Các ký tự khác: tường hoặc khoảng trống
                    map_row.append(char)
            base_map.append(map_row)

    # Gán bản đồ cho biến toàn cục
    game_map = base_map
    # Tạo trạng thái bắt đầu
    start_state = GameState(player, boxes)
    # Chuyển goals thành frozenset để so sánh
    goal = frozenset(goals)

    # Khởi tạo solver và utils
    solver = Solver()
    utils = Utils()

    # Hiển thị trạng thái ban đầu
    print("Initial State:")
    utils.animate([start_state], goals, base_map)

    # Menu lựa chọn thuật toán
    print("1. DFS\n2. BFS\n3. A*")
    n = input("Please choose a solving method: ")

    if n == "2":
        # Giải bằng BFS
        print("\nSolving with BFS...")
        tracemalloc.start()  # ✅ Bắt đầu đo bộ nhớ
        start_time = time.time()
        path = solver.bfs(start_state, goal)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()  # ✅ Dừng đo bộ nhớ

        # Hiển thị kết quả hiệu năng
        print(f"Solver finished in {end_time - start_time:.4f} seconds.")
        print(f"Memory used: {current / 1024:.2f} KB; Peak: {peak / 1024:.2f} KB\n")

        if path:
            # Hiển thị kết quả thành công
            print(f"Solution found! Moves count: {len(path) - 1}")
            utils.print_path(player, path)
            if input("Animate the solution? (y/n): ").lower() == "y":
                utils.animate(path, goals, base_map)
        else:
            print("No solution found.")

    elif n == "3":
        # Giải bằng A* (tương tự BFS)
        print("\nSolving with A*...")
        tracemalloc.start()
        start_time = time.time()
        path = solver.a_star(start_state, goal)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"Solver finished in {end_time - start_time:.4f} seconds.")
        print(f"Memory used: {current / 1024:.2f} KB; Peak: {peak / 1024:.2f} KB\n")

        if path:
            print(f"Solution found! Moves count: {len(path) - 1}")
            utils.print_path(player, path)
            if input("Animate the solution? (y/n): ").lower() == "y":
                utils.animate(path, goals, base_map)
        else:
            print("No solution found.")
    else:
        print("Only BFS and A* are runnable right now.")


if __name__ == "__main__":
    # Điểm bắt đầu của chương trình
    main()