#!/usr/bin/env python

import unittest
import atexit
import os
import rostopic
import rospy
import roslaunch
from testing_tools.misc import capture_screen, MessageQueue, add_text_to_video, wait_for, check_if_ffmpeg_satisfied
from testing_tools.blender import set_alive
from std_msgs.msg import String
import subprocess

CWD = os.path.abspath(os.path.dirname(__file__))

robot_name = 'han'
cmd = 'roslaunch {}/launch/robot.launch basedir:={basedir} name:={name}'.format(
    CWD, basedir='launch', name=robot_name)
proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
def shutdown():
    if proc:
        os.killpg(proc.pid, 2)
atexit.register(shutdown)

class InteractTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        for node in ['chatbot_en', 'chatbot_zh', 'speech2command', 'tts']:
            wait_for(node, robot_name)
        wait_for('blender_api')
        rospy.wait_for_service('/blender_api/set_param')

        self.output_video = os.path.expanduser('~/.hr/test/screencast')
        if not os.path.isdir(self.output_video):
            os.makedirs(self.output_video)
        self.output_audio = os.path.expanduser('~/.hr/test/audio')
        if not os.path.isdir(self.output_audio):
            os.makedirs(self.output_audio)
        self.queue = MessageQueue()
        self.queue.subscribe(
            '/{}/chatbot_responses'.format(robot_name), String)

    def setUp(self):
        set_alive(False)
        rospy.sleep(1)

    def tearDown(self):
        set_alive(True)
        rospy.sleep(1)

    @unittest.skipUnless(
        check_if_ffmpeg_satisfied(), 'Skip because ffmpeg is not satisfied.')
    def test_emotion_cmd(self):
        duration = 6
        pub, msg_class = rostopic.create_publisher(
            '/{}/speech'.format(robot_name), 'chatbot/ChatMessage', True)
        for cmd in ['sad', 'happy']:
            screen_output = '%s/bl_%s.avi' % (
                self.output_video, cmd.replace(' ', '_'))
            with capture_screen(screen_output, duration):
                rospy.sleep(0.5)
                pub.publish(msg_class(cmd, 100))

    @unittest.skipUnless(
        check_if_ffmpeg_satisfied(), 'Skip because ffmpeg is not satisfied.')
    def test_gesture_cmd(self):
        duration = 2
        pub, msg_class = rostopic.create_publisher(
            '/{}/speech'.format(robot_name), 'chatbot/ChatMessage', True)
        for cmd in ['blink', 'nod', 'shake']:
            screen_output = '%s/bl_%s.avi' % (
                self.output_video, cmd.replace(' ', '_'))
            with capture_screen(screen_output, duration):
                rospy.sleep(0.5)
                pub.publish(msg_class(cmd, 100))

    @unittest.skipUnless(
        check_if_ffmpeg_satisfied(), 'Skip because ffmpeg is not satisfied.')
    def test_turn_eye_cmd(self):
        duration = 2
        pub, msg_class = rostopic.create_publisher(
            '/{}/speech'.format(robot_name), 'chatbot/ChatMessage', True)
        pub.publish(msg_class('look center', 100))
        rospy.sleep(duration)
        for cmd in ['look left', 'look right']:
            screen_output = '%s/bl_%s.avi' % (
                self.output_video, cmd.replace(' ', '_'))
            with capture_screen(screen_output, duration):
                rospy.sleep(0.5)
                pub.publish(msg_class(cmd, 100))
            pub.publish(msg_class('look center', 100))
            rospy.sleep(duration)

    @unittest.skipUnless(
        check_if_ffmpeg_satisfied(), 'Skip because ffmpeg is not satisfied.')
    def test_turn_head_cmd(self):
        duration = 2
        pub, msg_class = rostopic.create_publisher(
            '/{}/speech'.format(robot_name), 'chatbot/ChatMessage', True)
        pub.publish(msg_class('turn center', 100))
        rospy.sleep(duration)
        for cmd in ['turn left', 'turn right']:
            screen_output = '%s/bl_%s.avi' % (
                self.output_video, cmd.replace(' ', '_'))
            with capture_screen(screen_output, duration):
                rospy.sleep(0.5)
                pub.publish(msg_class(cmd, 100))
            pub.publish(msg_class('turn center', 100))
            rospy.sleep(duration)

    def test_chat(self):
        pub, msg_class = rostopic.create_publisher(
            '/{}/speech'.format(robot_name), 'chatbot/ChatMessage', True)
        self.queue.clear()
        for speech in ['hi', 'what\'s your name']:
            pub.publish(msg_class(speech, 100))
            rospy.sleep(1)
        msgs = self.queue.tolist()
        self.assertEqual(msgs[0].data.lower(), 'hi there!')
        self.assertTrue('han' in msgs[1].data.lower())

if __name__ == '__main__':
    unittest.main()

