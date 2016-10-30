from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import os
import tempfile

from chainer import optimizers
import numpy as np

from chainerrl.q_function import FCSIQFunction
from chainerrl.q_function import FCSIContinuousQFunction
from chainerrl.q_function import FCLSTMStateQFunction
from chainerrl.envs.simple_abc import ABC
from chainerrl.explorers.epsilon_greedy import LinearDecayEpsilonGreedy
from chainerrl import replay_buffer
from test_training import _TestTraining


class _TestDQNLike(_TestTraining):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.model_filename = os.path.join(self.tmpdir, 'model.h5')
        self.rbuf_filename = os.path.join(self.tmpdir, 'rbuf.pkl')

    def make_agent(self, env, gpu):
        q_func = self.make_q_func(env)
        opt = self.make_optimizer(env, q_func)
        explorer = self.make_explorer(env)
        rbuf = self.make_replay_buffer(env)
        agent = self.make_dqn_agent(env=env, q_func=q_func, opt=opt,
                                    explorer=explorer, rbuf=rbuf, gpu=gpu)
        return agent

    def make_dqn_agent(self, env, q_func, opt, explorer, rbuf, gpu):
        raise NotImplementedError()

    def make_env_and_successful_return(self):
        raise NotImplementedError()

    def make_explorer(self, env):
        raise NotImplementedError()

    def make_optimizer(self, env, q_func):
        raise NotImplementedError()

    def make_replay_buffer(self, env):
        raise NotImplementedError()

    def test_training_gpu(self):
        self._test_training(0, steps=1000)
        self._test_training(0, steps=300, load_model=True)

    def test_training_cpu(self):
        self._test_training(-1, steps=1000)


class _TestDQNOnABC(_TestDQNLike):

    def make_agent(self, env, gpu):
        q_func = self.make_q_func(env)
        opt = self.make_optimizer(env, q_func)
        explorer = self.make_explorer(env)
        rbuf = self.make_replay_buffer(env)
        return self.make_dqn_agent(env=env, q_func=q_func,
                                   opt=opt, explorer=explorer, rbuf=rbuf,
                                   gpu=gpu)

    def make_dqn_agent(self, env, q_func, opt, explorer, rbuf, gpu):
        raise NotImplementedError()

    def make_explorer(self, env):
        def random_action_func():
            a = env.action_space.sample()
            if isinstance(a, np.ndarray):
                return a.astype(np.float32)
            else:
                return a
        return LinearDecayEpsilonGreedy(1.0, 0.1, 1000, random_action_func)

    def make_optimizer(self, env, q_func):
        opt = optimizers.Adam()
        opt.setup(q_func)
        return opt

    def make_replay_buffer(self, env):
        return replay_buffer.ReplayBuffer(10 ** 5)


class _TestDQNOnDiscreteABC(_TestDQNOnABC):

    def make_q_func(self, env):
        return FCSIQFunction(n_input_channels=env.observation_space.low.size,
                             n_actions=env.action_space.n,
                             n_hidden_channels=10,
                             n_hidden_layers=2)

    def make_env_and_successful_return(self):
        return ABC(discrete=True), 1


class _TestDQNOnDiscretePOABC(_TestDQNOnABC):

    def make_q_func(self, env):
        return FCLSTMStateQFunction(n_dim_obs=env.observation_space.low.size,
                                    n_dim_action=env.action_space.n,
                                    n_hidden_channels=10,
                                    n_hidden_layers=1)

    def make_replay_buffer(self, env):
        return replay_buffer.EpisodicReplayBuffer(10 ** 5)

    def make_env_and_successful_return(self):
        return ABC(discrete=True, partially_observable=True), 1


class _TestDQNOnContinuousABC(_TestDQNOnABC):

    def make_q_func(self, env):
        n_dim_action = env.action_space.low.size
        n_dim_obs = env.observation_space.low.size
        return FCSIContinuousQFunction(
            n_input_channels=n_dim_obs,
            n_dim_action=n_dim_action,
            n_hidden_channels=20,
            n_hidden_layers=2,
            action_space=env.action_space)

    def make_env_and_successful_return(self):
        return ABC(discrete=False), 1
