#!/bin/bash
set -e

ROS_DISTRO=foxy
ROS_ROOT=/opt/ros/$ROS_DISTRO

ros_env_setup="$ROS_ROOT/install/setup.bash"
echo "sourcing   $ros_env_setup"
source "$ros_env_setup"

echo "ROS_ROOT   $ROS_ROOT"
echo "ROS_DISTRO $ROS_DISTRO"

/usr/sbin/sshd -D

exec "$@"
