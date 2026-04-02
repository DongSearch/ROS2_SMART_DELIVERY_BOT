import rclpy
from rclpy.node import Node
from dr_interfaces.action import MoveTo
from rclpy.action import ActionClient
import threading

class MoveToAction(Node):
    def __init__(self) :
        super().__init__("moveto")
        self.cli_moveto = ActionClient(self,MoveTo,"moveto")
        while not self.cli_moveto.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Waiting for Service")
        
        self.current_goal_handle = None
       
    def input_thread(self):
        while True :
            try :
                tx, ty = map(float,input("set X, Y posiiton ").split())
                self.send_goal(tx,ty)
            except :
                print("invalid input")
        
    def send_goal(self,tx,ty) :
        if self.current_goal_handle is not None :
            self.get_logger().info("Cancel previous goal")
            self.current_goal_handle.cancel_goal_async()

        self.get_logger().info(f"x : {tx} | y : {ty}")
        goal = MoveTo.Goal()
        goal.target_x = tx
        goal.target_y = ty
        goal_future = self.cli_moveto.send_goal_async(goal,self.feedback_callback)
        goal_future.add_done_callback(self.goal_response_callback)
    
    def goal_response_callback(self,future):

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Goal Rejected")
            return
        self.current_goal_handle = goal_handle
        
        self.get_logger().info("Goal Accepted")
        self.result_future = goal_handle.get_result_async()
        self.result_future.add_done_callback(self.result_callback)

    def feedback_callback(self,feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f"remaining distance : {feedback.distance_remaining} m | current position ({feedback.current_x},{feedback.current_y})")
        self.get_logger().info(f"current state : {feedback.state}")


    def result_callback(self,future):
        result = future.result().result
        self.get_logger().info(f"Result : { result.success}")
    
    
def main():
    rclpy.init()
    node = MoveToAction()
    threading.Thread(target = node.input_thread, daemon=True).start()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
        
