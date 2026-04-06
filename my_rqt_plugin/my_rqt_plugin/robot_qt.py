import os
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QObject
from dr_interfaces.action import MoveTo
from dr_interfaces.srv import Resume, EmergerncyStop
import math
class Bridge(QObject):
    feedback_signal = pyqtSignal(float, float, float)
    log_signal = pyqtSignal(str)

class ControlPlugin(Plugin):
    def __init__(self,context):
        super().__init__(context)
        self.setObjectName("ControlPlugin")
        self.widget = QWidget()
        ui_file = os.path.join(os.path.dirname(__file__), 'resource/robot_qt.ui')
        loadUi(ui_file,self.widget)
        context.add_widget(self.widget)
        self.bridge = Bridge()
        self.node = ControlNode(self.bridge)
        self.widget.btn_send.clicked.connect(self.on_send_goal)
        self.bridge.feedback_signal.connect(self.update_feedback)
        self.widget.btn_emg.clicked.connect(self.node.send_emergency)
        self.widget.btn_re.clicked.connect(self.node.send_resume)
        
    def on_send_goal(self):
        x = float(self.widget.le_x.text())
        y = float(self.widget.le_y.text())
        self.node.send_goal(x,y)
        self.widget.lcd_tx = self.widget.le_x.text()
        self.widget.lcd_ty = self.widget.le_y.text()
        
        
        self.initial_distance = math.sqrt((self.widget.lcd_cx.display(x)-self.widget.lcd_tx)^2 + (self.widget.lcd_cy.display(y)-self.widget.lcd_ty)^2)
    
    def update_feedback(self,x,y,dist):
        self.widget.lcd_cx.display(x)
        self.widget.lcd_cy.display(y)
        self.widget.prb.display(dist/self.initial_distance)



class ControlNode(Node):
    def __init__(self,bridge):
        super().__init__('rqt_control_node')
        self.bridge = bridge
        # Action Client
        self.action_client = ActionClient(self, MoveTo,"moveto")
        self.cli_resume = self.create_client(Resume,'resume')
        self.cli_emr = self.create_client(Resume,'emergency')
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
            self.bridge.log_signal.emit("[WARM] Goal Rejected")
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
        req = EmergerncyStop.Request()
        future = self.cli_emr.call_async(req)
        future.add_done_callback(self.emergency_callback)
    
    def emergency_callback(self,future):
        response = future.result()
        self.bridge.log_signal.emit(f"[INFO] Emergency Stop : {response.success}")


        