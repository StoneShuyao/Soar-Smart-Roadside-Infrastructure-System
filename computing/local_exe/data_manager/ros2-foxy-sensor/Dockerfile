FROM testbed-master:5000/ros2-ssh:foxy-desktop-l4t-r32.6.1

ARG ROS_PKG=desktop
ENV ROS_DISTRO=foxy
ENV ROS_ROOT=/opt/ros/${ROS_DISTRO}


ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

ENV TimeZone=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TimeZone /etc/localtime && echo $TimeZone > /etc/timezone

WORKDIR /


# Install OpenCV (with CUDA)
ARG OPENCV_URL=https://nvidia.box.com/shared/static/5v89u6g5rb62fpz4lh0rz531ajo2t5ef.gz
ARG OPENCV_DEB=OpenCV-4.5.0-aarch64.tar.gz

RUN apt-get purge -y '*opencv*' || echo "previous OpenCV installation not found" && \
    mkdir opencv && \
    cd opencv && \
    wget --quiet --show-progress --progress=bar:force:noscroll --no-check-certificate ${OPENCV_URL} -O ${OPENCV_DEB} && \
    tar -xzvf ${OPENCV_DEB} && \
    dpkg -i --force-depends *.deb && \
    apt-get update && \
    apt-get install -y -f --no-install-recommends && \
    dpkg -i *.deb && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    cd ../ && \
    rm -rf opencv && \
    cp -r /usr/include/opencv4 /usr/local/include/opencv4 && \
    cp -r /usr/lib/python3.6/dist-packages/cv2 /usr/local/lib/python3.6/dist-packages/cv2


# Install img publisher
COPY ./ros2_package/img_publisher /img_publisher
RUN source $ROS_ROOT/install/setup.bash && \
    cd /img_publisher && \
    apt-get update && \
    colcon build --symlink-install && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN echo "source /img_publisher/install/setup.bash" >> /root/.bashrc

# Install thermal publisher
COPY ./ros2_package/thermal_pub /thermal_pub
RUN source $ROS_ROOT/install/setup.bash && \
    cd /thermal_pub && \
    apt-get update && \
    colcon build --symlink-install && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN echo "source /thermal_pub/install/setup.bash" >> /root/.bashrc


# Install topic subscriber
COPY ./sensor_subscriber /sensor_subscriber
RUN pip3 install transforms3d && \
    source $ROS_ROOT/install/setup.bash && \
    cd /sensor_subscriber && \
    colcon build

RUN echo "source /sensor_subscriber/install/setup.bash" >> /root/.bashrc

# Install ros2 monitor and set scheduled tasks
COPY ./ros2_monitor /ros2_monitor
RUN pip3 install --upgrade pip && \
    pip3 install psutil && \
    apt-get update && \
    apt-get install sshpass cron -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    echo "*/5 * * * * . /ros2_monitor/env.sh; /usr/bin/python3 /ros2_monitor/ros2_monitor.py" >> temp.cron && \
    crontab temp.cron && \
    rm -rf temp.cron

RUN mkdir /config
RUN sed -i 's/#\?#Port 22/Port 2202/' /etc/ssh/sshd_config
RUN echo "export ROS_DOMAIN_ID=1" >> /root/.bashrc


COPY ./ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]