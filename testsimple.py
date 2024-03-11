
from lmdp_utils import power_iteration
from environments.simplegrid import SimpleGrid

if __name__ == "__main__":
    g = SimpleGrid(2)
    Z, nsteps = power_iteration(g, 1)
    print(Z)
    
