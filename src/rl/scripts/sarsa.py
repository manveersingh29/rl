#! /usr/bin/env python

import numpy as np
from math import *
from std_msgs.msg import String
from itertools import product
from sensor_msgs.msg import LaserScan

STATE_SPACE_IND_MAX = 144 - 1
STATE_SPACE_IND_MIN = 1 - 1
ACTIONS_IND_MAX = 2
ACTIONS_IND_MIN = 0

ANGLE_MAX = 360 - 1
ANGLE_MIN = 1 - 1
HORIZON_WIDTH = 75

T_MIN = 0.001

# Create actions
def createActions():
    actions = np.array([0, 1, 2])
    return actions

# Create state space for Q table
def createStateSpace():
    x1 = set((0, 1, 2))
    x2 = set((0, 1, 2))
    x3 = set((0, 1, 2, 3))
    x4 = set((0, 1, 2, 3))
    state_space = set(product(x1, x2, x3, x4))
    return np.array(list(state_space))

# Create Q table, dim: n_states x n_actions
def createQTable(n_states, n_actions):
    Q_table = np.zeros((n_states, n_actions))
    return Q_table

# Read Q table from path
def readQTable(path):
    Q_table = np.genfromtxt(path, delimiter=' , ')
    return Q_table

# Write Q table to path
def saveQTable(path, Q_table):
    np.savetxt(path, Q_table, delimiter=' , ')

# Select the best action a in state
def getBestAction(Q_table, state_ind, actions):
    if STATE_SPACE_IND_MIN <= state_ind <= STATE_SPACE_IND_MAX:
        status = 'getBestAction => OK'
        a_ind = np.argmax(Q_table[state_ind, :])
        a = actions[a_ind]
    else:
        status = 'getBestAction => INVALID STATE INDEX'
        a = getRandomAction(actions)

    return a, status

# Select random action from actions
def getRandomAction(actions):
    n_actions = len(actions)
    a_ind = np.random.randint(n_actions)
    return actions[a_ind]

# Epsilog Greedy Exploration action chose
def sarsaEpsilonGreedy(Q_table, state_ind, actions, epsilon):
    if np.random.uniform() > epsilon and STATE_SPACE_IND_MIN <= state_ind <= STATE_SPACE_IND_MAX:
        status = 'sarsaEpsilonGreedy => OK'
        a_ind = np.argmax(Q_table[state_ind, :])
        a = actions[a_ind]
    else:
        status = 'sarsaEpsilonGreedy => OK'
        a = getRandomAction(actions)

    return a, status

# Reward function for Q-learning - table
def getReward(action, prev_action, lidar, prev_lidar, crash):
    # ... (your existing reward function)
    if crash:
        terminal_state = True
        reward = -100
    else:
        lidar_horizon = np.concatenate((lidar[(ANGLE_MIN + HORIZON_WIDTH):(ANGLE_MIN):-1],lidar[(ANGLE_MAX):(ANGLE_MAX - HORIZON_WIDTH):-1]))
        prev_lidar_horizon = np.concatenate((prev_lidar[(ANGLE_MIN + HORIZON_WIDTH):(ANGLE_MIN):-1],prev_lidar[(ANGLE_MAX):(ANGLE_MAX - HORIZON_WIDTH):-1]))
        terminal_state = False
        # Reward from action taken = fowrad -> +0.2 , turn -> -0.1
        if action == 0:
            r_action = +0.2
        else:
            r_action = -0.1
        # Reward from crash distance to obstacle change
        W = np.linspace(0.9, 1.1, len(lidar_horizon) // 2)
        W = np.append(W, np.linspace(1.1, 0.9, len(lidar_horizon) // 2))
        if np.sum( W * ( lidar_horizon - prev_lidar_horizon) ) >= 0:
            r_obstacle = +0.2
        else:
            r_obstacle = -0.2
        # Reward from turn left/right change
        if ( prev_action == 1 and action == 2 ) or ( prev_action == 2 and action == 1 ):
            r_change = -0.8
        else:
            r_change = 0.0

        # Cumulative reward
        reward = r_action + r_obstacle + r_change

    return ( reward, terminal_state )

# Update Q-table values
def updateQTableSARSA(Q_table, state_ind, action, reward, next_state_ind, next_action, alpha, gamma):
    if STATE_SPACE_IND_MIN <= state_ind <= STATE_SPACE_IND_MAX and STATE_SPACE_IND_MIN <= next_state_ind <= STATE_SPACE_IND_MAX:
        status = 'updateQTableSARSA => OK'
        Q_table[state_ind, action] = (1 - alpha) * Q_table[state_ind, action] + alpha * (
            reward + gamma * Q_table[next_state_ind, next_action]
        )
    else:
        status = 'updateQTableSARSA => INVALID STATE INDEX'
    return Q_table, status

# ... (your other existing functions)

def sarsa_learning(num_episodes=1000, max_steps=500):
    # Set learning parameters
    epsilon = 0.1
    alpha = 0.1
    gamma = 0.9

    # Create actions and state space
    actions = createActions()
    state_space = createStateSpace()

    # Create Q-table
    n_states = STATE_SPACE_IND_MAX - STATE_SPACE_IND_MIN + 1
    n_actions = ACTIONS_IND_MAX - ACTIONS_IND_MIN + 1
    Q_table = createQTable(n_states, n_actions)

    # Start learning loop
    for episode in range(num_episodes):
        # Initialize state
        state_ind = np.random.randint(STATE_SPACE_IND_MIN, STATE_SPACE_IND_MAX + 1)

        # Choose action A using epsilon-greedy policy (SARSA action selection)
        action, _ = sarsaEpsilonGreedy(Q_table, state_ind, actions, epsilon)

        for step in range(max_steps):
            # Take action A and observe reward R and next state S'
            reward, crash = getReward(action, prev_action, lidar, prev_lidar, crash)
            next_state_ind = updateState(state_ind, action)

            # Choose next action A' using epsilon-greedy policy (SARSA action selection)
            next_action, _ = sarsaEpsilonGreedy(Q_table, next_state_ind, actions, epsilon)

            # Update Q-table using SARSA update rule
            Q_table, _ = updateQTableSARSA(
                Q_table, state_ind, action, reward, next_state_ind, next_action, alpha, gamma
            )

            # Update current state and action for the next iteration
            state_ind = next_state_ind
            action = next_action

            # Check if the episode is done (terminal state reached)
            if terminal_state:
                break

    return Q_table
