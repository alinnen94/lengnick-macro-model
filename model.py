from mesa import Model
from mesa.datacollection import DataCollector
import numpy as np
import random

from agents import Household, Firm


class LengnickModel(Model):
    """
    Lengnick (2013) baseline agent-based macroeconomic model.
    """

    def __init__(
            self,
            H=1000,             # number of households
            F=100,              # number of firms
            num_typeA=7,        # type A connections per household
            # household parameters
            alpha=0.9,
            # firm parameters
            delta=0.019,
            Phi_min=1.025,
            Phi_max=1.15,
            phi_min=0.25,
            phi_max=1.0,
            theta=0.02,
            lambda_=3,
            gamma=24,
            Theta=0.75,
            # labour market parameters
            beta=5,
            pi=0.1,
            xi=0.01,
            Psi_price=0.25,
            Psi_quant=0.25,
            n=7,
            seed=1
        ):
            super().__init__()

            # store parameters
            self.H = H
            self.F = F
            self.num_typeA = num_typeA
            self.alpha = alpha
            self.delta = delta
            self.Phi_min = Phi_min
            self.Phi_max = Phi_max
            self.phi_min = phi_min
            self.phi_max = phi_max
            self.theta = theta
            self.lambda_ = lambda_
            self.gamma = gamma
            self.Theta = Theta
            self.beta = beta
            self.pi = pi
            self.xi = xi
            self.Psi_price = Psi_price
            self.Psi_quant = Psi_quant
            self.n = n

            # set random seeds for reproducibility
            random.seed(seed)
            np.random.seed(seed)

            # time tracking
            self.day = 0        # current day within month (1-20)
            self.month = 0      # current month

            # connection matrices - mirrors Java matrix_A and matrix_B
            self.matrix_A = [[False] * F for _ in range(H)]
            self.matrix_B = [[False] * F for _ in range(H)]
            self.matrix_A_constraints = [[0] * F for _ in range(H)]

            # initialise agents
            self._init_households()
            self._init_firms()
            self._init_connections()

            # data collector
            self.datacollector = DataCollector(
                model_reporters={
                      "Employment Rate": self._get_employment_rate,
                      "Mean Price": self._get_mean_price,
                      "Mean Wage": self._get_mean_wage,
                      "Total Production": self._get_total_production,
                      }
            )

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_households(self):
          """
          Create households with randomised starting values.
          Mirrors Java buildModel() household loop.
          """
          self.households = []

          for i in range(self.H):
                w = max(0.01, np.random.normal(1, 0.2))     # reservation wage
                m = max(0.01, np.random.normal(1, 0.2))     # liquidity
                c = random.randint(21, 105)                 # initial consumption

                hh = Household(
                    model=self,
                    w=w,
                    m=m,
                    c=c,
                    num_typeA=self.num_typeA,
                    alpha=self.alpha,
                )
                self.households.append(hh)
    
    def _init_firms(self):
          """
          Create firms with randomised starting values.
          Mirrors Java buildModel() firm loop.
          """
          self.firms = []

          for i in range(self.F):
                w = max(0.01, np.random.normal(1, 0.2))
                inv = random.randint(0, 10)
                p = max(0.001, np.random.normal(0.1, 0.02))

                firm = Firm(
                    model=self,
                    w=w,
                    m=0.0,
                    inv=inv,
                    inv_min=int(inv * 0.9),
                    inv_max=int(inv * 1.1),
                    p=p,
                    p_min=p * 0.9,
                    p_max=p * 1.1,
                    delta=self.delta,
                    Phi_min=self.Phi_min,
                    Phi_max=self.Phi_max,
                    phi_min=self.phi_min,
                    phi_max=self.phi_max,
                    theta=self.theta,
                    lambda_=self.lambda_,
                    gamma=self.gamma,
                    Theta=self.Theta,
                )
                self.firms.append(firm)
    
    def _init_connections(self):
          """
          Wire up type A and type B connections.
          Mirrors Java buildModel() connection loop.
          """
          for h in range(self.H):
                hh = self.households[h]

                # type B - assign one employer at random
                f = self.random.randint(0, self.F - 1)
                self.matrix_B[h][f] = True
                hh.typeB = f
                hh.employed = True
                self.firms[f].typeB.append(h)

                # type A - assign num_typeA distinct firms
                counter = 0
                while counter < self.num_typeA:
                      f = random.randint(0, self.F - 1)
                      if not self.matrix_A[h][f]:
                            self.matrix_A[h][f] = True
                            hh.typeA[counter] = f
                            self.firms[f].typeA.append(h)
                            counter += 1

    # ------------------------------------------------------------------
    # Data collector reporters
    # ------------------------------------------------------------------

    def _get_employment_rate(self):
          employed = sum(1 for hh in self.households if hh.employed)
          return (employed / self.H) * 100
    
    def _get_mean_price(self):
          return sum(f.p for f in self.firms) / self.F
    
    def _get_mean_wage(self):
          return sum(f.w for f in self.firms) / self.F
    
    def _get_total_production(self):
          return sum(f.lambda_ * len(f.typeB) for f in self.firms)

    # ------------------------------------------------------------------
    # Step — placeholder for now
    # ------------------------------------------------------------------

    def step(self):
          self.datacollector.collect(self)
