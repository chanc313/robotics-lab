"""Run the C++ talker and the Python listener; stop everything when the listener exits.

Run until Ctrl+C:           ros2 launch hello_py hello.launch.py
Self-check, exit after 5:   ros2 launch hello_py hello.launch.py max_messages:=5
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    max_messages = ParameterValue(LaunchConfiguration("max_messages"), value_type=int)
    listener = Node(
        package="hello_py",
        executable="listener",
        parameters=[{"max_messages": max_messages}],
        output="screen",
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument("max_messages", default_value="0"),
            Node(package="hello_cpp", executable="talker", output="screen"),
            listener,
            RegisterEventHandler(
                OnProcessExit(target_action=listener, on_exit=[EmitEvent(event=Shutdown())])
            ),
        ]
    )
