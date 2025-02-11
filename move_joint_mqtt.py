import os
import sys
import time
import math
import paho.mqtt.client as mqtt
from xarm.wrapper import XArmAPI

# ✅ 机械臂 IP 配置
ip = "192.168.1.236"
arm = XArmAPI(ip)

# ✅ 机械臂初始化
def initialize_arm():
    """初始化 xArm 并检查状态"""
    arm.motion_enable(enable=True)
    arm.set_mode(0)  # 位置控制模式
    arm.set_state(0)  # 进入正常状态

    # ✅ 检查是否有错误，自动清除
    err_code, warn_code = arm.get_err_warn_code()
    if err_code != 0:
        print(f"⚠️ xArm 处于错误状态: {err_code}，警告代码: {warn_code}，尝试清除错误并复位...")
        arm.clean_error()
        arm.reset(wait=True)

    print("✅ 机械臂初始化完成！")

initialize_arm()

# ✅ MQTT 服务器配置
MQTT_BROKER = "172.20.10.10"
MQTT_PORT = 1883
MQTT_TOPIC = "xarm/move"

# ✅ 机械臂状态
initial_angles = [0, 0, 0, 0, 0, 0, 0]
current_angles = initial_angles.copy()
move_step = 5
move_count = 0
max_moves = 100
speed = 50
acceleration = 500  # ✅ 限制加速度，防止超出 xArm 限制

def reset_arm():
    """复位机械臂到初始位置"""
    global move_count, current_angles
    print("🔄 机械臂复位中...")
    arm.clean_error()
    arm.reset(wait=True)
    print("✅ 机械臂已复位")
    current_angles = initial_angles.copy()
    move_count = 0

def check_arm_status():
    """检查机械臂状态"""
    err_code, warn_code = arm.get_err_warn_code()
    if err_code != 0:
        print(f"⚠️ xArm 处于错误状态，错误代码: {err_code}，警告代码: {warn_code}，尝试复位...")
        reset_arm()
    if not arm.connected:
        print("⚠️ 机械臂连接丢失，尝试重连...")
        arm.connect()
    state = arm.get_state()
    if state != 0:
        print(f"⚠️ 机械臂当前状态: {state}，尝试恢复...")
        arm.set_state(0)

def on_connect(client, userdata, flags, rc):
    """MQTT 连接成功时的回调函数"""
    if rc == 0:
        print("✅ 成功连接到 MQTT 服务器")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ 连接失败，错误码: {rc}")

def on_message(client, userdata, msg):
    """收到 MQTT 消息时执行的函数"""
    global current_angles, move_count

    print(f"📩 收到消息: {msg.topic} -> {msg.payload.decode()}")

    try:
        joint_index = int(msg.payload.decode())
        if joint_index == 9:
            reset_arm()
            return
        if 0 <= joint_index < 7:
            check_arm_status()

            if move_count >= max_moves:
                print("🔄 机械臂达到最大移动次数，自动复位...")
                reset_arm()
                return

            new_angle = current_angles[joint_index] + move_step
            if new_angle > 180 or new_angle < -180:
                print(f"⚠️ 关节 {joint_index} 角度超出范围，限制在 ±180° 内")
                return

            current_angles[joint_index] = new_angle
            move_count += 1
            print(f"🔄 移动关节 {joint_index} 到 {current_angles[joint_index]}°")

            code = arm.set_servo_angle(angle=current_angles, speed=speed, mvacc=acceleration, wait=True)
            if code != 0:
                print(f"⚠️ 机械臂移动失败，错误代码: {code}")
                reset_arm()
            else:
                print(f"✅ 机械臂当前角度: {arm.get_servo_angle()}")

        else:
            print("⚠️ 无效的关节编号！请输入 0 ~ 6 之间的数字")

    except ValueError:
        print("⚠️ 解析 MQTT 消息失败，请发送正确的关节编号（0-6）")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("🚀 正在连接 MQTT 服务器...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()