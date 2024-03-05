import numpy as np
import matplotlib.pyplot as plt
from gym.wrappers import OrderEnforcing
from environments.grid import CustomEnv
from environments.MDP import MDP, Minigrid_MDP
from models.zlearning import power_iteration, compute_Pu_sparse
from scipy.sparse import csr_matrix, isspmatrix_csr


class LMDP:
    def __init__(self, n_states, n_nonterminal_states, n_actions):
        self.n_states = n_states
        self.n_nonterminal_states = n_nonterminal_states
        self.n_actions = n_actions
        self.P0 = np.zeros((n_nonterminal_states, n_states))
        self.R = np.zeros(n_states)
        self.s0 = 0 

    def act(self, current_state, P): 
        if isspmatrix_csr(P):
            next_state = np.random.choice(P[current_state].indices, p=P[current_state].data) # Using sparse matrix
        else:
            next_state = np.random.choice(self.n_states, p=P[current_state])
        reward = self.R[next_state]
        return next_state, reward, self.terminal(next_state)
  
    def terminal(self, state):
        raise NotImplementedError
    
    def embedding_to_MDP(self):
        mdp = MDP(self.n_states, self.n_nonterminal_states, self.n_actions)
        Pu = find_optimal_Pu(self)

        for i in range(mdp.n_states):
            mdp.R[i, :] = self.R[i]
            if not self.terminal(i):
                data = Pu[i].data
                for a in range(mdp.n_actions):
                    mdp.P[i, a, (Pu[i].indices)] = np.roll(data,a)

        return mdp

def find_optimal_Pu(lmdp: LMDP, epsilon=1e-30, lmbda=1):
    Z_opt, _ =  power_iteration(lmdp, lmbda=lmbda, epsilon=epsilon)
    Pu = compute_Pu_sparse(Z_opt, csr_matrix(lmdp.P0))
    return Pu
    
class Minigrid(LMDP):

    DIR_TO_VEC = [
        # Pointing right (positive X)
        np.array((1, 0)),
        # Down (positive Y)
        np.array((0, 1)),
        # Pointing left (negative X)
        np.array((-1, 0)),
        # Up (negative Y)
        np.array((0, -1)),
    ]

    def __init__(self, grid_size = 14, walls = []):
        self.grid_size = grid_size
        self.n_orientations = 4
        self.actions = list(range(3))
        #TODO: Finish adaptations from MDP. Compare Z Learning - Q Learning convergence. Check value function. Fix Z for terminal states. Check embbedding value functions.

        self._create_environment(grid_size, walls)
        super().__init__(n_states = len(self.states), n_nonterminal_states = len(self.S), n_actions = len(self.actions))
        self.n_cells = int(self.n_states / self.n_orientations)
        
        self.create_P0()
        self.reward_function()

    def _create_environment(self, grid_size, walls):
        self.env = OrderEnforcing(CustomEnv(size=grid_size+2, walls=walls, render_mode="rgb_array"))
        self.env.reset()

        self.states = [
            (x, y, o) for x in range(1, self.env.grid.height) for y in range(1, self.env.grid.width) for o in range(4)
            if self._is_valid_position(x, y)
        ]
        assert self.grid_size * self.grid_size - len(walls) == len(self.states) / self.n_orientations
        self.state_to_index = {state: index for index, state in enumerate(self.states)}
        self.T = [
            self.state_to_index[s] for s in self.states if self.terminal(self.state_to_index[s])
        ]
        self.S = [
            self.state_to_index[s] for s in self.states if not self.terminal(self.state_to_index[s])
        ]

    def create_P0(self):
        for state in self.S: #range(self.n_states): 
            for action in self.actions:
                next_state = self.state_step(self.states[state], action)
                self.P0[state][self.state_to_index[next_state]] += 1/self.n_actions

    def reward_function(self):
        for state in self.S:
            #pos = self.env.grid.get(state[0], state[1])
            #at_goal = pos is not None and pos.type == "goal"
            self.R[state] = -1.0

    def _is_valid_position(self, x: int, y: int) -> bool:
        """Testing whether a coordinate is a valid location."""
        return (
            0 < x < self.env.width and
            0 < y < self.env.height and
            (self.env.grid.get(x, y) is None or self.env.grid.get(x, y).can_overlap())
        )

    def state_step(self, state: tuple[int, int, int], action: int) -> tuple[int, int, int]:
        """Utility to move states one step forward, no side effect."""
        x, y, direction = state

        # Default transition to the sink failure state
        assert self._is_valid_position(x, y)

        # Transition left
        if action == self.env.actions.left:
            direction = (direction - 1) % 4
        # Transition right
        elif action == self.env.actions.right:
            direction = (direction + 1) % 4
        # Transition forward
        elif action == self.env.actions.forward:
            fwd_pos = np.array((x, y)) + self.DIR_TO_VEC[direction]
            if self._is_valid_position(*fwd_pos):
                x, y = fwd_pos
        # Error
        else:
            print(action)
            assert False, "Invalid action"

        return x, y, direction
    
    # Core Methods

    def reset(self, **kwargs):
        state = self.s0
        self.env.reset(**kwargs)
        if state != self.state_to_index[tuple(np.array((*self.env.unwrapped.agent_start_pos, self.env.unwrapped.agent_start_dir), dtype=np.int32))]:
            self.env.unwrapped.agent_pos = self.states[state][:2]
            self.env.unwrapped.agent_dir = self.states[state][2]
        assert self.state_to_index[tuple(self.observation())] == state
        return state
    
    def step(self, state, P):
        next_state, reward, done = self.act(state, P)
        for action in self.actions:
            if self.state_step(self.states[state], action) == self.states[next_state]:
                self.env.step(action)
        return next_state, reward, done

    def observation(self):
        """Transform observation."""
        obs = (*self.env.agent_pos, self.env.agent_dir)
        return np.array(obs, dtype=np.int32)
    
    def render(self):
        image = self.env.render()
        plt.imshow(image)
        plt.show()
    
    def terminal(self, x: int) -> bool:
        state = self.states[x]
        pos = self.env.grid.get(state[0], state[1])
        at_goal = pos is not None and pos.type == "goal"
        return at_goal
    
    def embedding_to_MDP(self):
        mdp = super().embedding_to_MDP()
        mdp_minigrid = Minigrid_MDP(self.grid_size, walls = self.env.walls, env = self.env, P = mdp.P, R = mdp.R)
        return mdp_minigrid
    
    # Auxiliary Methods
    
    def print_attributes(self):
        print("Number of states: ", self.n_states)
        print("Number of actions: ", self.n_actions)
        print("Number of grid cells: ", self.n_cells)
    
    def print_environment(self):
        print("States: ", self.states)
        print("Actions: ", self.actions)


    # minigrid_mdp = Minigrid_MDP(grid_size=15, walls = walls)
    # # Q-learning
    # print("Q-learning training...")
    # qlearning = QLearning(minigrid_mdp, gamma=0.95, learning_rate=0.25)
    # start_time = time.time()
    # _, _, q_lengths, q_throughputs = Qlearning_training(qlearning, n_steps=int(7e5))
    # print("--- %s minutes and %s seconds ---" % (int((time.time() - start_time)/60), int((time.time() - start_time) % 60)))
    # q_averaged_throughputs = plot_episode_throughput(q_throughputs, minigrid.grid_size, plot_batch=True)
    # compare_throughputs(z_averaged_throughputs, q_averaged_throughputs, minigrid.grid_size, name1 = 'Z Learning', name2 = 'Q Learning')


    #state = 0
    # q = minigrid.R[state]
    # m = np.log(minigrid.P0[state] + 1e-30)
    # print("q =", q)
    # print("m =", m)
    # ones = np.ones(minigrid.n_states)
    # c = q*ones-m
    # print("c =", c)
    # q2 = -np.log(np.sum(np.exp(-c)))
    # print("q from LMDP =", q2)

    # minigrid_mdp = Minigrid_MDP(grid_size=14)
    # D = minigrid_mdp.P[state]
    # print("D =", D)
    # #c[c == np.inf] = -1e-10
    # b2 = D@c
    # print("b from LMDP =", b2)
    # b = minigrid_mdp.R[state]
    # print("original b from MDP =", b)
    # c2 = np.linalg.lstsq(D, b, rcond=None)[0]
    # #Substitute 0 with 68
    # c2[c2 == 0] = 68
    # print("c from MDP =", c2)
    # c3 = np.linalg.lstsq(D, b2, rcond=None)[0]
    # c3[c3 == 0] = 68
    # print("c from LMDP =", c3)
    # q4 = -np.log(np.sum(np.exp(-c3)))
    # print("q from LMDP =", q4)
    # q3 = -np.log(np.sum(np.exp(-c2)))
    # print("q from MDP =", q3)
    # #print(c)
    # #print(c2)
    # #print(c.dtype, c2.dtype)
    # #print(c.shape, c2.shape)
    # D[D == 0] = 1e-30
    # print(np.log(D))
    # tmp = np.sum((D)*np.log(D), axis=1)
    # print(tmp)
    # b3 = minigrid_mdp.R[state] - tmp
    # print(b3)
    # c4 = np.linalg.lstsq(D, b3, rcond=None)[0]
    # print(c4)
    # q5 = -np.log(np.sum(np.exp(c4)))
    # print("q from MDP =", q5)


   

    