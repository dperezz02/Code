from environments.minigrids import Minigrid_LMDP, Minigrid_LMDP_transition, Minigrid_MDP, generate_random_walls_and_lavas
from environments.blackjack import Black_Jack_MDP
import numpy as np
from utils.plot import Plotter, Minigrid_MDP_Plotter
from algs.zlearning import ZLearning, Zlearning_training
from algs.qlearning import QLearning, Qlearning_training
from utils.lmdp_plot import Minigrid_LMDP_Plotter

simple6_map = [
    "########",
    "#A     #",
    "#      #",
    "#  W   #",
    "#      #",
    "#      #",
    "#L    G#",
    "########"
]

hill13_map = [
    "#################",
    "#A              #",
    "# WLLLLLLLLLLLL #",
    "# WWWWWWWWWWWWL #",
    "# W   W   W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "# W W W W W  WL #",
    "#   W   W      G#",
    "#################"
]

maze13_map = [
    "###############",
    "#A    W       #",
    "# W W W W W W #",
    "# W   W W W W #",
    "# W W W W W W #",
    "# W W W W   W #",
    "# W W W WWWWW #",
    "# W     W     #",
    "# W WWWWW WWW #",
    "# W W   W   W #",
    "# WWW W W W W #",
    "#     W W W W #",
    "# WWWWW W W WW#",
    "#     W W    G#",
    "###############"
]

maze18_map = [
    "####################",
    "#A    W     W     G#",
    "#W W  W W W W W W  #",
    "#W W      W W W W  #",
    "#W W W W WWW  WWWWW#",
    "#W   W W   W   W   #",
    "#WWWWWWWWW WWW WW W#",
    "#  W   W     W W   #",
    "#  W W WWW W W W  W#",
    "#  W W   W W W     #",
    "#  W WW    WWWWW WW#",
    "#    W       W W W #",
    "#WWWWW WWWWW W W W #",
    "#W     W     W   W #",
    "#W WWWWW WWWWW WWW #",
    "#W     W     W     #",
    "#WWWWWWW WWWWWWW WW#",
    "#        W        W#",
    "#W W W W   W W W   #",
    "####################"
]

rooms18_map = [
    "######################",
    "#             W     G#",
    "#      W      W      #",
    "#      W      W      #",
    "#      W      W      #",
    "#      W      W      #",
    "#      W      W      #",
    "#WWWW WW WWWWWWW WWWWW#",
    "#      W      W      #",
    "#      W      W      #",
    "#      W      W      #",
    "#      W  A   W      #",
    "#      W      W      #",
    "#      W      W      #",
    "#W WWWWWWWWWWWWWWWWW W#",
    "#      W             #",
    "#      W      W      #",
    "#      W      W      #",
    "#      W      W      #",
    "#             W      #",
    "#      W      W      #",
    "######################"
]


if __name__ == "__main__":

    grid_size = 3
    wall_percentage = 10
    lava_percentage = 10
    objects = generate_random_walls_and_lavas(grid_size, wall_percentage, lava_percentage)
    objects = {"walls":[], "lavas":[]}

    grid_map = None
    grid_size = len(grid_map)-2 if grid_map is not None else grid_size

    gamma = 1
    epsilon = 1e-10
    n_iters = int(1e5)
    lmbda = 1

    # MDP
    minigrid_mdp = Minigrid_MDP(grid_size=grid_size, objects = objects, map=grid_map, gamma=gamma)


    # minigrid_mdp_plots = Minigrid_MDP_Plotter(minigrid_mdp)
    minigrid_lmdp = Minigrid_LMDP(grid_size=grid_size, objects=objects, map=grid_map, lmbda=lmbda)
    minigrid_lmdp_transition = Minigrid_LMDP_transition(grid_size=grid_size, objects=objects, map=grid_map, lmbda=lmbda)

    Z, n_steps = minigrid_lmdp.power_iteration(epsilon=epsilon)
    V = minigrid_lmdp.Z_to_V(Z)
    Z_2, n_steps_2 = minigrid_lmdp_transition.power_iteration(epsilon=epsilon)
    V_2 = minigrid_lmdp_transition.Z_to_V(Z_2)

    print(V, n_steps)
    print(V_2, n_steps_2)

    # for s in range(minigrid_lmdp.n_nonterminal_states):
    #     print("R[{}]: {}".format(minigrid_lmdp.states[s], minigrid_lmdp.R[s]))
    #     for s2 in range(minigrid_lmdp.n_states):
    #         print("R[{}][{}]: {}".format(minigrid_lmdp.states[s], minigrid_lmdp.states[s2], minigrid_lmdp_transition.R[s, s2]))
   