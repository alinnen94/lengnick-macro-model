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

    def __init__(self, model, w, m, c, num_typeA, alpha):
        super().__init__(model)

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

class Firm(Agent):
    """
    Firm agent following Lengnick (2013).
    
    Attributes
    ----------
    unique_id : int
    model : LengnickModel
    w : float
        Wage offered by the firm.
    m : float
        Initial liquidity.
    inv : int
        Initial inventory.
    inv_min : int
        Lower inventory bound (updated monthly via eq. 6).
    inv_max : int
        Upper inventory bound (updated monthly via eq. 7).
    p : float
        Price of the firm's product.
    p_min : float
        Lower price bound (updated monthly via eq. 9).
    p_max : float
        Upper price bound (updated monthly via eq. 8).
    delta : float
        Wage adjustment parameter (eq. 5).
    Phi_min: float
        Lower inventory scaling factor (eq. 6).
    Phi_max: float
        Upper inventory scaling factor (eq. 7).
    phi_min: float
        Lower price scaling factor (eq. 9).
    phi_max: float
        Upper price scaling factor (eq. 8).
    theta : float
        Price adjustment parameter (eq. 10).
    lambda_ : int
        Labour productivity - units produced per worker per day (eq. 13-14).
    gamma : int
        Months threshold before wage is raised (Section 2.2).
    Theta : float
        Probability of considering a price change (Fig. 3).
    """

    def __init__(self, model, w, m, inv, inv_min, inv_max, p, p_min, p_max,
                 delta, Phi_min, Phi_max, phi_min, phi_max, theta, lambda_, gamma, Theta):
        super().__init__(model)

        self.w = w                              # offered wage
        self.m = m                              # liquidity
        self.m_buffer = 0.0                     # liquidity buffer
        self.inv = inv                          # current inventory
        self.inv_min = inv_min                  # lower inventory bound
        self.inv_max = inv_max                  # upper inventory bound
        self. d = 0                             # demand recieved last month
        self.p = p                              # current price
        self.p_min = p_min                      # lower price bound
        self.p_max = p_max                      # upper price bound
        self.mc = w                             # marginal cost = wage (fixed in Java, we set it explicitly)
        self.delta = delta
        self.Phi_min = Phi_min
        self.Phi_max = Phi_max
        self.phi_min = phi_min
        self.phi_max = phi_max
        self.theta = theta
        self.lambda_ = lambda_
        self.gamma = gamma
        self.Theta = Theta
        self.open_position = 0                  # current open vacancies
        self.to_fire = 0                        # workers to fire at start of next month
        self.num_months_with_open_positions = 0
        self.typeA = []                         # list of household IDs buying from this firm
        self.typeB = []                         # list of household IDs employed by this firm
    
    # --- Monthly methods ---

    def new_wage(self):
        """
        Adjust wage randomly within [-delta, delta] range.
        Equation (5). Mirrors Java newWage() method.
        """
        self.w = self.w * (1 + random.uniform(-self.delta, self.delta))
    
    def update_inv_range(self):
        """
        Recalculate inventory bounds based on last month's demand.
        Equations (8) and (9). Mirrors Java updateInvRange() method.
        """
        self.inv_max = int(self.Phi_max * self.d)
        self.inv_min = int(self.Phi_min * self.d)
    
    def update_price_range(self):
        """
        Recalculate price bounds based on marginal cost.
        Equations (8) and (9). Mirrors Java updatePriceRange() method.
        Marginal cost is the firm's current wage rate.
        """
        self.mc = self.w
        self.p_max = self.phi_max * self.mc
        self.p_min = self.phi_min * self.mc
    
    def update_demand_for_labour(self):
        """
        Hiring/firing and price adjustment decisions.
        Mirrors Java updateDemandForLabour() method and Fig. 3 flow chart.
        """
        # wage adjustment based on open position history
        if self.open_position > 0:
            self.num_months_with_open_positions += 1
        else:
            self.w *= 0.9 # all positions filled - reduce wage
        
        if self.num_months_with_open_positions == self.gamma:
            self.w *= 1.1 # had open positions for gamma months - raise wage
            self.num_months_with_open_positions = 0
        
        # inventory vs bounds - hire, fire, or adjust price
        if self.inv < self.inv_min:
            self.open_position += 1
            if self.p < self.p_max and random.random() < self.Theta:
                self.increase_price()
        elif self.inv > self.inv_max:
            self.to_fire += 1
            if self.p > self.p_min and random.random() < self.Theta:
                self.decrease_price()
    
    def increase_price(self):
        """Equation (10) - raise price by random factor within [0, theta] range."""
        self.p = self.p * (1 + random.uniform(0, self.theta))
    
    def decrease_price(self):
        """Equation (10) - lower price by random factor within [0, theta] range."""
        self.p = self.p * (1 - random.uniform(0, self.theta))
    
    # --- Daily methods ---

    def produce(self):
        """
        Production function - equations (13) and (14).
        Each working produces lambda_ units per day.
        Mirrors Java produce() method.
        """
        self.inv += self.lambda_ * len(self.typeB)
