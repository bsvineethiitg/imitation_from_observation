import numpy as np
from gym import utils
from gym.envs.mujoco import mujoco_env
import xml.etree.ElementTree as ET
import os
import gym.envs.mujoco.arm_shaping
import scipy.misc

class PusherEnv3DOFTarget(mujoco_env.MujocoEnv, utils.EzPickle):
    def __init__(self):
        utils.EzPickle.__init__(self)
        self.randomize_xml('3link_gripper_push_2d.xml')
        mujoco_env.MujocoEnv.__init__(self, 'temp.xml', 5)

    def _step(self, a):   
        reward = 0
        self.do_simulation(a, self.frame_skip)
        ob = self._get_obs()
        done = False
        if not hasattr(self, 'itr'):
            self.itr = 0
        self.itr += 1
        return ob, reward, done, dict(reward_true=reward_reach)

    def viewer_setup(self):
        # self.itr = 0
        self.viewer.cam.trackbodyid=0
        self.viewer.cam.distance = 4.0
        rotation_angle = self.np_random.uniform(low=0, high=360, size=1)
        cam_dist = 4
        cam_pos = np.array([0, 0, 0, cam_dist, -45, rotation_angle])
        for i in range(3):
            self.viewer.cam.lookat[i] = cam_pos[i]
        self.viewer.cam.distance = cam_pos[3]
        self.viewer.cam.elevation = cam_pos[4]
        self.viewer.cam.azimuth = cam_pos[5]
        self.viewer.cam.trackbodyid=-1
    
    def getcolor(self):
        color = np.random.uniform(low=0, high=1, size=3)
        while np.linalg.norm(color - np.array([1.,0.,0.])) < 0.5:
            color = np.random.uniform(low=0, high=1, size=3)
        return np.concatenate((color, [1.0]))

    def randomize_xml(self, xml_name):
        print("YOYO")
        fullpath = os.path.join(os.path.dirname(__file__), "assets", xml_name)
        newpath = os.path.join(os.path.dirname(__file__), "assets", "temp.xml")
        print(fullpath)
        tree = ET.parse(fullpath)
        root = tree.getroot()
        worldbody = tree.find(".//worldbody")
        num_objects = int(np.random.uniform(low=0, high=6, size=1))
        print("NUM objects %f"%(num_objects))
        for object_to_spawn in range(num_objects):

            pos_x = np.random.uniform(low=-0.9, high=0.9, size=1)
            pos_y = np.random.uniform(low=0, high=1.0, size=1)
            rgba_colors = self.getcolor()
            ET.SubElement(
                worldbody, "geom",
                pos="%f %f -0.145"%(pos_x, pos_y),
                rgba="%f %f %f 1"%(rgba_colors[0], rgba_colors[1], rgba_colors[2]),
                name="object" + str(object_to_spawn),
                size="0.17 0.005 0.2",
                density='0.00001',
                type="cylinder",
                contype="0",
                conaffinity="0"

            )

        tree.write(newpath)

    def reset_model(self):        
        self.itr = 0
        qpos = self.init_qpos#self.np_random.uniform(low=-0.1, high=0.1, size=self.model.nq)
        self.goal = np.concatenate([self.np_random.uniform(low=-1.1, high=-0.5, size=1),
                 self.np_random.uniform(low=0.5, high=1.1, size=1)])
        self.object = np.array([0.0, 0.0])
        rgbatmp = np.copy(self.model.geom_rgba)
        bgcolor = self.getcolor()
        armcolor = self.getcolor()
        while np.linalg.norm(bgcolor - armcolor) < 0.5:
            armcolor = np.concatenate((np.random.uniform(low=0, high=1, size=3), [1.0]))
        rgbatmp[0, :] = bgcolor
        for k in range(2, 9):
            rgbatmp[-k, :] = armcolor
        self.model.geom_rgba = rgbatmp

        qpos[-2:] = self.goal
        qvel = self.init_qvel
        qvel[-2:] = 0
        self.set_state(qpos, qvel)
        return self._get_obs()

    def _get_obs(self):
        if not hasattr(self, 'np_random'):
            self._seed()
        if not hasattr(self, 'object'):
            self.reset_model()

        return np.concatenate([
            self.model.data.qpos.flat[:-4],
            self.model.data.qvel.flat[:-4],
            self.get_body_com("distal_4"),
            self.get_body_com("goal"),
        ])