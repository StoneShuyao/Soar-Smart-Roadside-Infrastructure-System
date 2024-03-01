FROM testbed-master:5000/ros2:foxy-desktop-l4t-r32.6.1

RUN apt-get update && \
    apt-get install -y openssh-server && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN pip3 install sysv-ipc

RUN mkdir /var/run/sshd

RUN echo 'root:root' | chpasswd
RUN sed -i 's/#\?PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN sed -i 's/${ROS_ROOT}/\/opt\/ros\/foxy/g' /root/.bashrc

EXPOSE 22
COPY ./ros_entrypoint.sh /ros_entrypoint.sh
