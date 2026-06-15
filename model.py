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
