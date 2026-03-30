import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy,DurabilityPolicy,HistoryPolicy
import math


pub_move_qos = QoSProfile(
    realiablity = ReliabilityPolicy.RELIABLE,
    durability = DurabilityPolicy.VOLATILE,
    history = HistoryPolicy.KEEP_LAST,
    depth = 10
)
class RobotController(Node):
    def __init__(self):
        super().__init__("robot_contorller")
        self.pub_move_publisher = self.create_publisher(Twist,"/cmd_vel",pub_move_qos)
        self.pub_move_timer = self.create_timer(0.1,self.send_pub_move)
        self.target_x = 0.0
        self.target_y = 0.0
        self.quaternion = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_quaternion = 0.0
        self.sub_odom = self.create_subscription(Odometry,"/odom",self.listener_sub_odom)
        self.sub_scan = self.create_subscription(LaserScan,"/scan",self.listener_sub_scan)



#publish move message
    def send_pub_move(self):
        dx,dtheta = self.calculate_move()
        msg = Twist()
        msg.linear.x = dx
        msg.angular.z = dtheta
        self.get_logger().info(f"move : velocity :{msg.linear.x} , angle : {msg.angular.z} ")
        self.pub_move_publisher.publish(msg)
        
# calculate how much and where the robot should move
    def calculate_move(self):
        diff_distance = math.sqrt((self.target_x - self.current_x)**2 + (self.target_y - self.self.current_y)**2)
        diff_quaternion = math.atan(self.target_y/self.target_x) - self.current_quaternion

        return x, theta
    
    def avoid_obstacle(self):
        pass

    def listener_sub_odom(self,msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        self.current_quaternion = msg.pose.pose.orientation.z

    def listener_sub_scan(self,msg):

