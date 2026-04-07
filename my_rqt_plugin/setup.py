from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_rqt_plugin'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share',package_name, 'resource'), glob('resource/*.ui')),
        (os.path.join('share', package_name),['plugin.xml'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gidong',
    maintainer_email='gd.baek1495@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
        'rqt_gui_py.plugin' : [
            'robot_qt = my_rqt_plugin.robot_qt:ControlPlugin'
        ]
    },
)
