import random
import matplotlib.pyplot as plt

trials = 1000000

Zs = []
Qs = []

sums = []

for i in range(trials):
    X = random.uniform(0, 1)
    Y = random.uniform(0, 1)

    Z = max(X, Y)
    Zs.append(Z)

    Q = min(X, Y)
    Qs.append(Q)


plt.hist(Zs, bins=100)
plt.show()
plt.hist(Qs, bins=100)
plt.show()
