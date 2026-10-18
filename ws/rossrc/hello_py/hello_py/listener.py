"""Subscribe to /hello; with max_messages > 0, exit after that many messages."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.task import Future
from std_msgs.msg import String


class Listener(Node):
    def __init__(self) -> None:
        super().__init__("listener")
        self.max_messages = self.declare_parameter("max_messages", 0).value
        self.received = 0
        self.done = Future()
        self.create_subscription(String, "hello", self.on_message, 10)

    def on_message(self, message: String) -> None:
        self.received += 1
        self.get_logger().info(f"heard: {message.data}")
        if self.max_messages and self.received >= self.max_messages:
            self.get_logger().info(f"received {self.received} messages, exiting")
            self.done.set_result(True)


def main() -> None:
    rclpy.init()
    node = Listener()
    try:
        if node.max_messages:
            rclpy.spin_until_future_complete(node, node.done)
        else:
            rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
