from mesa import Agent
import numpy as np
import random

class Household(Agent):
    """
    Household agent following Lengnick (2013).
    
    Attributes
    ----------
    unique_id : int
    model : LengnickModel
    w : float
        Reservation wage (omega in paper).
    m : float
        Initial liquidity.
    c : int
        Initial consumption (randomised at init, updated monthly).
    num_typeA : int
        Number of type A firm connections (fixed at 7 per paper).
    alpha : float
        Consumption parameter (eq. 12).
    """

    def __init__(self, unique_id, model, w, m, c, num_typeA, alpha):
        super().__init__(unique_id, model)

        self.w = w                          # reservation wage
        self.m = m                          # liquidity
        self.c = c                          # planned monthly consumption
        self.alpha = alpha                  # consumption parameter
        self.P = 1.0                        # average price of typeA firms
        self.employed = False
        self.typeA = [None] * num_typeA     # array of firm IDs (length = num_typeA)
        self.typeB = None                   # single employer firm ID (None if unemployed)
    
    def update_consumption(self):
        """
        Update planned monthly consumption.
        Mirrors Java: Math.min((m/P) * Math.exp(alpha), m/P)
        Budget constraint: never exceeds m/P.
        """
        if self.P > 0 and self.m > 0:
            unconstrained = (self.m / self.P) * np.exp(self.alpha)
            budget_limit = self.m / self.P
            self.c = min(unconstrained, budget_limit)
        else:
            self.c = 0.0
    
    def update_reservation_wage(self):
        """
        Called at the end of the month (Section 2.4).
        - Employeed: if current employer wage > reservation wage, raise omega to match.
        - Unemployed: reduce reservation wage by 10%.
        """
        if self.employed and self.typeB is not None:
            employer = self.model.firms[self.typeB]
            if employer.w > self.w:
                self.w = employer.w
        elif not self.employed:
            self.w *= 0.9
