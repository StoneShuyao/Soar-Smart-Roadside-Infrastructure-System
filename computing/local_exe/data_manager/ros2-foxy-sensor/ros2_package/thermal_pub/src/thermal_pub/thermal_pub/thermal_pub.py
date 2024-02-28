# Copyright 2017 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# from examples_rclpy_executors.listener import Listener
import socket

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import CompressedImage


class IPCamera(Node):
    """Publish messages to a topic using two publishers at different rates."""

    def __init__(self, nodename, img_path):
        super().__init__(nodename)

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,
            history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST,
            depth=1
        )

        hostname = socket.gethostname()
        topic = "/" + hostname + "/thermal_1"
        self.topic = topic.replace("-", "_")
        self.frame = cv2.imread(img_path, cv2.IMREAD_COLOR)

        # Used to convert between ROS and OpenCV images
        self.br = CvBridge()

        self.publisher = self.create_publisher(CompressedImage, self.topic, qos_profile)

        # # This type of callback group only allows one callback to be executed at a time
        self.group = ReentrantCallbackGroup()
        # Pass the group as a parameter to give it control over the execution of the timer callback
        timer_period = 0.05

        self.timer = self.create_timer(timer_period, self.timer_callback, callback_group=self.group)
        # self.timer2 = self.create_timer(0.5, self.timer_callback, callback_group=self.group)

    def timer_callback(self):
        msg = self.br.cv2_to_compressed_imgmsg(self.frame)
        msg.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    hostname = socket.gethostname()
    nodename = hostname + "_IPThermal_1"
    nodename = nodename.replace("-", "_")
    img_path = "/thermal_pub/FLIR_video_04211.jpeg"

    image_publisher = IPCamera(nodename, img_path)
    executor = MultiThreadedExecutor()
    # signal.signal(signal.SIGINT, sensor_signal_handler(sensor_subscriber))
    # signal.signal(signal.SIGTERM, sensor_signal_handler(sensor_subscriber))

    executor.add_node(image_publisher)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        image_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
