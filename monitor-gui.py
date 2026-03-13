import sys
import requests
import time
import json
import os
import ipaddress  # IP 검증을 위한 라이브러리 추가
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QColor

# 설정 파일 경로
DB_FILE = "servers.json"

class Worker(QThread):
    """서버 상태를 체크하고 결과를 메인 UI로 전달하는 스레드"""
    # (아이템객체, IP, Port, Status, Time, Data, 변경여부)
    result_signal = pyqtSignal(object, str, str, str, str, str, bool)

    def __init__(self, item, ip, port, parent=None):
        super().__init__(parent)
        self.item, self.ip, self.port = item, ip, port
        self.interval = 1.0
        self.is_running = True
        self.last_content = ""

    def run(self):
        url = f"http://{self.ip}:{self.port}"
        while self.is_running:
            try:
                response = requests.get(url, timeout=2)
                status = str(response.status_code)
                latency = f"{response.elapsed.total_seconds() * 1000:.2f}ms"
                content = response.text.replace('\n', ' ').replace('\r', '').strip()[:50]
                
                # 데이터 변경 감지 로직
                is_changed = False
                if self.last_content and self.last_content != content:
                    is_changed = True
                self.last_content = content
                
            except Exception:
                status, latency, content, is_changed = "DOWN", "---", "Connection Fail", False

            if self.is_running:
                self.result_signal.emit(self.item, self.ip, self.port, status, latency, content, is_changed)
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False

class MonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker_map = {}
        self.current_interval = 1.0
        self.init_ui()
        self.load_from_file()

    def init_ui(self):
        self.setWindowTitle("서버 모니터링 시스템")
        self.resize(1050, 450)
        
        # 화면 중앙 배치
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- 상단 컨트롤 영역 ---
        top_layout = QHBoxLayout()
        self.input_ip = QLineEdit(); self.input_ip.setPlaceholderText("IP (ex: 1.1.1.1)")
        self.input_port = QLineEdit(); self.input_port.setPlaceholderText("Port")
        self.input_port.setFixedWidth(60)
        
        btn_add = QPushButton("추가"); btn_add.setFixedWidth(50)
        btn_add.clicked.connect(self.handle_add_server)
        
        btn_del = QPushButton("삭제"); btn_del.setFixedWidth(50)
        btn_del.setStyleSheet("background-color: #ffebee; color: red; font-weight: bold;")
        btn_del.clicked.connect(self.delete_selected_server)

        self.lbl_interval = QLabel(f"주기: {self.current_interval}s")
        btn_set_int = QPushButton("간격"); btn_set_int.setFixedWidth(50)
        menu = QMenu(self); [menu.addAction(f"{s}s", lambda v=s: self.change_interval(v)) for s in [0.5, 1.0, 2.0]]
        btn_set_int.setMenu(menu)

        top_layout.addWidget(QLabel("IP:")); top_layout.addWidget(self.input_ip)
        top_layout.addWidget(QLabel("Port:")); top_layout.addWidget(self.input_port)
        top_layout.addWidget(btn_add); top_layout.addWidget(btn_del)
        top_layout.addSpacing(15); top_layout.addWidget(self.lbl_interval); top_layout.addWidget(btn_set_int)
        layout.addLayout(top_layout)

        # --- 트리 위젯 ---
        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["No", "IP Address", "Port", "Status", "Response Time", "Data (HTML/Raw)"])
        self.tree.setFont(QFont("Consolas", 9))
        
        self.tree.setStyleSheet("""
            QTreeWidget::item { 
                height: 25px; 
                padding: 0px; 
                margin: 0px;
                border-bottom: 1px solid #f0f0f0; 
            }
            QTreeWidget::item:hover { background-color: #f8f9fa; }
            QTreeWidget::item:selected { background-color: #e3f2fd; color: #000000; outline: none; }
            QHeaderView::section { padding-left: 4px; background-color: #f8f9fa; border: 1px solid #dee2e6; }
        """)
        
        self.tree.setColumnWidth(0, 40)
        self.tree.setColumnWidth(1, 140)
        self.tree.setColumnWidth(2, 60)
        self.tree.setColumnWidth(3, 70)
        self.tree.setColumnWidth(4, 110)
        self.tree.header().setStretchLastSection(True)
        self.tree.setRootIsDecorated(False)
        
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.model().rowsMoved.connect(self.reorder_numbers)
        
        layout.addWidget(self.tree)
        QShortcut(Qt.Key_Delete, self.tree).activated.connect(self.delete_selected_server)

    def reorder_numbers(self):
        """리스트 순번에 맞춰 번호 재매기기(가운데 정렬) 및 파일 동기화"""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setText(0, str(i + 1))
            item.setTextAlignment(0, Qt.AlignCenter)
        self.update_json_file()

    def load_from_file(self):
        if not os.path.exists(DB_FILE):
            initial = [("172.16.1.1", "80"), ("172.16.1.2", "8080"), ("172.16.1.3", "8080"),
                       ("172.16.1.6", "80"), ("172.16.1.4", "9090"), ("172.16.1.5", "9090")]
            self.save_to_file(initial)
        
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for ip, port in data: self.create_worker(ip, port)
        self.reorder_numbers()

    def save_to_file(self, server_list):
        with open(DB_FILE, "w") as f: json.dump(server_list, f, indent=4)

    def update_json_file(self):
        current_data = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            w = self.worker_map.get(id(item))
            if w: current_data.append((w.ip, w.port))
        self.save_to_file(current_data)

    def validate_input(self, ip, port):
        """ipaddress 라이브러리를 사용한 강력한 유효성 검사"""
        try:
            ipaddress.ip_address(ip) # 유효하지 않으면 ValueError 발생
        except ValueError:
            QMessageBox.critical(self, "오류", f"'{ip}'는 유효한 IP 주소가 아닙니다.\n(예: 192.168.0.1)")
            return False
        
        if not (port.isdigit() and 1 <= int(port) <= 65535):
            QMessageBox.critical(self, "오류", "Port(1-65535)를 확인하세요.")
            return False
        return True

    def handle_add_server(self):
        ip, port = self.input_ip.text().strip(), self.input_port.text().strip()
        if self.validate_input(ip, port):
            self.create_worker(ip, port)
            self.reorder_numbers()
            self.input_ip.clear(); self.input_port.clear()

    def create_worker(self, ip, port):
        item = QTreeWidgetItem(["", ip, port, "Wait...", "...", "..."])
        item.setTextAlignment(0, Qt.AlignCenter)
        self.tree.addTopLevelItem(item)
        worker = Worker(item, ip, port)
        worker.interval = self.current_interval
        worker.result_signal.connect(self.update_display)
        self.worker_map[id(item)] = worker
        worker.start()

    def delete_selected_server(self):
        item = self.tree.currentItem()
        if item:
            item_id = id(item)
            if item_id in self.worker_map:
                self.worker_map[item_id].stop()
                del self.worker_map[item_id]
            self.tree.invisibleRootItem().removeChild(item)
            self.reorder_numbers()

    @pyqtSlot(object, str, str, str, str, str, bool)
    def update_display(self, item, ip, port, status, time, data, is_changed):
        if id(item) in self.worker_map:
            item.setText(3, status)
            item.setText(4, time)
            item.setText(5, data)
            
            # 기본 색상 설정
            base_color = QColor(Qt.red) if status == "DOWN" else QColor(Qt.darkGreen)
            
            for i in range(6):
                # 데이터가 변경된 경우 Data 컬럼(Index 5)만 파란색 및 굵게 표시
                if i == 5 and is_changed:
                    item.setForeground(i, QColor(Qt.blue))
                    item.setFont(i, QFont("Consolas", 9, QFont.Bold))
                else:
                    item.setForeground(i, base_color)
                    item.setFont(i, QFont("Consolas", 9))

    def change_interval(self, val):
        self.current_interval = val
        self.lbl_interval.setText(f"주기: {val}s")
        for worker in self.worker_map.values(): worker.interval = val

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorApp(); window.show()
    sys.exit(app.exec_())