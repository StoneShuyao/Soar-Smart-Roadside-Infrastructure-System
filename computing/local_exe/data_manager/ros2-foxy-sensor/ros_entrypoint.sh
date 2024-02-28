#!/bin/bash
set -e

ROS_DISTRO=foxy
ROS_ROOT=/opt/ros/$ROS_DISTRO

ros_env_setup="$ROS_ROOT/install/setup.bash"
echo "sourcing   $ros_env_setup"
source "$ros_env_setup"
source "/root/.bashrc"
source "/img_publisher/install/setup.bash"
source "/thermal_pub/install/setup.bash"
source "/sensor_subscriber/install/setup.bash"

echo "ROS_ROOT   $ROS_ROOT"
echo "ROS_DISTRO $ROS_DISTRO"

# Start scheduled task
/usr/sbin/cron

/usr/sbin/sshd -D

exec "$@"
