# ROS2_SMART_DELIVERY_BOT
Delivery bot using ROS 2 and Turtlebot3

# Jounrey
1. Test Gazebo
```
gazebo --verbose -s libgazebo_ros_factory.so # run gazebo 

ros2 run gazebo_ros spawn_entity.py   -entity waffle   -file /opt/ros/humble/share/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf  #spawn turtlebot3 

ros2 run turtlebot3_teleop teleop_keyboard # move turtlebot3

```
