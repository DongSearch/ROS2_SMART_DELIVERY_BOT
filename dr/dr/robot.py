import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy,DurabilityPolicy,HistoryPolicy
import math
from tf_transformations import euler_from_quaternion
from dr_interfaces.srv import Resume,EmergencyStop
from dr_interfaces.action import MoveTo
from rclpy.action import ActionServer
import asyncio



pub_move_qos = QoSProfile(
    reliability = ReliabilityPolicy.RELIABLE,
    durability = DurabilityPolicy.VOLATILE,
    history = HistoryPolicy.KEEP_LAST,
    depth = 10
)

class RobotController(Node):
    def __init__(self):
        super().__init__("robot_controller")
        self.pub_move_publisher = self.create_publisher(Twist,"/cmd_vel",pub_move_qos)
        self.pub_move_timer = self.create_timer(0.1,self.send_pub_move)
        self.target_x = 0.0
        self.target_y = 0.0
        self.quaternion = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.obj_list = []
        self.angles = 0.0
        self.move_flag = True
        self.sub_odom = self.create_subscription(Odometry,"/odom",self.listener_sub_odom,10)
        self.sub_scan = self.create_subscription(LaserScan,"/scan",self.listener_sub_scan,10)
        self.emer_srv = self.create_service(EmergencyStop,"emg_stop",self.emer_srv_listener)
        self.resume_srv = self.create_service(Resume,"resume",self.resume_srv_listener)
        self.action_moveto = ActionServer(self,MoveTo,"moveto", execute_callback=self.execute_callback)

    def emer_srv_listener(self,request,response):
        self.move_flag = False
        self.get_logger().info("Emergency Stop from service")
        response.success = True
        response.message = "Stop command accpeted"
        return response

    def resume_srv_listener(self,request,response):
        self.move_flag = True
        self.get_logger().info("Resume from service")
        response.success = True
        response.message = "Resume command accpeted"
        return response

    async def execute_callback(self, goal_handle):
        self.get_logger().info("Received MoveTo goal")
        self.target_x = goal_handle.request.target_x
        self.target_y = goal_handle.request.target_y

        while True :
            dx = self.target_x - self.current_x
            dy = self.target_y - self.current_y
            dist = math.sqrt(dx**2 + dy**2)

            feedback_msg = MoveTo.Feedback()
            feedback_msg.distance_remaining = dist
            feedback_msg.current_x = self.current_x
            feedback_msg.current_y = self.current_y
            feedback_msg.state = "moving"
            
            goal_handle.publish_feedback(feedback_msg)

            if dist < 0.1:
                # avoid to move after arriving to goal
                self.target_x = self.current_x
                self.target_y = self.current_y
                break

            await asyncio.sleep(0.1)
        goal_handle.succeed()
        result = MoveTo.Result()
        result.success = True
        return result
            


#publish move message
    def send_pub_move(self):
        dx,dtheta = self.calculate_move()
        msg = Twist()
        if self.move_flag : 
            msg.linear.x = dx
            msg.angular.z = dtheta
            self.get_logger().info(f"move : velocity :{msg.linear.x} , angle : {msg.angular.z} ")
        else :
            msg.linear.x = 0
            msg.angular.z = 0

        self.pub_move_publisher.publish(msg)
        
# calculate how much and where the robot should move
    def calculate_move(self):
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        diff_distance = math.sqrt(dx**2 + dy**2)
        # atan -> ratio: estimate angle(1,1 = -1,-1), atan2 -> coordinate : 360 degree
        diff_angle = self.normalize_angle(math.atan2(dy, dx) - self.current_yaw)
        # knowing object in minimum distance is enough 
        min_dist = min(self.obj_list) if self.obj_list else float('inf')
        if min_dist < 0.5 :
            x,theta = self.avoid_obstacle()
        else :
            if abs(diff_angle) > 0.2:
                x=0.0
                theta = diff_angle
            else :
                x,theta = diff_distance, diff_angle

        return min(x,0.2), max(min(theta,1.0),-1.0) # limit speed
    
    def normalize_angle(self,angle):
        while angle > math.pi :
            angle -= 2 * math.pi
        while angle < - math.pi :
            angle += 2 * math.pi
        return angle
    
    def avoid_obstacle(self):
        front = min(self.obj_list[:10] + self.obj_list[-10:])
        left = min(self.obj_list[30:60])
        right = min(self.obj_list[-60:-30])
        x = 0
        if front < 0.5:
            if left > right :
                theta = 0.5
            else : 
                theta = -0.5
        else : 
            x = 0.1
            theta = 0
      
        return x,theta

    def listener_sub_odom(self,msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        # quaternion -> euler angles 
        _,_, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.current_yaw =  yaw

    def listener_sub_scan(self,msg):
        self.obj_list = msg.ranges
        self.angles = msg.angle_min

def main():
    rclpy.init()
    node = RobotController()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    
if __name__ =="__main__":
    main()
