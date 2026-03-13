import sys
import requests
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont

class Worker(QThread):
    result_signal = pyqtSignal(object, str)

    def __init__(self, item, ip, port, parent=None):
        super().__init__(parent)
        self.item = item
        self.ip = ip
        self.port = port
        self.interval = 1.0
        self.is_running = True

    def run(self):
        url = f"http://{self.ip}:{self.port}"
        while self.is_running:
            try:
                response = requests.get(url, timeout=2)
                status = response.status_code
                latency = response.elapsed.total_seconds() * 1000
                content = response.text.replace('\n', ' ').replace('\r', '').strip()[:40]
                result = f"IP: {self.ip:<15} | Port: {self.port:<5} | Status: {status} | Time: {latency:7.2f}ms | Data: {content}..."
            except Exception:
                result = f"IP: {self.ip:<15} | Port: {self.port:<5} | Status: DOWN | Time:  ---.--ms | Error: Connection Fail"

            if self.is_running:
                self.result_signal.emit(self.item, result)
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False

class MonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # id(item)을 키로 사용하는 딕셔너리
        self.worker_map = {} 
        self.current_interval = 1.0
        self.init_ui()
        
        # 프로그램 시작 시 6개 서버를 초기 리스트로 등록 (삭제 가능)
        initial_setup = [
            ("172.16.1.1", "80"), ("172.16.1.2", "8080"), ("172.16.1.3", "8080"),
            ("172.16.1.6", "80"), ("172.16.1.4", "9090"), ("172.16.1.5", "9090")
        ]
        for ip, port in initial_setup:
            self.create_worker(ip, port)

    def init_ui(self):
        self.setWindowTitle("Server Monitoring System v5.0")
        self.setGeometry(100, 100, 1100, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- 상단 컨트롤 ---
        top_layout = QHBoxLayout()
        self.input_ip = QLineEdit(); self.input_ip.setPlaceholderText("IP 주소")
        self.input_port = QLineEdit(); self.input_port.setPlaceholderText("포트")
        self.input_port.setFixedWidth(80)
        
        btn_add = QPushButton("서버 추가")
        btn_add.clicked.connect(self.add_new_server)
        
        btn_del = QPushButton("선택 서버 삭제")
        btn_del.setStyleSheet("background-color: #ffcccc; font-weight: bold;")
        btn_del.clicked.connect(self.delete_selected_server)

        self.lbl_interval = QLabel(f"주기: {self.current_interval}s")
        btn_set_int = QPushButton("간격 변경")
        menu = QMenu(self)
        for s in [0.5, 1.0, 2.0]:
            menu.addAction(f"{s}s", lambda v=s: self.change_interval(v))
        btn_set_int.setMenu(menu)

        top_layout.addWidget(self.input_ip)
        top_layout.addWidget(self.input_port)
        top_layout.addWidget(btn_add)
        top_layout.addWidget(btn_del)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_interval)
        top_layout.addWidget(btn_set_int)
        layout.addLayout(top_layout)

        # --- 리스트 위젯 ---
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Consolas", 10))
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        layout.addWidget(self.list_widget)

        # Delete 키 단축키
        QShortcut(Qt.Key_Delete, self.list_widget).activated.connect(self.delete_selected_server)

    def add_new_server(self):
        ip, port = self.input_ip.text().strip(), self.input_port.text().strip()
        if ip and port:
            self.create_worker(ip, port)
            self.input_ip.clear(); self.input_port.clear()

    def create_worker(self, ip, port):
        item = QListWidgetItem(f"IP: {ip:<15} | Port: {port:<5} | Connecting...")
        self.list_widget.addItem(item)
        
        worker = Worker(item, ip, port)
        worker.interval = self.current_interval
        worker.result_signal.connect(self.update_display)
        
        self.worker_map[id(item)] = worker
        worker.start()

    def delete_selected_server(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            item_id = id(current_item)
            if item_id in self.worker_map:
                worker = self.worker_map[item_id]
                worker.stop()
                worker.wait(500) # 스레드 안전 종료 대기
                del self.worker_map[item_id]
            
            row = self.list_widget.row(current_item)
            self.list_widget.takeItem(row)

    @pyqtSlot(object, str)
    def update_display(self, item, text):
        if id(item) in self.worker_map:
            item.setText(text)
            item.setForeground(Qt.red if "DOWN" in text else Qt.darkGreen)

    def change_interval(self, val):
        self.current_interval = val
        self.lbl_interval.setText(f"주기: {val}s")
        for worker in self.worker_map.values():
            worker.interval = val

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorApp()
    window.show()
    sys.exit(app.exec_())