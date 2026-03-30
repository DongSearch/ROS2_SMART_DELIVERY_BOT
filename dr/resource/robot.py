import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rclpy.qos import QoSProfile, DurabilityPolicy,ReliabilityPolicy,HistoryPolicy

# set QoS
#  
pub_move_qos = QoSProfile(reliablity = ReliabilityPolicy.RELIABLE,
                          history = HistoryPolicy.KEEP_LAST,
                          depth = 10)

class RobotController(Node):
    def __init__(self) :
        super().__init__("robot_controller")
        self.pub_move = self.create_publisher(Twist,"/cmd_vel",pub_move_qos)
        self.timer = self.create_timer(0.1,self.pub_move_callback)
        self.sub_odom  = self.create_subscription(Odometry,"/odom",self.sub_odom_listener)
        self.sub_laser = self.create_subscription(LaserScan,"/scan",self.sub_laser_listener)


        
