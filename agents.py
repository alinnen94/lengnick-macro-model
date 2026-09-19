from mesa import Agent
import numpy as np
import random
import math


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

        self.w = w  # reservation wage
        self.m = m  # liquidity
        self.c = c  # planned monthly consumption
        self.alpha = alpha  # consumption parameter
        self.P = 1.0  # average price of typeA firms
        self.employed = False
        self.typeA = [None] * num_typeA  # array of firm IDs (length = num_typeA)
        self.typeB = None  # single employer firm ID (None if unemployed)

    def update_consumption(self):
        """
        Update planned monthly consumption — equation (12).
        c = min((m/P)^alpha, m/P) — paper's true formula.
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

    def __init__(
        self,
        model,
        w,
        m,
        inv,
        inv_min,
        inv_max,
        p,
        p_min,
        p_max,
        delta,
        Phi_min,
        Phi_max,
        phi_min,
        phi_max,
        theta,
        lambda_,
        gamma,
        Theta,
    ):
        super().__init__(model)

        self.w = w  # offered wage
        self.m = m  # liquidity
        self.m_buffer = 0.0  # liquidity buffer
        self.inv = inv  # current inventory
        self.inv_min = inv_min  # lower inventory bound
        self.inv_max = inv_max  # upper inventory bound
        self.d = 0  # demand recieved last month
        self.p = p  # current price
        self.p_min = p_min  # lower price bound
        self.p_max = p_max  # upper price bound
        self.mc = w  # marginal cost = wage (fixed in Java, we set it explicitly)
        self.delta = delta
        self.Phi_min = Phi_min
        self.Phi_max = Phi_max
        self.phi_min = phi_min
        self.phi_max = phi_max
        self.theta = theta
        self.lambda_ = lambda_
        self.gamma = gamma
        self.Theta = Theta
        self.open_position = 0  # current open vacancies
        self.to_fire = 0  # workers to fire at start of next month
        self.num_months_with_open_positions = 0
        self.had_open_positions_last_month = False
        self.typeA = []  # list of household IDs buying from this firm
        self.typeB = []  # list of household IDs employed by this firm
        self.branch_run = 0 # +n = n consecutive months hiring, -n = firing

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
        self.inv_max = self.Phi_max * self.d
        self.inv_min = self.Phi_min * self.d

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

        Divergences from the original Java, all deliberate:
        - Wage only falls if previously-open positions were filled, not
          whenever open_position == 0 (Java's version spirals wages to zero).
        - Hiring/firing scales with the inventory gap, capped at 3 workers
          per month, rather than a flat 1 (the paper's one-per-month limit
          leaves large firms permanently unable to reach their target).
        - A firm with no workers always hires and never adjusts price
          (see the guard below).
        """
        # --- wage adjustment based on open position history ---
        if self.open_position > 0:
            self.num_months_with_open_positions += 1
        elif self.had_open_positions_last_month:
            self.w *= 0.9   # positions were filled — reduce wage

        if self.num_months_with_open_positions == self.gamma:
            self.w *= 1.1   # open for gamma months — raise wage
            self.num_months_with_open_positions = 0

        self.had_open_positions_last_month = self.open_position > 0

        d = self.model.diag
        monthly_output_per_worker = self.lambda_ * 21

        # --- a firm with no workers is dead and must hire ---
        # Without this it can be trapped permanently in whichever branch its
        # inventory happens to fall in: stuck above inv_max it never
        # advertises (so the labour market cannot rescue it) and cuts price
        # every month; stuck below inv_min it ratchets price up forever.
        # The paper assumes firms always operate and never covers this case.
        if len(self.typeB) == 0:
            d["hire_branch"] += 1
            self.branch_run = self.branch_run + 1 if self.branch_run > 0 else 1
            self.open_position += 1
            d["vacancies_created"] += 1
            return

        # --- inventory vs bounds: hire, fire, or adjust price ---
        if self.inv < self.inv_min:
            d["hire_branch"] += 1
            self.branch_run = self.branch_run + 1 if self.branch_run > 0 else 1

            gap = self.inv_min - self.inv
            needed = (math.ceil(gap / monthly_output_per_worker)
                      if monthly_output_per_worker > 0 else 1)
            added = max(1, min(needed, 3))
            self.open_position += added
            d["vacancies_created"] += added

            if self.p >= self.p_max:
                d["price_up_blocked_by_pmax"] += 1
            elif random.random() < self.Theta:
                self.increase_price()
                d["price_up_executed"] += 1
            else:
                d["price_up_skipped_prob"] += 1

        elif self.inv > self.inv_max:
            d["fire_branch"] += 1
            self.branch_run = self.branch_run - 1 if self.branch_run < 0 else -1

            surplus = self.inv - self.inv_max
            excess = (math.ceil(surplus / monthly_output_per_worker)
                      if monthly_output_per_worker > 0 else 1)
            self.to_fire += max(1, min(excess, 3))

            if self.p <= self.p_min:
                d["price_down_blocked_by_pmin"] += 1
            elif random.random() < self.Theta:
                self.decrease_price()
                d["price_down_executed"] += 1
            else:
                d["price_down_skipped_prob"] += 1

        else:
            d["no_branch"] += 1
            self.branch_run = 0

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
