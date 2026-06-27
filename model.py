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
        H=1000,  # number of households
        F=100,  # number of firms
        num_typeA=7,  # type A connections per household
        # household parameters
        alpha=0.9,
        # firm parameters
        delta=0.019,
        Phi_min=1.025,
        Phi_max=1.15,
        phi_min=0.01,
        phi_max=2.0,
        theta=0.02,
        lambda_=1,
        gamma=24,
        Theta=0.75,
        # labour market parameters
        beta=5,
        pi=0.1,
        xi=0.01,
        Psi_price=0.25,
        Psi_quant=0.25,
        n=7,
        seed=1,
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
        self.day = 0  # current day within month (1-20)
        self.month = 0  # current month
        self.last_month_mean_price = None
        self.delta_p_history = []   # list of (delta_p, unemployment) tuples per month
        self.beveridge_history = []  # list of (vacancies, unemployment) tuples per month

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
                "Household Liquidity": self._get_household_liquidity,
                "Firm Liquidity":      self._get_firm_liquidity,
                "Mean Reservation Wage": self._get_mean_reservation_wage,
                "Price Dispersion":    self._get_price_dispersion,
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
            w = max(0.01, np.random.normal(1, 0.2))  # reservation wage
            m = max(0.01, np.random.normal(1, 0.2))  # liquidity
            c = random.randint(21, 105)  # initial consumption

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
            inv = random.uniform(0, 10)
            p = max(0.001, np.random.normal(0.05, 0.01))

            firm = Firm(
                model=self,
                w=w,
                m=0.0,
                inv=inv,
                inv_min=inv * 0.9,
                inv_max=inv * 1.1,
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
    
    def _get_household_liquidity(self):
        return sum(hh.m for hh in self.households)

    def _get_firm_liquidity(self):
        return sum(f.m + f.m_buffer for f in self.firms)

    def _get_mean_reservation_wage(self):
        return sum(hh.w for hh in self.households) / self.H

    def _get_price_dispersion(self):
        """Standard deviation of prices across firms — measures how much
        firms differ in price (key signal of competition strength)."""
        prices = [f.p for f in self.firms]
        mean = sum(prices) / self.F
        variance = sum((p - mean) ** 2 for p in prices) / self.F
        return variance ** 0.5
    
    def _get_firm_sizes(self):
        """Returns list of current employee counts per firm — for the histogram."""
        return [len(f.typeB) for f in self.firms]

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self):
        """
        One day of simulation. Mirrors Java event scheduling:
        - day 0: beginning-of-month events
        - every day: daily events (added later)
        - day 20: end-of-month events (added later)
        """
        if self.day == 0:
            self._beginning_of_month()

        # daily events - goods market then production
        self._good_market_daily_events()
        for firm in self.firms:
            firm.produce()
        
        if self.day == 20:
            self._end_of_month()
            self._record_monthly_phillips_point()

        self.datacollector.collect(self)

        # advance time
        self.day += 1
        if self.day == 21:
            self.day = 0
            self.month += 1

    # ------------------------------------------------------------------
    # Beginning of month
    # ------------------------------------------------------------------

    def _beginning_of_month(self):
        """
        Mirrors Java scheduleEvents() 'beginningMonth' group:
        1. Firms: new wage, update inventory range, update price range,
           update demand for labour (hiring/firing/price decisions)
        2. Process firing queue (model-level, mirrors Java updateTypeB's
           firing loop)
        3. Network rewiring: type A (price), type A (quantity), type B
        4. Households recompute average price (P) and consumption plan
        """
        # 1. firm-level monthly decisions
        for firm in self.firms:
            firm.new_wage()
            firm.update_inv_range()
            firm.update_price_range()
            firm.update_demand_for_labour()
            firm.d = 0.0        # reset demand counter - paper's d_old is "most recent month"

        # 2. process firing - mirrors Java per-firm firing loop in updateTypeB
        self._process_firing()

        # 3. labour market search and rewiring (hiring)
        self._update_typeB()

        # 4. goods market network rewiring (price and quantity based)
        self._update_typeA_price()
        self._update_typeA_quantity()

        # 5. households recompute P and plan monthly consumption
        self._update_households_average_prices()
        for hh in self.households:
            hh.update_consumption()

    def _process_firing(self):
        """
        Fire `to_fire` workers per firm, chosen at random.
        Mirrors Java updateTypeB() firing block exactly.
        """
        for firm in self.firms:
            for _ in range(firm.to_fire):
                if len(firm.typeB) == 0:
                    break
                idx = random.randint(0, len(firm.typeB) - 1)
                hh_id = firm.typeB.pop(idx)
                household = self.households[hh_id]
                household.employed = False
                household.typeB = None
            firm.to_fire = 0

    def _update_typeB(self):
        """
        Labour market search and rewiring.
        Mirrors Java updateTypeB() exactly (excluding the firing block,
        which we already handle separately in _process_firing).
        """
        for h in range(self.H):
            household = self.households[h]

            if household.employed:
                beta = 1
                employer = self.firms[household.typeB]
                prob = self.pi if household.w <= employer.w else 1.0
            else:
                beta = self.beta
                employer = None
                prob = 1.0

            if random.random() >= prob:
                continue

            # build temp list of candidate firms (exclude current employer)
            candidates = list(range(self.F))
            if household.employed:
                candidates.remove(household.typeB)

            for _ in range(beta):
                if not candidates:
                    break

                idx = random.randint(0, len(candidates) - 1)
                f_id = candidates[idx]
                firm = self.firms[f_id]

                if household.employed:
                    if firm.open_position > 0 and firm.w > employer.w:
                        # switch jobs
                        employer.typeB.remove(h)
                        firm.typeB.append(h)
                        firm.open_position -= 1
                        household.typeB = f_id
                        break
                else:
                    if firm.w >= household.w and firm.open_position > 0:
                        # take the job
                        firm.typeB.append(h)
                        firm.open_position -= 1
                        household.typeB = f_id
                        household.employed = True
                        break

                candidates.remove(f_id)
    
    def _update_typeA_price(self):
        """
        Households drop a current type A connection in favour of a cheaper one.
        Mirrors Java updateTypeA_Price().

        For each household, with probability Psi_price:
        - Pick a random current type A firm (f) and a random non-connected firm (f_new),
            where f_new is weighted by firm size (employee count).
        - If f_new's price is at least xi (1%) cheaper than f, swap.
        """
        for h in range(self.H):
            household = self.households[h]

            if random.random() >= self.Psi_price:
                continue

            # pick a random existing type A firm to potentially drop
            f_index = random.randint(0, self.num_typeA - 1)
            f_id = household.typeA[f_index]
            f = self.firms[f_id]

            # build pool of candidate non-connected firms, weighted by size
            non_connected = [
                (fid, len(self.firms[fid].typeB))
                for fid in range(self.F)
                if not self.matrix_A[h][fid]
            ]
            if not non_connected:
                continue

            total_weight = sum(weight for _, weight in non_connected)
            if total_weight == 0:
                # all firms have zero employees — fall back to uniform
                f_new_id = non_connected[random.randint(0, len(non_connected) - 1)][0]
            else:
                # weighted random selection by firm size
                pick = random.uniform(0, total_weight)
                cumulative = 0
                f_new_id = non_connected[-1][0]   # fallback
                for fid, weight in non_connected:
                    cumulative += weight
                    if cumulative >= pick:
                        f_new_id = fid
                        break      
            
            f_new = self.firms[f_new_id]

            # swap if f_new is at least xi cheaper
            if f.p > 0 and (f.p - f_new.p) / f.p >= self.xi:
                self.matrix_A[h][f_id] = False
                self.matrix_A[h][f_new_id] = True
                household.typeA[f_index] = f_new_id
                f.typeA.remove(h)
                f_new.typeA.append(h)
    
    def _update_typeA_quantity(self):
        """
        Households drop a type A firm that rationed them, in favour of a new one.
        Mirrors Java updateTypeA_Quantity().

        For each household with unmet demand last month, with probability Psi_quant:
        - Drop a firm weighted by how much it failed to satisfy demand.
        - Pick a uniformly random non-connected firm to replace it.
        """
        for h in range(self.H):
            household = self.households[h]

            # compute total unmet demand across this household's type A firms
            constraints = [self.matrix_A_constraints[h][fid] for fid in household.typeA]
            tot_constraint = sum(constraints)

            if tot_constraint <= 0:
                continue

            if random.random() >= self.Psi_quant:
                continue

            # weighted choice of which firm to drop
            pick = random.uniform(0, tot_constraint)
            cumulative = 0
            f_index_to_drop = 0
            for i, c in enumerate(constraints):
                cumulative += c
                if cumulative >= pick:
                    f_index_to_drop = i
                    break

            f_id = household.typeA[f_index_to_drop]
            f = self.firms[f_id]

            # uniformly random non-connected firm
            non_connected = [fid for fid in range(self.F) if not self.matrix_A[h][fid]]
            if not non_connected:
                continue
            f_new_id = non_connected[random.randint(0, len(non_connected) - 1)]
            f_new = self.firms[f_new_id]

            # swap
            self.matrix_A[h][f_id] = False
            self.matrix_A[h][f_new_id] = True
            household.typeA[f_index_to_drop] = f_new_id
            f.typeA.remove(h)
            f_new.typeA.append(h)

        # reset constraints matrix for next month
        self.matrix_A_constraints = [[0] * self.F for _ in range(self.H)]

    def _update_households_average_prices(self):
        """
        Compute each household's average type A price (P).
        Mirrors Java updateHouseholdsAveragePrices().
        """
        for hh in self.households:
            total = 0.0
            for f_id in hh.typeA:
                total += self.firms[f_id].p
                hh.P = total / self.num_typeA

    # ------------------------------------------------------------------
    # Daily events
    # ------------------------------------------------------------------

    def _good_market_daily_events(self):
        """
        Daily goods market — households visit firms and buy goods.
        Mirrors Java GoodMarketDailyEvents() faithfully.
        """
        # shuffle household order — each household acts once per day in random order
        order = list(range(self.H))
        random.shuffle(order)

        for h in order:
            household = self.households[h]

            # daily demand = monthly planned / 21, integer per Java cast
            daily_demand = household.c / 21
            if daily_demand <= 0:
                continue

            # candidate firms = household's type A connection IDs (list-indices)
            candidates = list(household.typeA)

            purchased = 0
            visited = 0

            while (
                household.m > 0
                and purchased / daily_demand < 0.95
                and visited < self.n
                and candidates
            ):
                idx = random.randint(0, len(candidates) - 1)
                f_id = candidates[idx]
                firm = self.firms[f_id]

                # record demand at the firm (note: this overcounts across firms,
                # but matches the Java implementation exactly)
                firm.d += daily_demand - purchased

                # how much the firm can supply
                txn = min(daily_demand - purchased, firm.inv)

                # record the unmet demand for type A quantity rewiring later
                unmet = daily_demand - purchased - txn
                self.matrix_A_constraints[h][f_id] = unmet

                # cap by household's liquidity
                if firm.p > 0:
                    txn = min(txn, household.m / firm.p)

                # execute transaction
                firm.inv -= txn
                firm.m += txn * firm.p
                household.m -= txn * firm.p
                purchased += txn

                # household won't return to this firm today
                candidates.pop(idx)
                visited += 1

    # ------------------------------------------------------------------
    # End of month
    # ------------------------------------------------------------------

    def _end_of_month(self):
        """
        1. Firms pay wages to employed households (drawing from m and m_buffer).
        2. Firms top up m_buffer relative to labour costs.
        3. Remaining firm liquidity distributed as profit proportional to
            household liquidity.
        4. Households update reservation wage based on this month's income.
        """
        self._firms_pay_wages()
        self._firms_pay_profits()
        for hh in self.households:
            hh.update_reservation_wage()

    def _record_monthly_phillips_point(self):
        """
        Record delta_p (price change) and current unemployment for the
        Phillips curve scatter plot. Called once per month after end-of-month.
        Also records vacancies for the Beveridge curve.
        """
        current_mean_price = self._get_mean_price()

        if self.last_month_mean_price is not None:
            delta_p = current_mean_price - self.last_month_mean_price
            unemployed = self.H - sum(1 for hh in self.households if hh.employed)
            self.delta_p_history.append((delta_p, unemployed))

            vacancies = sum(f.open_position for f in self.firms)
            self.beveridge_history.append((vacancies, unemployed))

        self.last_month_mean_price = current_mean_price

    def _firms_pay_wages(self):
        """
        Mirrors Java firmsPayWages().
        Each employed household receives its employer's offered wage w.
        Payment drawn first from m, then from m_buffer.
        Unemployed households receive nothing.
        """
        for hh in self.households:
            if not hh.employed or hh.typeB is None:
                continue

            firm = self.firms[hh.typeB]
            amount_paid = min(firm.w, firm.m + firm.m_buffer)
            hh.m += amount_paid

            # draw from m first, then from buffer
            from_m = min(firm.m, amount_paid)
            from_buffer = min(amount_paid - from_m, firm.m_buffer)
            firm.m -= from_m
            firm.m_buffer -= from_buffer

    def _firms_pay_profits(self):
        """
        Mirrors Java firmsPayProfits().
        All remaining firm liquidity is pooled and distributed to households
        proportional to each household's current liquidity (a proxy for
        stock ownership — eq. as in Section 2.4).
        """
        # pool aggregate firm liquidity
        aggregate_profit = 0.0
        for firm in self.firms:
            aggregate_profit += firm.m
            firm.m = 0.0

        # share of profit proportional to current liquidity
        aggregate_hh_wealth = sum(hh.m for hh in self.households)
        if aggregate_hh_wealth <= 0:
            return

        for hh in self.households:
            hh.m += aggregate_profit * (hh.m / aggregate_hh_wealth)
