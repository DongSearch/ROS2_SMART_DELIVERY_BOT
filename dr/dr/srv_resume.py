import rclpy
from rclpy.node import Node
from dr_interfaces.srv import Resume



class ResumeService(Node):
    def __init__(self) :
        super().__init__("resume")
        self.cli_resume = self.create_client(Resume,"resume")
        while not self.cli_resume.wait_for_service(1.0):
            self.get_logger().info("Waiting for Server")
        
        self.req = Resume.Request()
        self.send_request()

    
    def send_request(self):
        self.future = self.cli_resume.call_async(self.req)
        self.future.add_done_callback(self.callback)

    def callback(self,future):
        response = future.result()

        if response.success :
            self.get_logger().info(f"Success Resume")
        else :
            self.get_logger().warn(f"Fail Stop")
            self.get_logger().warn(response.message)


    
def main():
    rclpy.init()
    node = ResumeService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
        
