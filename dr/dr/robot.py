import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy,DurabilityPolicy,HistoryPolicy
import math
from tf_transformations import euler_from_quaternion

pub_move_qos = QoSProfile(
    reliability = ReliabilityPolicy.RELIABLE,
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
        self.current_yaw = 0.0
        self.obj_list = []
        self.angles = 0.0
        self.sub_odom = self.create_subscription(Odometry,"/odom",self.listener_sub_odom,10)
        self.sub_scan = self.create_subscription(LaserScan,"/scan",self.listener_sub_scan,10)



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


