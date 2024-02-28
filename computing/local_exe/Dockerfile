FROM testbed-master:5000/ros2-sensor:foxy-desktop-l4t-r32.6.1

ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# Python basic requirements
RUN apt-get update && \
    apt-get install -y python3-pip libopenblas-base libopenmpi-dev && \
    apt-get install -y libblas-dev libatlas3-base liblapack-dev libtesseract-dev && \
    apt-get install -y gfortran && \
    apt-get install -y ninja-build && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    pip3 install --upgrade Cython && \
    pip3 install numpy==1.19.4 && \
    pip3 install --upgrade configparser sysv-ipc scipy colorama scikit-build 

# Install pytorch and torchvision
RUN apt-get update && \
    apt-get install libopenblas-base libopenmpi-dev libomp-dev -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean
RUN wget https://nvidia.box.com/shared/static/h1z9sw4bb1ybi0rm3tu8qdj8hs05ljbm.whl -O torch-1.9.0-cp36-cp36m-linux_aarch64.whl && \
    pip3 install ./torch-1.9.0-cp36-cp36m-linux_aarch64.whl && \
    rm ./torch-1.9.0-cp36-cp36m-linux_aarch64.whl
RUN apt-get update && \ 
    apt-get install libjpeg-dev zlib1g-dev libpython3-dev libavcodec-dev libavformat-dev libswscale-dev -y && \
    apt-get clean
RUN git clone --branch v0.10.0 https://github.com/pytorch/vision torchvision && \
    cd torchvision  && \
    export BUILD_VERSION=0.10.0 && \
    python3 setup.py bdist_wheel && \
    pip3 install dist/torchvision-0.10.0-cp36-cp36m-linux_aarch64.whl && \
    cd .. && \
    rm -r torchvision


# # Lidar preprocessing related
# # Install llvm
RUN apt-get update && \
    apt-get install -y llvm-9 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# # RUN wget https://github.com/llvm/llvm-project/releases/download/llvmorg-9.0.1/llvm-9.0.1.src.tar.xz && \
# #     tar -xvf llvm-9.0.1.src.tar.xz && \
# #     cd llvm-9.0.1.src && \
# #     mkdir llvm_build_dir && \
# #     cd llvm_build_dir/ && \
# #     cmake ../ -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="ARM;X86;AArch64" && \
# #     make && \
# #     make install && \
# #     cd ../.. && \
# #     rm -r llvm-9.0.1.src

# Install llvmlite
RUN LLVM_CONFIG=/usr/lib/llvm-9/bin/llvm-config pip3 install llvmlite==0.36.0
# Update TBB
RUN git clone https://github.com/wjakob/tbb.git && \
    cd tbb/build && \
    cmake .. && \
    make -j4 && \
    make install && \
    cd ../.. && \
    rm -r tbb
# Install numba
RUN pip3 install numba==0.53.0

# # Install Open3d-ml
# RUN git clone -b v3.3.4 https://github.com/matplotlib/matplotlib.git && \
#     cd matplotlib && \
#     mkdir build && \
#     cd build && \
#     wget https://downloads.sourceforge.net/project/freetype/freetype2/2.6.1/freetype-2.6.1.tar.gz && \
#     tar xvzf freetype-2.6.1.tar.gz && \
#     cd .. && \
#     python3 setup.py bdist_wheel && \
#     pip3 install dist/matplotlib-3.3.4-cp36-cp36m-linux_aarch64.whl && \
#     cd .. && \
#     rm -r matplotlib
# RUN pip3 install yapf tensorboard && \
#     pip3 install --ignore-installed PyYAML && \
#     git clone -b v0.15.1 https://github.com/isl-org/Open3D && \
#     cd Open3D && \
#     sed -i '/GIT_REPOSITORY "${OPEN3D_ML_ROOT}"/a\GIT_TAG "v0.15.1"' cpp/pybind/CMakeLists.txt && \
#     mkdir build && \
#     cd build && \
#     git clone -b v0.15.1 https://github.com/isl-org/Open3D-ML open3d_ml --recurse && \
#     export PATH=/usr/local/cuda/bin:$PATH && \
#     cmake -DPYTHON_EXECUTABLE=$(which python3) \
#           -DBUILD_GUI=OFF \
#           -DGLIBCXX_USE_CXX11_ABI=ON \
#           -DBUILD_PYTORCH_OPS=ON \
#           -DBUNDLE_OPEN3D_ML=ON \
#           -DCMAKE_BUILD_TYPE=Release \
#           -DUSE_BLAS=ON \
#           -DUSE_SYSTEM_BLAS=ON \
#           -DOPEN3D_ML_ROOT=./open3d_ml \
#           -DBUILD_CUDA_MODULE=ON .. && \
#     make && \
#     make pip-package && \
#     pip3 install lib/python_package/pip_package/open3d-0.15.1+ed30e3b61-cp36-cp36m-linux_aarch64.whl 

# # Install OpenPCDet
# RUN sed -i "s/self.use_ninja = kwargs.get('use_ninja', True)/self.use_ninja = kwargs.get('use_ninja', False)/g" /usr/local/lib/python3.6/dist-packages/torch/utils/cpp_extension.py
# RUN git clone -b v0.5.2 https://github.com/open-mmlab/OpenPCDet.git && \
#     cd OpenPCDet && \
#     python3 setup.py bdist_wheel && \
#     pip3 install dist/pcdet-0.5.2+b6fbf07-cp36-cp36m-linux_aarch64.whl && \
#     cd .. && \
#     rm -r OpenPCDet
# RUN sed -i "s/self.use_ninja = kwargs.get('use_ninja', False)/self.use_ninja = kwargs.get('use_ninja', True)/g" /usr/local/lib/python3.6/dist-packages/torch/utils/cpp_extension.py

# Model inference related
# Install pycuda from source
# ENV PATH="/usr/local/cuda/bin:${PATH}"
# ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
# RUN echo "$PATH" && echo "$LD_LIBRARY_PATH"
# RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
# RUN pip3 install --upgrade setuptools && pip3 install pycuda --verbose

# Install Open3D with Open3d-ml

RUN git clone -b v2022.1 https://github.com/inducer/pycuda.git --recurse && \
    cd pycuda && \
    python3 configure.py && \
    python3 setup.py bdist_wheel && \
    pip3 install dist/pycuda-2022.1-cp36-cp36m-linux_aarch64.whl && \
    cd .. && \
    rm -r pycuda

# Install preprocessing
COPY ./pre_processing /pre_processing

# Install inference
COPY ./local_scheduler /local_scheduler
RUN cd /local_scheduler/model/plugins/pointpillar_scatter_plugin/build && \
    cmake .. &&\
    make -j4 && \
    cp libpillarScatter.so /local_scheduler/model/plugins/libpillarScatter.so && \
    rm -r /local_scheduler/model/plugins/pointpillar_scatter_plugin

# Install postprocessing
COPY ./post_processing /post_processing
RUN cd /post_processing/IoU3D && \
    python3 setup.py bdist_wheel && \
    pip3 install dist/iou3d_nms_cuda-0.5.2-cp36-cp36m-linux_aarch64.whl && \
    rm -r /post_processing/IoU3D