import time
import os
import numpy as np
import pycuda.driver as cuda
import tensorrt as trt
import ctypes

from pathlib import Path

path = Path(__file__).parent.absolute()

ctypes.CDLL(os.path.join(path, "plugins/libpillarScatter.so"), mode=ctypes.RTLD_GLOBAL)

# Simple helper data class that's raw_data little nicer to use than raw_data 2-tuple.
class HostDeviceMem(object):
    def __init__(self, host_mem, device_mem):
        self.host = host_mem
        self.device = device_mem

    def __str__(self):
        return "Host:\n" + str(self.host) + "\nDevice:\n" + str(self.device)

    def __repr__(self):
        return self.__str__()


def allocate_buffers(engine, max_batch_size=16):
    inputs = []
    outputs = []
    bindings = []
    stream = cuda.Stream()
    for binding in engine:
        dims = engine.get_binding_shape(binding)
        if dims[0] == -1:
            assert (max_batch_size is not None)
            dims[0] = max_batch_size

        size = trt.volume(dims) * engine.max_batch_size
        dtype = trt.nptype(engine.get_binding_dtype(binding))

        # Allocate host and device buffers
        host_mem = cuda.pagelocked_empty(size, dtype)
        device_mem = cuda.mem_alloc(host_mem.nbytes)

        # Append the device buffer to device bindings.
        bindings.append(int(device_mem))

        # Append to the appropriate list.
        if engine.binding_is_input(binding):
            inputs.append(HostDeviceMem(host_mem, device_mem))
        else:
            outputs.append(HostDeviceMem(host_mem, device_mem))
    return inputs, outputs, bindings, stream


class Detect:
    def __init__(self, engine_path, input_shapes):
        cuda.init()
        self.cfx = cuda.Device(0).make_context()
        self.engine_path = engine_path
        # {input_name: shape}
        self.input_shapes = input_shapes
        self._init_model()
        # self.cfx.pop()
        self.bindings = None
        self.stream = None
        self.inputs = None
        self.outputs = None
        self.running = False

    def _init_model(self):
        with open(self.engine_path, "rb") as f:
            serialized_engine = f.read()
        logger = trt.Logger(trt.Logger.WARNING)
        runtime = trt.Runtime(logger)
        self.engine = runtime.deserialize_cuda_engine(serialized_engine)
        self.context = self.engine.create_execution_context()
    
    def do_inference_v2(self, *inputs):
        if not self.running:
            for input_name in self.input_shapes:
                idx = self.engine.get_binding_index(input_name)
                assert self.engine.binding_is_input(idx)
                # print(self.engine.get_binding_shape(idx))
                # print(self.input_shapes[input_name])
                assert self.engine.get_binding_shape(idx) == self.input_shapes[input_name]
                self.context.set_binding_shape(idx, self.input_shapes[input_name])
                self.inputs, self.outputs, self.bindings, self.stream = allocate_buffers(self.engine, max_batch_size=1)
            self.running = True
        for idx in range(len(self.inputs)):
            if isinstance(inputs[idx], np.ndarray):
                np.copyto(self.inputs[idx].host, inputs[idx].ravel())
            elif isinstance(inputs[idx], int):
                np.copyto(self.inputs[idx].host, inputs[idx])
        # Transfer input data to the GPU.
        [cuda.memcpy_htod_async(inp.device, inp.host, self.stream)
         for inp in self.inputs]
        # Run inference.
        self.context.execute_async_v2(
            bindings=self.bindings, stream_handle=self.stream.handle)
        # Transfer predictions back from the GPU.
        [cuda.memcpy_dtoh_async(out.host, out.device, self.stream)
         for out in self.outputs]
        # Synchronize the stream
        self.stream.synchronize()
        # Return only the host outputs.
        return [out.host for out in self.outputs]

    def detect(self, *x):
        t1 = time.time()
        self.cfx.push()
        t2 = time.time()
        result = self.do_inference_v2(*x)
        t3 = time.time()
        self.cfx.pop()
        t4 = time.time()
        print("Context push %s" % str(t2 - t1))
        print("Inference time %s" % str(t3 - t2))
        print("Context pop %s" % str(t4 - t3))
        return result


if __name__ == "__main__":
    voxels = np.random.rand(10000, 32, 10)
    voxel_idxs = np.random.randint(200, size=(10000, 4))
    model = Detect("./pointpillar_fp16.engine", {"voxels": (10000, 32, 10), "voxel_idxs": (10000, 4), "voxel_num": (1,)})
    import time
    times = []
    for i in range(200):
        s = time.time()
        model.detect(voxels, voxel_idxs, 10000)
        e = time.time()
        times.append(e - s)
    print("End")
    import numpy as np
    print(np.average(times[1:]))
