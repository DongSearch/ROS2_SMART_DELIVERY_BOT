import rclpy
from rclpy.node import Node
from dr_interfaces.srv import EmergencyStop



class EmergencyService(Node):
    def __init__(self) :
        super().__init__("emergency_stop")
        self.cli_stop = self.create_client(EmergencyStop,"emg_stop")
        while not self.cli_stop.wait_for_service(1.0) :
            self.get_logger().info("Wating Server")
        
        self.req = EmergencyStop.Request()
        self.send_request()
    
    def send_request(self):
        self.future = self.cli_stop.call_async(self.req)
        self.future.add_done_callback(self.callback)

    def callback(self,future):
        response = future.result()
       
        if response.success :
            self.get_logger().info(f"Success Stop ")
        else :
            self.get_logger().warn(f"Fail Stop ")
            self.get_logger().warn(response.message)

    
def main():
    rclpy.init()
    node = EmergencyService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
        
