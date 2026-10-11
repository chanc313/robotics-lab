# ROS 2 入门：从 `rossrc` 的两个节点讲起

2026-10-12。配合 [学习沙盒工具链](TOOLCHAIN.md#ros-2rossrc) 的 `rossrc/` 示例阅读，所有命令在 `dev` 容器中执行。

## 1. ROS 2 解决什么问题

一个机器人系统由很多独立程序组成：读相机的、算控制的、跑模型的、画界面的。它们用不同语言编写，可能运行在不同进程、容器甚至不同电脑上，但需要持续交换数据。

ROS 2 是这些程序之间的**通信框架和配套工具**，不是操作系统。它规定了：

- 程序怎样找到彼此（自动发现）；
- 数据长什么样（消息类型）；
- 数据怎样传过去（底层用 DDS 网络协议，本项目为 Fast DDS + UDPv4）；
- 怎样构建、启动、观察这些程序（colcon、launch、`ros2` 命令行）。

## 2. 五个核心概念

| 概念 | 含义 | 在示例中 |
|---|---|---|
| **节点 node** | 一个参与通信的程序单元，有自己的名字 | `talker`（C++）、`listener`（Python） |
| **话题 topic** | 有名字的数据通道，一方写、多方读 | `/hello` |
| **消息类型 message** | 话题上数据的固定格式，双方必须一致 | `std_msgs/msg/String`，只有一个字段 `data` |
| **发布 / 订阅** | 发布者往话题写消息，订阅者收到后回调处理；双方互不知道对方是谁 | talker 发布，listener 订阅 |
| **参数 parameter** | 节点启动时或运行中可调的配置值 | `rate_hz`、`max_messages` |

关键点是**解耦**：talker 不知道有没有人在听，listener 也不知道消息来自哪个程序、哪种语言。只要话题名和消息类型一致，C++ 和 Python 就能直接通信。换成 Isaac 仿真发布的关节状态、真机驱动发布的传感器数据，订阅方的写法完全一样。

另外两种通信方式以后会用到：**服务 service**（一问一答，像函数调用）和**动作 action**（长时间任务，带进度反馈和取消）。

## 3. 发布者：`hello_cpp/src/talker.cpp`

```cpp
class Talker : public rclcpp::Node          // 继承 Node，就成为一个 ROS 节点
{
public:
    Talker() : Node("talker")               // 节点名 talker
    {
        const double rate_hz = declare_parameter("rate_hz", 2.0);   // 声明参数，默认 2 Hz
        publisher_ = create_publisher<std_msgs::msg::String>("hello", 10);
        timer_ = create_wall_timer(
            std::chrono::duration<double>(1.0 / rate_hz), [this] { publish(); });
    }
    ...
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);                // 初始化 ROS 客户端库
    rclcpp::spin(std::make_shared<Talker>()); // 进入事件循环，直到 Ctrl+C
    rclcpp::shutdown();
}
```

- `create_publisher<String>("hello", 10)`：在话题 `hello` 上发布 `String`。名字不以 `/` 开头时会加上节点命名空间，这里解析为 `/hello`。`10` 是 **QoS 队列深度**：来不及发送时最多缓存 10 条。
- `create_wall_timer`：每隔 `1 / rate_hz` 秒调用一次 `publish()`，生成 `hello 0`、`hello 1`……并发布。
- `spin`：节点本身不写循环，而是把计时器、订阅等回调交给执行器调度。这是 ROS 程序的基本结构：**在构造函数里注册回调，在 spin 里等事件**。

## 4. 订阅者：`hello_py/hello_py/listener.py`

```python
class Listener(Node):
    def __init__(self) -> None:
        super().__init__("listener")
        self.max_messages = self.declare_parameter("max_messages", 0).value
        self.done = Future()
        self.create_subscription(String, "hello", self.on_message, 10)

    def on_message(self, message: String) -> None:   # 每收到一条消息调用一次
        self.received += 1
        self.get_logger().info(f"heard: {message.data}")
        if self.max_messages and self.received >= self.max_messages:
            self.done.set_result(True)
```

- `create_subscription(String, "hello", self.on_message, 10)`：话题名和消息类型必须与 talker 一致，否则收不到。
- `on_message` 是回调，由 `rclpy.spin` 在消息到达时调用。
- `max_messages` 为 0 时一直运行；大于 0 时收满就把 `done` 置为完成，`spin_until_future_complete` 随即返回，程序退出。这让它可以当作自动检查使用。

C++ 用 `rclcpp`，Python 用 `rclpy`，两者是同一套 ROS 概念的不同语言接口。

## 5. launch：一次启动多个节点

`hello_py/launch/hello.launch.py` 描述"启动哪些节点、带什么参数"：启动 talker 和 listener，把 `max_messages` 传给 listener，并注册一个事件——listener 退出时关闭整个 launch。真实机器人往往要同时启动几十个节点，launch 文件就是系统的启动清单。

## 6. 包、工作区与构建

ROS 代码以**包 package** 为单位组织，每个包有 `package.xml` 声明名字和依赖：

| 文件 | C++ 包 `hello_cpp` | Python 包 `hello_py` |
|---|---|---|
| 构建类型 | `ament_cmake`，用 `CMakeLists.txt` 编译并 `install` 可执行文件 | `ament_python`，用 `setup.py` 注册入口 `listener` |
| 额外文件 | — | `setup.cfg` 指定可执行文件安装到 `lib/hello_py`；`resource/hello_py` 是让 ROS 找到这个包的标记文件 |

`rossrc/` 是**工作区**的源码根。`colcon build` 逐个构建包，产物装进 `output/rossrc/install`。`source output/rossrc/install/setup.bash` 把这些包加入当前 shell 的环境，之后 `ros2 run hello_cpp talker` 才能找到它们。系统自带的 ROS 包在 `/opt/ros/jazzy`，自己的工作区叠加在它上面，称为 **overlay**。

完整流程：**写代码 → colcon build → source install/setup.bash → ros2 run / ros2 launch**。改了 C++ 要重新 build；Python 和 launch 文件因为用了 `--symlink-install`，改完直接重新运行即可。

## 7. 节点怎样找到彼此

两个节点之间没有任何地址配置。启动时，它们通过 DDS 在本机网络上广播自己，并根据 `ROS_DOMAIN_ID`（本项目默认 0）组成同一个通信图。同一个 domain 内、话题名和类型都匹配的发布者和订阅者会自动连上。这也是后续让 `sim` 里的 Isaac 与 `dev` 里的 ROS 节点通信的基础：双方 domain、话题、消息类型、QoS 一致即可。

## 8. 动手练习

先构建并 source（见 [工具链](TOOLCHAIN.md#ros-2rossrc)），然后在多个 `dev` 终端中操作：

1. 终端 A 运行 `ros2 run hello_cpp talker`，终端 B 运行 `ros2 run hello_py listener`，观察日志一一对应。
2. 终端 C 依次运行，理解通信图：
   ```bash
   ros2 node list
   ros2 node info /talker
   ros2 topic list
   ros2 topic info /hello --verbose
   ros2 topic hz /hello
   ros2 interface show std_msgs/msg/String
   ```
3. 停掉 talker，用命令行冒充发布者，listener 照样能收到：
   ```bash
   ros2 topic pub --rate 1 /hello std_msgs/msg/String "{data: 'from the command line'}"
   ```
4. 改发布频率：`ros2 run hello_cpp talker --ros-args -p rate_hz:=10.0`，再用 `ros2 topic hz /hello` 确认。
5. 把 listener 订阅的话题名改成 `hello2` 重新运行，观察它为什么收不到，再改回来。

## 9. 理解检查

- talker 和 listener 都没写对方的地址，它们是怎样连上的？
- 如果 listener 的消息类型写成 `std_msgs/msg/Int32`，会发生什么？
- 为什么节点代码里没有 `while` 循环？`spin` 在做什么？
- 第 3 题中，listener 能区分消息来自 talker 还是命令行吗？这对系统设计有什么好处和风险？
- Isaac 仿真以后会发布 `/joint_states`。按本页的模式，订阅它的节点需要知道哪些信息？
