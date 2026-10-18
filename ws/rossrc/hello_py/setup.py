from setuptools import setup

package_name = "hello_py"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/hello.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Channing",
    maintainer_email="hjchanc313@gmail.com",
    description="ROS 2 sandbox: Python listener for /hello",
    license="MIT",
    entry_points={"console_scripts": [f"listener = {package_name}.listener:main"]},
)
