# 安装依赖包
sudo apt install ros-melodic-fake-localization ros-melodic-map-server ros-melodic-hector-slam ros-melodic-gmapping ros-melodic-slam-gmapping ros-melodic-open-karto ros-melodic-slam-karto

# 新建ros程序包
cd ~/catkin_ws/src
# catkin_create_pkg <package_name> [depend1] [depend2] [depend3]
catkin_create_pkg ros_slam_rplidar std_msgs rospy roscpp
# 编辑slam launch
cd ~/catkin_ws/src/ros_slam_rplidar/launch/slam/
vim hector.launch    #不需要里程计数据，只根据激光信息即可构建地图
    <!--
    notice : you should install hector-slam at first,  sudo apt-get install ros-melodic-hector-slam
               this launch just for test, you should improve the param for the best result.
     -->
    <launch>
      <node pkg="tf" type="static_transform_publisher" name="link1_broadcaster" args="1 0 0 0 0 0 base_link laser 100" /> <!--change -->
        <node pkg="hector_mapping" type="hector_mapping" name="hector_height_mapping" output="screen">
        <param name="scan_topic" value="scan" />
        <param name="base_frame" value="base_link" />
        <param name="odom_frame" value="base_link" />
        <param name="output_timing" value="false"/>
        <param name="advertise_map_service" value="true"/>
        <param name="use_tf_scan_transformation" value="true"/>
        <param name="use_tf_pose_start_estimate" value="false"/>
        <param name="pub_map_odom_transform" value="true"/>
        <param name="map_with_known_poses" value="false"/>
        <param name="map_pub_period" value="0.5"/>
        <param name="update_factor_free" value="0.45"/>
        <param name="map_update_distance_thresh" value="0.02"/>
        <param name="map_update_angle_thresh" value="0.1"/>
        <param name="map_resolution" value="0.05"/>
        <param name="map_size" value="1024"/>
        <param name="map_start_x" value="0.5"/>
        <param name="map_start_y" value="0.5"/>
      </node>
    </launch>
vim gmapping.launch   #需要IMU+里程计+激光信息构建地图
    <!--
      notice : you should install gmapping-slam at first, command 'sudo apt-get install ros-indigo-gmapping'and 'sudo apt-get install ros-indigo-slam-gmapping'.
               this launch just for test, you should improve the param for the best result.
      you nedd change the frame of the "static_transform_publisher" when using the real robot platform.
      it is better  subscribe the topic /odom with true to slam in gmapping
     -->
    <launch>
      <node pkg="tf" type="static_transform_publisher" name="link1_broadcaster" args="0 0 0 0 0 0 base_link laser 100" /> <!--change -->
      <node pkg="tf" type="static_transform_publisher" name="link2_broadcaster" args="0 0 0 0 0 0 odom base_link 100" /> <!--change -->
      <node pkg="gmapping" type="slam_gmapping" name="simple_gmapping" output="screen">
          <!--remap from="scan" to="base_scan"/-->
          <param name="map_update_interval" value="5.0"/>
          <param name="maxUrange" value="8.0"/>
          <param name="sigma" value="0.05"/>
          <param name="kernelSize" value="1"/>
          <param name="lstep" value="0.05"/>
          <param name="astep" value="0.05"/>
          <param name="iterations" value="5"/>
          <param name="lsigma" value="0.075"/>
          <param name="ogain" value="3.0"/>
          <param name="lskip" value="0"/>
          <param name="minimumScore" value="50"/>
          <param name="srr" value="0.1"/>
          <param name="srt" value="0.2"/>
          <param name="str" value="0.1"/>
          <param name="stt" value="0.2"/>
          <param name="linearUpdate" value="0.3"/>
          <param name="angularUpdate" value="0.4"/>
          <param name="temporalUpdate" value="3.0"/>
          <param name="resampleThreshold" value="0.5"/>
          <param name="particles" value="30"/>
          <param name="xmin" value="-5.0"/>
          <param name="ymin" value="-5.0"/>
          <param name="xmax" value="5.0"/>
          <param name="ymax" value="5.0"/>
          <param name="delta" value="0.05"/>
          <param name="llsamplerange" value="0.01"/>
          <param name="llsamplestep" value="0.01"/>
          <param name="lasamplerange" value="0.005"/>
          <param name="lasamplestep" value="0.005"/>
      </node>
    </launch>

vim karto.launch
    <!--
      notice : you should install karto-slam at first, command 'sudo apt-get install ros-indigo-open-karto'and 'sudo apt-get install ros-indigo-slam-karto'.
              this launch just for test, you should improve the param for the best result.
      you nedd change the frame of the "static_transform_publisher" when using the real robot platform.
      it is better  subscribe the topic /odom with true to slam in gmapping
    -->
    <launch>
      <node pkg="tf" type="static_transform_publisher" name="link1_broadcaster" args="0 0 0 0 0 0 base_link laser 100" /> <!--change -->
      <node pkg="tf" type="static_transform_publisher" name="link2_broadcaster" args="0 0 0 0 0 0 odom base_link 100" /> <!--change -->
      <node pkg="slam_karto" type="slam_karto" name="slam_karto" output="screen">
        <remap from="scan" to="scan"/>
        <param name="odom_frame" value="odom"/>
        <param name="map_update_interval" value="25"/>
        <param name="resolution" value="0.025"/>
        <rosparam command="load" file="$(find ros_slam_rplidar)/launch/slam/karto_mapper_params.yaml" />
      </node>
    </launch>
vim karto_mapper_params.yaml
    # General Parameters
    use_scan_matching: true
    use_scan_barycenter: true
    minimum_travel_distance: 0.3 
    minimum_travel_heading: 0.4  # 0.2         #in radians
    scan_buffer_size: 67                       
    scan_buffer_maximum_scan_distance: 20.0
    link_match_minimum_response_fine: 0.6
    link_scan_maximum_distance: 4         #  6
    do_loop_closing: true
    loop_match_minimum_chain_size: 5
    loop_match_maximum_variance_coarse: 0.4    # gets squared later
    loop_match_minimum_response_coarse: 0.4        # 0.6
    loop_match_minimum_response_fine: 0.6
    # Correlation Parameters -              Correlation Parameters
    correlation_search_space_dimension: 2
    correlation_search_space_resolution: 0.05
    correlation_search_space_smear_deviation: 0.05
    # Correlation Parameters - Loop Closure Parameters
    loop_search_space_dimension: 10  # 2.8
    loop_search_space_resolution: 0.1
    loop_search_space_smear_deviation: 0.05
    loop_search_maximum_distance: 4.0
    # Scan Matcher Parameters
    distance_variance_penalty: 0.3             # gets squared later
    angle_variance_penalty: 0.35                # in degrees (gets converted to radians then squared)
    fine_search_angle_offset: 0.00349               # in degrees (gets converted to radians)
    coarse_search_angle_offset: 0.349            # in degrees (gets converted to radians)
    coarse_angle_resolution: 0.0349                # in degrees (gets converted to radians)
    minimum_angle_penalty: 0.9
    minimum_distance_penalty: 0.5
    use_response_expansion: false

# 编辑slam rviz
cd ~/catkin_ws/src/ros_slam_rplidar/rviz/
vim slam.rviz
    Panels:
      - Class: rviz/Displays
        Help Height: 78
        Name: Displays
        Property Tree Widget:
          Expanded:
            - /Global Options1
            - /Status1
            - /RPLidarLaserScan1
          Splitter Ratio: 0.5
        Tree Height: 413
      - Class: rviz/Selection
        Name: Selection
      - Class: rviz/Tool Properties
        Expanded:
          - /2D Pose Estimate1
          - /2D Nav Goal1
        Name: Tool Properties
        Splitter Ratio: 0.588679
      - Class: rviz/Views
        Expanded:
          - /Current View1
        Name: Views
        Splitter Ratio: 0.5
      - Class: rviz/Time
        Experimental: false
        Name: Time
        SyncMode: 0
        SyncSource: RPLidarLaserScan
    Visualization Manager:
      Class: ""
      Displays:
        - Alpha: 0.5
          Cell Size: 1
          Class: rviz/Grid
          Color: 160; 160; 164
          Enabled: true
          Line Style:
            Line Width: 0.03
            Value: Lines
          Name: Grid
          Normal Cell Count: 0
          Offset:
            X: 0
            Y: 0
            Z: 0
          Plane: XY
          Plane Cell Count: 10
          Reference Frame: <Fixed Frame>
          Value: true
        - Alpha: 1
          Autocompute Intensity Bounds: true
          Autocompute Value Bounds:
            Max Value: 0
            Min Value: 0
            Value: true
          Axis: Z
          Channel Name: intensity
          Class: rviz/LaserScan
          Color: 255; 255; 255
          Color Transformer: AxisColor
          Decay Time: 0
          Enabled: true
          Invert Rainbow: false
          Max Color: 255; 255; 255
          Max Intensity: 4096
          Min Color: 0; 0; 0
          Min Intensity: 0
          Name: RPLidarLaserScan
          Position Transformer: XYZ
          Queue Size: 1000
          Selectable: true
          Size (Pixels): 5
          Size (m): 0.03
          Style: Squares
          Topic: /scan
          Use Fixed Frame: true
          Use rainbow: true
          Value: true
        - Alpha: 0.7
          Class: rviz/Map
          Color Scheme: map
          Draw Behind: false
          Enabled: true
          Name: Map
          Topic: /map
          Value: true
      Enabled: true
      Global Options:
        Background Color: 48; 48; 48
        Fixed Frame: map
        Frame Rate: 30
      Name: root
      Tools:
        - Class: rviz/MoveCamera
        - Class: rviz/Interact
          Hide Inactive Objects: true
        - Class: rviz/Select
        - Class: rviz/SetInitialPose
          Topic: /initialpose
        - Class: rviz/SetGoal
          Topic: /move_base_simple/goal
      Value: true
      Views:
        Current:
          Class: rviz/Orbit
          Distance: 11.1184
          Enable Stereo Rendering:
            Stereo Eye Separation: 0.06
            Stereo Focal Distance: 1
            Swap Stereo Eyes: false
            Value: false
          Focal Point:
            X: -0.0344972
            Y: 0.065886
            Z: 0.148092
          Name: Current View
          Near Clip Distance: 0.01
          Pitch: 1.5698
          Target Frame: <Fixed Frame>
          Value: Orbit (rviz)
          Yaw: 5.66358
        Saved: ~
    Window Geometry:
      Displays:
        collapsed: false
      Height: 626
      Hide Left Dock: false
      Hide Right Dock: false
      QMainWindow State: 000000ff00000000fd0000000400000000000001950000022cfc0200000006fb0000001200530065006c0065006300740069006f006e00000001e10000009b0000006400fffffffb0000001e0054006f006f006c002000500072006f0070006500720074006900650073020000019b000001b500000185000000a3fb000000120056006900650077007300200054006f006f02000001df000002110000018500000122fb000000200054006f006f006c002000500072006f0070006500720074006900650073003203000002880000011d000002210000017afb000000100044006900730070006c00610079007301000000280000022c000000dd00fffffffb0000000a0049006d006100670065000000028d000000c60000000000000000000000010000010b00000294fc0200000003fb0000001e0054006f006f006c002000500072006f00700065007200740069006500730100000041000000780000000000000000fb0000000a00560069006500770073000000003300000294000000b000fffffffb0000001200530065006c0065006300740069006f006e010000025a000000b200000000000000000000000200000490000000a9fc0100000001fb0000000a00560069006500770073030000004e00000080000002e10000019700000003000004a00000003efc0100000002fb0000000800540069006d00650000000000000004a0000002f600fffffffb0000000800540069006d00650100000000000004500000000000000000000003240000022c00000004000000040000000800000008fc0000000100000002000000010000000a0054006f006f006c00730100000000ffffffff0000000000000000
      Selection:
        collapsed: false
      Time:
        collapsed: false
      Tool Properties:
        collapsed: false
      Views:
        collapsed: false
      Width: 1215
      X: 503
      Y: 227

# 编辑view slam launch
cd ~/catkin_ws/src/ros_slam_rplidar/launch/
vim slam_laser.launch
    <!-- SLAM with lidar -->
    <launch>
      <!-- Arguments -->
      <arg name="slam_methods" default="hector" doc="slam type [gmapping, hector, karto, cartographer]"/>
      <arg name="open_rviz" default="false"/>
      <arg name="planner"  default="" doc="opt: dwa, teb"/>

      <!-- robot with lidar -->
      <include file="$(find rplidar_ros)/launch/rplidar.launch" />

      <!-- SLAM: Gmapping, Cartographer, Hector, Karto -->
      <include file="$(find ros_slam_rplidar)/launch/slam/$(arg slam_methods).launch" />

      <!-- move_base -->
      <group unless="$(eval planner == '')">
        <include file="$(find ros_slam_rplidar)/launch/move_base.launch" unless="$(eval planner == '')">
            <arg name="planner"            value="$(arg planner)"/>
        </include>
      </group>

      <!-- rviz -->
      <group if="$(arg open_rviz)">
        <node name="rviz" pkg="rviz" type="rviz" args="-d $(find ros_slam_rplidar)/rviz/slam.rviz" />
      </group>
    </launch>

# 测试hector slam并通过rviz展示
roslaunch ros_slam_rplidar slam_laser.launch open_rviz:=true