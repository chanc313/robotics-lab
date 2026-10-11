// Publishes "hello <n>" on /hello at a configurable rate (parameter rate_hz, default 2).
#include <chrono>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class Talker : public rclcpp::Node
{
public:
    Talker() : Node("talker")
    {
        const double rate_hz = declare_parameter("rate_hz", 2.0);
        publisher_ = create_publisher<std_msgs::msg::String>("hello", 10);
        timer_ = create_wall_timer(
            std::chrono::duration<double>(1.0 / rate_hz), [this] { publish(); });
    }

private:
    void publish()
    {
        std_msgs::msg::String message;
        message.data = "hello " + std::to_string(count_++);
        RCLCPP_INFO(get_logger(), "publish: %s", message.data.c_str());
        publisher_->publish(message);
    }

    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    unsigned int count_ = 0;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<Talker>());
    rclcpp::shutdown();
    return 0;
}
