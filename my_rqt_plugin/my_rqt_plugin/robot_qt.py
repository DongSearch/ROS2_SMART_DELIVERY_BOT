import os
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QObject
from dr_interfaces.action import MoveTo
from dr_interfaces.srv import Resume, EmergencyStop
import math
import threading
from ament_index_python.packages import get_package_share_directory


class Bridge(QObject):
    feedback_signal = pyqtSignal(float, float, float)
    log_signal = pyqtSignal(str)

class ControlPlugin(Plugin):
    def __init__(self,context):
        super().__init__(context)
        self.setObjectName("ControlPlugin")
        self.widget = QWidget()
        pkg_path = get_package_share_directory('my_rqt_plugin')
        ui_file = os.path.join(pkg_path,'resource','resource/robot_qt.ui')
        loadUi(ui_file,self.widget)
        context.add_widget(self.widget)
        self.bridge = Bridge()
        rclpy.init()
        self.node = ControlNode(self.bridge)
        self.initial_distance = None
        self.target_x = None
        self.target_y = None
        self.widget.btn_send.clicked.connect(self.on_send_goal)
        self.bridge.feedback_signal.connect(self.update_feedback)
        self.widget.btn_emg.clicked.connect(self.node.send_emergency)
        self.widget.btn_re.clicked.connect(self.node.send_resume)
        # self.widget.rbn_res.clicked.connect(self.node.send_addition)
        # self.widget.rbn_pre.clicked.connect(self.node.send_addition)
        # self.widget.rbn_du.clicked.connect(self.node.send_addition)
        # self.widget.rbn_qu.clicked.connect(self.node.send_addition)
        self.widget.qt_plot.setXRange(0, 100)
        self.widget.qt_plot.setYRange(0, 100)
        self.widget.qt_plot.setLabel('left', 'Y')
        self.widget.qt_plot.setLabel('bottom', 'X')
        self.widget.qt_plot.showGrid(x=True, y=True)
        self.bridge.log_signal.connect(self.update_log)

        threading.Thread(target=rclpy.spin,args=(self.node,), daemon=True).start()
    
    def update_log(self,msg):
        self.widget.tb_error.append(msg)

        
    def on_send_goal(self):
        self.widget.prb.setValue(0)
        x = float(self.widget.le_x.text())
        y = float(self.widget.le_y.text())
        self.node.send_goal(x,y)
        self.target_x = x
        self.target_y = y
        self.initial_distance = None
        self.widget.lcd_tx.display(x)
        self.widget.lcd_ty.display(y)
        
    
    
    def update_feedback(self,x,y,dist):
        self.widget.lcd_cx.display(x)
        self.widget.lcd_cy.display(y)
        if self.initial_distance is None and dist is not None:
            self.initial_distance = dist

        if self.initial_distance:
            progress = 1 - (dist/self.initial_distance)
            progress = max(0.0,min(1.0,progress)) # 0~1 clamping
            self.widget.prb.setValue(int(progress * 100))



class ControlNode(Node):
    def __init__(self,bridge):
        super().__init__('rqt_control_node')
        self.bridge = bridge
        # Action Client
        self.action_client = ActionClient(self, MoveTo,"moveto")
        self.cli_resume = self.create_client(Resume,'resume')
        self.cli_emr = self.create_client(EmergencyStop,'emergency')
        self.current_goal_handle = None

    def send_goal(self,x,y):
        if not self.action_client.wait_for_server(timeout_sec=1.0):
            self.bridge.log_signal.emit("[WARN] Action server not available")
            return
        
        #preemption
        if self.current_goal_handle:
            self.current_goal_handle.cancel_goal_async()
        goal = MoveTo.Goal()
        goal.target_x = x
        goal.target_y = y
        future = self.action_client.send_goal_async(goal,self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.bridge.log_signal.emit("[WARN] Goal Rejected")
            return
        
        self.current_goal_handle = goal_handle
        self.bridge.log_signal.emit("[INFO] Goal Accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)
    
    def get_result_callback(self,future):
        result = future.result().result
        self.bridge.log_signal.emit(f"[INFO] Result : {result.success}")

    def feedback_callback(self,feedback_msg):
        feedback = feedback_msg.feedback
        self.bridge.feedback_signal.emit(
            feedback.current_x,
            feedback.current_y,
            feedback.distance_remaining
        )

    def send_resume(self):
        if not self.cli_resume.wait_for_service(1.0):
            self.bridge.log_signal.emit("[WARN] Wait service for Resume")
            return
        req = Resume.Request()
        future = self.cli_resume.call_async(req)
        future.add_done_callback(self.resume_callback)

    def resume_callback(self,future):
        response = future.result()
        self.bridge.log_signal.emit(f"[INFO]Resume : {response.success}")

    def send_emergency(self):
        if not self.cli_emr.wait_for_service(1.0):
            self.bridge.log_signal.emit("[WARN] Wait service for Emergency")
            return
        req = EmergencyStop.Request()
        future = self.cli_emr.call_async(req)
        future.add_done_callback(self.emergency_callback)
    
    def emergency_callback(self,future):
        response = future.result()
        self.bridge.log_signal.emit(f"[INFO] Emergency Stop : {response.success}")


        