

Working notes for the [[PPA]] volume-over-time paper. Every stage below adds exactly one ingredient to the previous one and comes with a numerical example you can reproduce by hand.

  ## The ladder


| Stage | Ingredient added                       | Question answered                 | Result                                   |
| ----- | -------------------------------------- | --------------------------------- | ---------------------------------------- |
| 0     | Profit, utility, disagreement, surplus | What is a contract worth?         | Definitions                              |
| 1     | Deterministic prices                   | Does a contract emerge?           | No                                       |
| 2     | The swap decomposition                 | Why not?                          | A PPA is a derivative, so it is zero sum |
| 3     | Uncertainty, risk neutral              | Does uncertainty help?            | No                                       |
| 4     | CVaR                                   | What creates surplus?             | Risk premia, cancelled                   |
| 5     | Asymmetric risk aversion               | Who pays whom?                    | The strike price moves                   |
| 6     | A second hour, volume over time        | Does the delivery path matter?    | Only if risk averse                      |
| 7     | Who picks the path                     | Nominated versus shared           | Efficiency gap                           |
| 8     | Honest information                     | Is the value real?                | Foresight inflates it                    |
| 9     | Non anticipativity                     | How is information modelled?      | Scenario trees, and why they fail        |
| 10    | The MDP                                | How do we scale to 168 hours?     | State and value function                 |
| 11    | Back to the bilevel                    | What does the lower level return? | $V(Q)$                                   |
| 12    | The catch                              | What breaks?                      | CVaR is not time additive                |

---

## Stage 0. The three objects you need

- **Profit** $\phi^i_\omega$: a number per party $i \in \{S, B\}$ per scenario $\omega$.
- **Utility** $u^i$: a single number summarising the whole profit distribution. Read it as a *certainty equivalent*, the certain amount of money the party would accept instead of the random profit.
- **Disagreement point** $d^i$: the utility when no contract is signed. This is the threat point of the negotiation.

The gain from signing is $u^i - d^i$. The Nash bargaining solution maximises the **Nash product** $(u^S - d^S)(u^B - d^B)$, subject to both factors being non negative (nobody signs something that makes them worse off than walking away).

*Example*
For a seller a contract returns a utility of +20, while the disagreement point is +5. For a buyer the disagreement point leads to a cost of -20, but with a contract the total costs goes down to -5.
- The surplus for the seller is (+20) - (+5) = +15. Positive!
	- I increased my profit by 15. That increase signals that I am better off with a contract.
- The surplus for the buyer is (-5) - (-20) = +15. Positive!
	- By having a contract, I reduced my cost of 15. Doing a contract for me is better off!

Note that in this example $W = 15 + 15 = 30 > 0$: both parties gain at the same time, so a contract is signed and the Nash product is $15 \times 15 = 225$. Keep that number in mind, because Stage 1 shows that with deterministic prices and linear utilities such a pair of numbers is **impossible**. The whole ladder is the story of what has to be added to the model before the situation described here can actually arise.


The quantity that decides everything is the **joint surplus**:
$$W = (u^S - d^S) + (u^B - d^B)$$
If $W = 0$, the two factors cannot both be positive, so the best the Nash product can do is zero, which is the no contract outcome. **Every "no contract" result you have seen is a statement that $W = 0$.** The rest of these notes is about what makes $W$ strictly positive.

---

## Stage 1. Deterministic prices: nothing happens

**Setup.** One hour. Day ahead price $\lambda^{DA} = 50$ EUR/MWh, known with certainty. Seller produces $P = 10$ MWh, buyer consumes $D = 10$ MWh. The contract delivers $M$ MWh at strike price $\lambda$.

**Profits.**
The profit of the **seller** is the contract revenue plus whatever it sells merchant:
$$\phi^S = \lambda M + \lambda^{DA} (P^S - M)$$
which in this case takes the value
$$\phi^S = \lambda M + 50\,(10 - M) = 500 + M(\lambda - 50)$$

The profit of the **buyer** is minus the contract payment, minus the cost of buying the rest at spot:
$$\phi^B = -\lambda M + \lambda^{DA}(M - D^B) = -\lambda M - 50\,(10 - M) = -500 - M(\lambda - 50)$$
With no uncertainty, utility is just profit, $u^i = \phi^i$. At $M = 0$ we get $d^S = 500$ and $d^B = -500$.

### The general proof that $W = 0$

The numerical example above uses $P^S = D^B = 10$, but nothing depends on that. Write out the four objects for arbitrary production and demand:
- $\phi^S = \lambda M + \lambda^{DA} (P^S - M)$
- $d^S = \lambda^{DA} P^S$
- $\phi^B = -\lambda M + \lambda^{DA} (M - D^B)$
- $d^B = - \lambda^{DA} D^B$

The joint surplus is then
$$W = (u^S - d^S) + (u^B - d^B)$$
$$W = (\lambda M + \lambda^{DA} (P^S - M) - \lambda^{DA} P^S) + (-\lambda M + \lambda^{DA} (M - D^B) - (- \lambda^{DA} D^B))$$
$$W = (\lambda M + \lambda^{DA} P^S -  \lambda^{DA} M - \lambda^{DA} P^S) + (-\lambda M + \lambda^{DA} M - \lambda^{DA} D^B + \lambda^{DA} D^B)$$
$$W = (\lambda M -  \lambda^{DA} M ) + (-\lambda M + \lambda^{DA} M )$$
$$W = 0$$

**Two things worth extracting from this derivation, because they are used repeatedly later.**

First, look at *where* the cancellation happens. It is not that the two parties cancel against each other at the end. Each party's merchant term cancels against **its own** disagreement point, before the two are added:
$$u^S - d^S = M(\lambda - \lambda^{DA}), \qquad u^B - d^B = -M(\lambda - \lambda^{DA})$$
The quantities $P^S$ and $D^B$ vanish on their own. This is why the result survives any change to production or demand, and it is also why the size of the parties is irrelevant to whether a contract exists.

Second, what is left after the cancellation is exactly the swap payoff $M(\lambda - \lambda^{DA})$, held with opposite sign. So this derivation already *proves* the decomposition that Stage 2 states: the gain from a PPA is the swap, and nothing else.


**Numerical example.** Fix $M = 10$ and sweep the strike price.

| $\lambda$ | $u^S - d^S$ | $u^B - d^B$ | $W$ | Nash product |
| --------- | ----------- | ----------- | --- | ------------ |
| 55        | +50         | -50         | 0   | -2500        |
| 52        | +20         | -20         | 0   | -400         |
| 50        | 0           | 0           | 0   | 0            |
| 45        | -50         | +50         | 0   | -2500        |
Every euro the seller gains, the buyer loses. The Nash product equals $-[M(\lambda - 50)]^2 \le 0$ and is maximised at zero. **No contract.**


Notice that no choice of $M$ helps either: the product is zero only when $\lambda = 50$ or $M = 0$, and in both cases nothing of value has happened.


---
## Stage 2. Why: the contract is a pure transfer

Split the profit into what each party would have had anyway, plus what the contract adds:


$$\phi^S = \underbrace{\lambda^{DA} P}_{\text{merchant position}} + \underbrace{M(\lambda - \lambda^{DA})}_{\text{swap}}$$
$$\phi^B = \underbrace{-\lambda^{DA} D}_{\text{merchant position}} - \underbrace{M(\lambda - \lambda^{DA})}_{\text{swap}}$$


The merchant terms are unaffected by the contract. What the PPA *adds* is the second term: a fixed for floating swap, or contract for difference, on $M$ MWh at strike $\lambda$. The two parties hold it with **opposite sign**.


A swap is a pure derivative. It is in zero net supply. It creates no energy, saves no fuel, builds no turbine. It moves cash from one pocket to another. Therefore, scenario by scenario,
$$\phi^S_\omega + \phi^B_\omega = \lambda^{DA}_\omega (P - D)$$
which contains no $\lambda$, no $M$, and later no delivery path. This is `prop:zerosum` in the paper.

**The single sentence to remember.** *A PPA can only create value by moving risk to whoever minds it less. If nobody minds risk, it creates nothing.*


**Numerical check.** From Stage 1, at $\lambda = 55$, $M = 10$:
- $\phi^S = 550$, $\phi^B = -550$, sum $= 0 = 50 \cdot (10 - 10)$. At $\lambda = 45$:
- $\phi^S = 450$, $\phi^B = -450$, sum $= 0$. The sum never moves.

### The bargaining frontier, and what a slope of $-1$ means

The zero sum identity is much easier to use once it is drawn. Put the seller's gain $x = u^S - d^S$ on the horizontal axis and the buyer's gain $y = u^B - d^B$ on the vertical one. Every admissible contract is one point in this plane. The **bargaining set** is the collection of all such points, and the **bargaining frontier** is its upper right boundary: the contracts you cannot improve for one party without hurting the other. The disagreement point sits at the origin $(0,0)$ by construction.

The frontier's **slope** $\mathrm{d}y / \mathrm{d}x$ is the object that matters. It is an *exchange rate*: how many euros of buyer utility are destroyed per euro of seller utility created, as you slide along the frontier. Compute it for the Stage 1 contract by differentiating with respect to the strike price:

$$\frac{\mathrm{d}x}{\mathrm{d}\lambda} = +M, \qquad \frac{\mathrm{d}y}{\mathrm{d}\lambda} = -M \qquad \Longrightarrow \qquad \frac{\mathrm{d}y}{\mathrm{d}x} = \frac{-M}{+M} = -1$$
![[stage_2_zero_sum.png|481]]
**Numerical example.** $M = 10$, sweeping the strike price:

| $\lambda$ | $x = u^S - d^S$ | $y = u^B - d^B$ | $x + y$ |
| --------- | --------------- | --------------- | ------- |
| 45        | -50             | +50             | 0       |
| 48        | -20             | +20             | 0       |
| 50        | 0               | 0               | 0       |
| 52        | +20             | -20             | 0       |
| 55        | +50             | -50             | 0       |

Raise the strike by $1$ EUR/MWh and the seller gains exactly $10$ while the buyer loses exactly $10$. The points trace a straight line of slope $-1$, and because the disagreement point lies on it, that line is $x + y = 0$.

**What slope $-1$ means.** The exchange rate is one for one. Nothing is gained or lost in the act of transferring: utility is *perfectly transferable*, like handing over cash. Compare three cases:

| slope of frontier             | interpretation                                                                          |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| steeper than $-1$, say $-7$   | giving the seller 1 euro costs the buyer 7. The move destroys 6 euros of joint value.   |
| exactly $-1$                  | pure transfer. Joint value unchanged.                                                   |
| flatter than $-1$, say $-0.2$ | giving the seller 1 euro costs the buyer only 0.2. The move creates 0.8 euros of value. |

This gives a rule you can apply everywhere in the paper. Write the frontier as $y = F(x)$. Then

$$W = x + F(x), \qquad \frac{\mathrm{d}W}{\mathrm{d}x} = 1 + F'(x)$$

so the joint surplus stops changing exactly where $F'(x) = -1$.


> **The rule.** *Wherever the frontier's slope differs from $-1$, there is an unexploited joint gain. The efficient contract is where the slope equals $-1$. A direction with slope exactly $-1$ everywhere can only redistribute, never create.*

The strike price is precisely such a direction: its slope is $-1$ identically, at every price, in every model in this paper. That is why **the strike price can never be the source of value.** It sets the split and nothing else.

**Why Stage 1 fails, restated geometrically.** The frontier is a line of slope $-1$ that passes *through the origin*. The Nash product $xy$ is negative everywhere on it except at the origin itself, where it is zero. There is no point with $x > 0$ and $y > 0$, because $x + y = 0$ forbids it. The only question left for the rest of these notes is: **what pushes that line away from the origin?**

---

## Stage 3. Add uncertainty, stay risk neutral: still nothing

**Setup.** Same hour, but now $\lambda^{DA} = 20$ or $80$, each with probability $0.5$, so $\mathbb{E}[\lambda^{DA}] = 50$. Still $P = D = 10$. Utility is expected profit.

$$\mathbb{E}[\phi^S] = 500 + M(\lambda - 50)$$

This is **algebraically identical to Stage 1**. Expectation is a linear operator and the contract payoff is linear in the price, so the randomness cancels term by term. $d^S = 500$, $d^B = -500$, $W \equiv 0$, no contract.

**But look at what the contract actually did.** Take the full hedge $M = 10$, $\lambda = 50$:

|                       | $\lambda^{DA} = 20$ | $\lambda^{DA} = 80$ | mean |
| --------------------- | ------------------- | ------------------- | ---- |
| Seller, no contract   | 200                 | 800                 | 500  |
| Seller, with contract | **500**             | **500**             | 500  |
| Buyer, no contract    | -200                | -800                | -500 |
| Buyer, with contract  | **-500**            | **-500**            | -500 |

Check one cell. In the high price scenario the seller earns  $\phi^S = \lambda^{DA} P + M(\lambda - \lambda^{DA}) = 800 + 10(50 - 80) = 500$.

The merchant revenue rose by $300$ and the swap lost exactly $300$. With $M = P = 10$ the whole production is contracted, so the seller is fully hedged in both scenarios.

The contract turned a coin flip into a certainty **for both parties simultaneously**. This is not a transfer of risk from one to the other. It is an outright *cancellation*, because the seller is naturally **long** the price (revenue rises with price) and the buyer is naturally **short** it (cost rises with price). Their exposures are mirror images and the swap nets them out.

A risk neutral agent is by definition indifferent between $\{200, 800\}$ and a certain $500$. So it will not pay a cent for this. **Uncertainty is necessary but not sufficient. You also need someone who dislikes it.**

---

## Stage 4. Add CVaR: the contract appears

### What CVaR is
$\mathrm{CVaR}_\beta$ (conditional value at risk, or expected shortfall) is the **average of the worst $(1 - \beta)$ fraction of outcomes**. Larger is better, because we apply it to profits.

*Numerical example.* Four equiprobable profit outcomes $\{100, 300, 500, 900\}$, mean $450$.

| measure                | worst fraction                 | value |
| ---------------------- | ------------------------------ | ----- |
| $\mathbb{E}$           | all                            | 450   |
| $\mathrm{CVaR}_{0.5}$  | worst 50%, i.e. $\{100, 300\}$ | 200   |
| $\mathrm{CVaR}_{0.75}$ | worst 25%, i.e. $\{100\}$      | 100   |
The utility used in the paper is
$$u^i = (1 - A_i)\, \mathbb{E}[\phi^i] + A_i\, \mathrm{CVaR}_{\beta_i}(\phi^i)$$
with $A_i = 0$ recovering risk neutrality and $A_i = 1$ giving pure CVaR. It is **concave** in the profit vector, and that concavity is the entire source of value.

> **Notation warning.** $A_i$ with a **subscript** is the risk aversion weight of party $i$. From Stage 6 onward, $m^S$ and $m^B$ with a **superscript** denote the *merchant utility*, that is, the utility of the residual market position only. The paper currently calls that second object $A^S$ and $A^B$ in `prop:decoupling`, which clashes with the symbol used here for risk aversion. The paper should be renamed to $m^i$ to match.

### Step 0: the input data, in full

Everything in this stage comes from these numbers and nothing else.

| primitive                      | symbol                     | value                           |
| ------------------------------ | -------------------------- | ------------------------------- |
| number of hours                | $T$                        | 1                               |
| number of scenarios            | $\vert\Omega\vert$         | 2                               |
| probability of each scenario   | $\pi_\omega$               | $0.5$ and $0.5$                 |
| day ahead price, low scenario  | $\lambda^{DA}_L$           | 20 EUR/MWh                      |
| day ahead price, high scenario | $\lambda^{DA}_H$           | 80 EUR/MWh                      |
| expected price                 | $\mathbb{E}[\lambda^{DA}]$ | 50 EUR/MWh                      |
| seller production              | $P^S$                      | 10 MWh, same in both scenarios  |
| buyer demand                   | $D^B$                      | 10 MWh, same in both scenarios  |
| CVaR confidence level          | $\beta_S = \beta_B$        | $0.5$                           |
| seller risk aversion           | $A_S$                      | free, studied below             |
| buyer risk aversion            | $A_B$                      | free, studied below             |

Only the **price** is uncertain. Production and demand are deterministic and equal, which is deliberate: it removes volume risk entirely, so whatever surplus appears cannot be attributed to anything except price risk.

The two decision variables are the contracted volume $M$ and the strike price $\lambda$. The Stage 1 profit formulas, evaluated scenario by scenario:

$$\phi^S_\omega = \lambda M + \lambda^{DA}_\omega (10 - M), \qquad \phi^B_\omega = -\lambda M + \lambda^{DA}_\omega (M - 10)$$

### Step 1: the cash table, where the zero sum property is still intact

Take two contracts: no contract at all ($M = 0$), and the **perfect hedge** $M = P^S = 10$ at $\lambda = 50$. All eight numbers:

| contract               | party   | $\omega_L$ ($\lambda^{DA} = 20$) | $\omega_H$ ($\lambda^{DA} = 80$) |
| ---------------------- | ------- | -------------------------------- | -------------------------------- |
| $M = 0$                | seller  | $20 \times 10 = 200$             | $80 \times 10 = 800$             |
| $M = 0$                | buyer   | $-200$                           | $-800$                           |
|                        | **sum** | **0**                            | **0**                            |
| $M = 10, \lambda = 50$ | seller  | $50(10) + 20(0) = 500$           | $50(10) + 80(0) = 500$           |
| $M = 10, \lambda = 50$ | buyer   | $-500$                           | $-500$                           |
|                        | **sum** | **0**                            | **0**                            |

**Read the two bold rows carefully. The cash is still exactly zero sum, in every scenario, before and after the contract.** Not one euro has been created. Stage 2 has not gone away and never will.

What *did* change is the shape of each distribution:

| party  | no contract       | with perfect hedge | spread destroyed |
| ------ | ----------------- | ------------------ | ---------------- |
| seller | $\{200,\ 800\}$   | $\{500,\ 500\}$    | 600              |
| buyer  | $\{-200,\ -800\}$ | $\{-500,\ -500\}$  | 600              |

Both distributions collapsed to a point **at the same time**, with no cash moving in aggregate. That simultaneity is possible only because the seller is long the price and the buyer is short it.

### Step 2: from cash to utility, where the risk premium enters

With two equiprobable scenarios and $\beta = 0.5$, $\mathrm{CVaR}_{0.5}$ is just the **worse** of the two outcomes, which makes the arithmetic transparent:

$$\mathbb{E}[\phi] - \mathrm{CVaR}_{0.5}(\phi) = \frac{\phi_1 + \phi_2}{2} - \min\{\phi_1, \phi_2\} = \frac{\vert \phi_1 - \phi_2 \vert}{2} = \frac{\text{spread}}{2}$$

For both parties that gap is $600/2 = 300$. Applying $u = (1-A)\mathbb{E} + A\,\mathrm{CVaR}$ leaves each utility linear in the risk aversion weight:

| party, contract     | $\mathbb{E}$ | $\mathrm{CVaR}_{0.5}$ | utility $u = \mathbb{E} - A \cdot (\text{spread}/2)$ |
| ------------------- | ------------ | --------------------- | ---------------------------------------------------- |
| seller, no contract | 500          | 200                   | $d^S = 500 - 300\,A_S$                               |
| buyer, no contract  | -500         | -800                  | $d^B = -500 - 300\,A_B$                              |
| seller, hedged      | $10\lambda$  | $10\lambda$           | $u^S = 10\lambda$, no risk left so $A_S$ drops out   |
| buyer, hedged       | $-10\lambda$ | $-10\lambda$          | $u^B = -10\lambda$                                   |

The key line of this stage is the last column of the first two rows. The **risk premium**

$$\text{risk premium of party } i \;=\; \mathbb{E}[\phi^i] - u^i \;=\; A_i \times \frac{\text{spread}_i}{2} \;=\; 300\,A_i$$

is the amount by which each party discounts its own risky cash flow. It is a *private* loss: it appears in nobody else's accounts, and it does not show up anywhere in the cash table of Step 1.

### The contract, priced
Back to Stage 3, with $A_S = A_B = 0.5$ and $\beta = 0.5$. With two equiprobable scenarios, $\mathrm{CVaR}_{0.5}$ is simply the worse of the two.

|                       | $\mathbb{E}$ | $\mathrm{CVaR}_{0.5}$ | $u = 0.5\,\mathbb{E} + 0.5\,\mathrm{CVaR}$ |
| --------------------- | ------------ | --------------------- | ------------------------------------------ |
| Seller, no contract   | 500          | 200                   | $d^S = 350$                                |
| Buyer, no contract    | -500         | -800                  | $d^B = -650$                               |
| Seller, with contract | 500          | 500                   | $u^S = 500$                                |
| Buyer, with contract  | -500         | -500                  | $u^B = -500$                               |
$$u^S - d^S = 150, \qquad u^B - d^B = 150, \qquad W = 300, \qquad \text{Nash} = 22{,}500 > 0$$
**Both factors are positive, and now you know why.** The seller's certainty equivalent for $\{200, 800\}$ is $350$, which is $150$ below its mean of $500$. That $150$ is the seller's **risk premium**: money it is implicitly burning by holding risk it dislikes. The buyer is burning $150$ too. The contract extinguishes both fires at once:

$$W = \text{seller's risk premium} + \text{buyer's risk premium}$$
Nothing was transferred. Something was **created**, out of the removal of a mutually unwanted gamble.

### Step 3: the surplus appears

Add the two gains, keeping $A_S$ and $A_B$ general:

$$W = (u^S - d^S) + (u^B - d^B) = \underbrace{(10\lambda - 500 + 300A_S)}_{x} + \underbrace{(-10\lambda + 500 + 300A_B)}_{y}$$

The strike price cancels, exactly as it must, because the price direction has slope $-1$ (Stage 2). What survives is

$$\boxed{\;W = 300\,(A_S + A_B)\;}$$

At $A_S = A_B = 0.5$ this is $W = 300$, which Nash splits into $x = y = 150$ with product $22{,}500 > 0$. **A contract exists, and its size is set entirely by risk aversion.**

### Why it is no longer zero sum

This is the crux of the whole document, so here it is three ways.

**In words.** Each party was privately burning $300 A_i$ by holding a risk it dislikes. The contract puts out both fires at once. Nobody handed anybody a euro. Two separate deadweight losses simply stopped existing.

**In algebra.** Zero sum *in cash* means $\phi^S_\omega + \phi^B_\omega$ is constant. That is still true and always will be. Zero sum *in utility* is a strictly stronger requirement: it needs the utility functional to be **additive across parties**,

$$u(\phi^S) + u(\phi^B) \;=\; u(\phi^S + \phi^B) \;=\; u(\text{a constant})$$

Expectation satisfies this because it is linear: $\mathbb{E}[\phi^S] + \mathbb{E}[\phi^B] = \mathbb{E}[\phi^S + \phi^B] = 0$ whatever the contract. **CVaR does not.** It is only *superadditive*, which is the formal way of saying that diversification helps:

$$\mathrm{CVaR}(\phi^S) + \mathrm{CVaR}(\phi^B) \;\le\; \mathrm{CVaR}(\phi^S + \phi^B)$$

**In numbers.** Check that inequality on our data. With no contract,

$$\underbrace{200}_{\mathrm{CVaR}(\phi^S)} \;+\; \underbrace{(-800)}_{\mathrm{CVaR}(\phi^B)} \;=\; -600 \;\;\le\;\; \underbrace{0}_{\mathrm{CVaR}(0)}$$

a gap of 600. With the perfect hedge both sides are certain and the inequality closes to an equality, $10\lambda + (-10\lambda) = 0$. **The joint surplus is exactly the superadditivity gap that the contract closes**, weighted by how much each party cares about CVaR:

$$W = A_S \cdot 300 + A_B \cdot 300$$

So the answer to "what changed" is precise. The moment $A_i > 0$, the utility functional stops being additive across parties, so $u^S + u^B$ stops being a constant and becomes something a contract can move. That, and nothing else, creates the surplus.

### The derivative with respect to $A$

$W = 300(A_S + A_B)$ is linear, so the derivatives are constants, and they are interpretable:

$$\frac{\partial W}{\partial A_S} = \frac{\partial W}{\partial A_B} = 300 = \mathbb{E}[\phi^i] - \mathrm{CVaR}_{0.5}(\phi^i) = \frac{\text{spread}}{2}$$

**One unit of risk aversion is worth half the profit spread that the contract eliminates.** Sweeping it:

| $A_S$ | $A_B$ | $d^S$ | $d^B$ | $W$ | comment                                      |
| ----- | ----- | ----- | ----- | --- | -------------------------------------------- |
| 0     | 0     | 500   | -500  | 0   | Stage 3, no contract possible                |
| 0.25  | 0.25  | 425   | -575  | 150 |                                              |
| 0.5   | 0.5   | 350   | -650  | 300 | the worked example                           |
| 1     | 1     | 200   | -800  | 600 | pure CVaR, both parties price the worst case |
| 0     | 0.5   | 500   | -650  | 150 | Stage 5, only the buyer is risk averse       |

Note the last row: the surplus does **not** require both parties to be risk averse. One is enough. A risk neutral seller gains nothing from the hedge itself, but it can still sell that hedge to a buyer who values it, and Nash splits the buyer's premium between them.

**The second derivative result is the more useful one.** Impose the Nash condition $u^S - d^S = \theta W$ with $\theta = 1/2$ and solve for the strike price:

$$10\lambda - 500 + 300 A_S = 150\,(A_S + A_B) \qquad \Longrightarrow \qquad \boxed{\;\lambda^\star = 50 + 15\,(A_B - A_S)\;}$$

$$\frac{\partial \lambda^\star}{\partial A_B} = +15, \qquad \frac{\partial \lambda^\star}{\partial A_S} = -15$$

The strike starts at $\mathbb{E}[\lambda^{DA}] = 50$ and is pushed **away from the more risk averse party** at 15 EUR/MWh per unit of asymmetry. Whoever minds risk more pays for the insurance. Checks: $A_S = A_B$ gives $\lambda^\star = 50$, and $A_S = 0$ with $A_B = 0.5$ gives $\lambda^\star = 57.5$, which is exactly the number Stage 5 derives separately.

The same algebra gives the individually rational range:

$$\lambda \in \big[\,50 - 30 A_S,\ \ 50 + 30 A_B\,\big], \qquad \text{width} = 30\,(A_S + A_B)\ \text{EUR/MWh}$$

Multiply that width by $M = 10$ MWh and you recover $W = 300(A_S + A_B)$. **The bargaining range and the surplus are the same object in different units**, and both are proportional to risk aversion.

![[stage_4_risk_aversion.png]]

Panel (a) is the point made earlier: raising risk aversion does **not** bend the frontier, it translates it outward while the slope stays at $-1$. Panel (b) computes $W$ from the scenario data rather than from the formula, and recovers the straight lines of slope 300. Panel (c) shows $\lambda^\star$ crossing $\mathbb{E}[\lambda^{DA}] = 50$ exactly on the diagonal $A_S = A_B$: the strike price is the fair expected price only when the two parties are equally risk averse.

### Where does the money actually come from?

A fair objection: the cash table of Step 1 sums to zero everywhere, so how can anything be created? Because $W$ is not measured in cash. It is measured in **certainty equivalents**, and the two differ by exactly the risk premium.

For the seller at $A_S = 0.5$:
- Holding the gamble $\{200, 800\}$, it would swap it for a certain **350**. That is what the gamble is worth to it.
- The contract hands it a certain **500**.
- Better off by 150, even though its *expected* cash is 500 either way, unchanged.

For the buyer at $A_B = 0.5$:
- Facing the cost gamble $\{-200, -800\}$, it would pay up to **650** with certainty to be rid of it.
- The contract lets it pay a certain **500**.
- Better off by 150.

$150 + 150 = 300 = W$. No euro was created. What was destroyed is the *discount* each party was applying to its own position, and in practice those discounts are real costs: higher cost of capital, credit lines held against price swings, investments not made. Removing them is value creation in exactly the sense that insurance is.

> **The one line version.** *A PPA does not move money. It moves risk to where it is cheapest to hold, and the surplus is the risk premium that stops being paid.*

### A check that direction matters: over-hedging

If the mechanism really is "cancel a mutually unwanted gamble", then overshooting should destroy the surplus again. Set $M = 20$ at $\lambda = 50$:

$$\phi^S_L = 200 + 20(50-20) = 800, \qquad \phi^S_H = 800 + 20(50-80) = 200$$

The seller's profit is now **high in the low price scenario**. It has flipped from long to short and taken on the buyer's old exposure. Its spread is 600 again, so $u^S = 350 = d^S$ and its gain is zero. The same happens to the buyer, and $W = 0$.

So the surplus peaks at the perfect hedge $M = P^S = 10$ and falls to zero at both $M = 0$ and $M = 20$. Risk aversion creates surplus only when the contract is sized to **cancel** exposure, not when it creates new exposure in the opposite direction. This is the tent shape visible in the figure below.

### The mechanism in one line
Total profit $\phi^S_\omega + \phi^B_\omega$ is fixed scenario by scenario (Stage 2). But $u^S + u^B$ is not, because $u$ is a **concave** function of the profit vector. With a linear $u$, the sum of the parts equals the function of the fixed sum. With a concave $u$, *how you split a fixed random total* changes the sum of the
utilities, and smooth splits beat lumpy ones. This is Jensen's inequality doing all the work.

### The geometry to keep in your head
Sweep the strike price $\lambda$ at $M = 10$ and plot the achievable pairs
$(u^S - d^S,\ u^B - d^B)$.
- **Risk neutral:** the frontier is the line $x + y = 0$, which passes *through* the origin. The Nash product $xy \le 0$ everywhere on it, best value zero, attained only at the origin. A solver maximising $\log x + \log y$ hits $\log 0 = -\infty$ and reports infeasible. **That is what "no contract comes out" looks like numerically.**
- **With CVaR:** the frontier is the line $x + y = 300$, pushed *outward*, away from the origin. A whole segment now has both coordinates positive, and Nash picks the symmetric point $(150, 150)$.

![[stage_4_bargaining_set.png]]

Run `uv run python ppa_vot/stage4_bargaining_set.py` to regenerate it. The script sweeps both the contracted volume $M$ and the strike price $\lambda$, so the blue cloud is the full **bargaining set**, not just the frontier. Two features are worth reading off it:

- The set is the triangle $\{x \ge 0,\ y \ge 0,\ x + y \le 300\}$. Sweeping $\lambda$ at fixed $M$ moves you along a line of slope $-1$; sweeping $M$ moves you between such lines, because $W = 30 \min\{M,\ 20 - M\}$.
- $W$ is maximised at $M = 10 = P$, the **perfect hedge**, and falls away on both sides. Under-hedging ($M < 10$) leaves risk on the table; over-hedging ($M > 10$) creates new risk in the opposite direction, and by $M = 20$ the surplus is back to zero.

The left panel is the same sweep with $A_S = A_B = 0$. The entire set collapses onto the line $x + y = 0$, so the only individually rational point is the origin itself.

The individually rational range:
$$u^S - d^S = 10\lambda - 350 \ge 0 \;\Rightarrow\; \lambda \ge 35$$
$$u^B - d^B = 650 - 10\lambda \ge 0 \;\Rightarrow\; \lambda \le 65$$

So $\lambda \in [35, 65]$, a genuine **bargaining range** of width $30$ EUR/MWh times $10$ MWh $= 300 = W$. Nash with equal bargaining power splits it down the middle, giving $\lambda^\star = 50 = \mathbb{E}[\lambda^{DA}]$.

Under risk neutrality that range collapses to the single point $\lambda = 50$. **The bargaining range is the surplus.** No risk aversion, no range, no contract.

### Cross check against `prop:transfer`

With $q = M = 10 = P$ the merchant residual is zero, so $m^S = m^B = 0$ and $\Pi = \lambda Q = 10\lambda$. Then
$$W = (m^S - d^S) + (m^B - d^B) = (0 - 350) + (0 + 650) = 300 \quad \checkmark$$
$$\Pi^\star = \theta W - (m^S - d^S) = 0.5 \cdot 300 + 350 = 500, \qquad \lambda^\star = 500/10 = 50 \quad \checkmark$$
The closed form in the paper reproduces the hand calculation.

---

## Stage 5. Asymmetric risk aversion: the strike price moves
Make the seller risk neutral, $A_S = 0$, and keep $A_B = 0.5$.

|        | $d^i$ | $u^i$ at full hedge | gain |
| ------ | ----- | ------------------- | ---- |
| Seller | 500   | 500                 | 0    |
| Buyer  | -650  | -500                | 150  |
$W = 150$: only the buyer's risk premium contributes. Nash splits it $75 / 75$, which requires the buyer to **pay** for the insurance:


$$10\lambda - 500 = 75 \;\Rightarrow\; \lambda^\star = 57.5 > \mathbb{E}[\lambda^{DA}] = 50$$

**Diagnostic rule for reading your own results.** $\lambda^\star = \mathbb{E}[\lambda^{DA}]$ means symmetric risk aversion. $\lambda^\star$ above it means the buyer is the more risk averse party and is paying a premium. Below it means the seller is.

---
## Stage 6. Two hours: now the delivery path matters

**Setup.** Two hours, two equiprobable scenarios, $P = D = 5$ MWh per hour,
contracted volume $Q = 5$ MWh over the period, delivery cap $\bar q = 5$, $A = \beta = 0.5$ for both parties.

|                      | $\lambda_1$ | $\lambda_2$ |
| -------------------- | ----------- | ----------- |
| $\omega_1$ (p = 0.5) | 30          | 20          |
| $\omega_2$ (p = 0.5) | 50          | 100         |
| $\mathbb{E}$         | 40          | 60          |
| spread               | 20          | **80**      |

Hour 2 is expensive on average **and much more volatile**. That asymmetry is the whole point of the example.

**No contract.** Seller merchant revenue is $5(\lambda_1 + \lambda_2)$, giving $\{250, 750\}$, so $d^S = 0.5(500) + 0.5(250) = 375$. Buyer gets $\{-250, -750\}$, so $d^B = 0.5(-500) + 0.5(-750) = -625$. Their sum is $-250$.

**Three candidate paths.** The seller's residual merchant position is $\sum_t \lambda_t (P_t - q_t)$.

| path $(q_1, q_2)$             | seller residual                               | $m^S$   | $m^B$  | $W$     |
| ----------------------------- | --------------------------------------------- | ------- | ------ | ------- |
| A = (5, 0), deliver in hour 1 | $5\lambda_2 \in \{100, 500\}$                 | **200** | -400   | 50      |
| C = (2.5, 2.5), flat          | $2.5(\lambda_1 + \lambda_2) \in \{125, 375\}$ | 187.5   | -312.5 | 125     |
| B = (0, 5), deliver in hour 2 | $5\lambda_1 \in \{150, 250\}$                 | 175     | -225   | **200** |

Worked cell, path A: residual is $\lambda_1(5-5) + \lambda_2(5-0) = 5\lambda_2$, so $\{100, 500\}$, mean $300$, worst $100$, and $m^S = 0.5(300) + 0.5(100) = 200$.

### Two things to read off
**(i) Risk neutral sanity check.** Set $A = 0$. Then $m^S$ becomes $300 / 250 / 200$ and $m^B$ becomes $-300 / -250 / -200$, while $d^S + d^B = 0$. So $W = 0$ for **every** path. The path is pure redistribution.
`prop:zerosum` confirmed numerically, and this is a second unit test for your code.

**(ii) The seller and the partnership want opposite paths.** The seller ranks $A \succ C \succ B$: it delivers in the **cheap** hour and keeps the expensive merchant hour for itself. Joint surplus ranks $B \succ C \succ A$: the efficient path delivers into the **volatile** hour, because that is where a hedge is worth most. In this example the relation is exactly linear,
$$W = 250 - 0.5 \cdot (\text{spread of the seller's residual})$$
with spreads of $400$, $250$, $100$ for A, C, B.

> **The intuition to carry into the paper.** Risk neutral logic says "deliver when the price is low", and it is worth exactly nothing. Risk averse logic says "deliver when the price is uncertain", and that is where the joint value is.

  ---

## Stage 7. Who picks the path: the efficiency gap
Case 3 of the paper gives the seller the nomination right, so it picks path A. Case 4 negotiates the path jointly, so the parties pick the surplus maximising path B.
$$W_4 - W_3 = 200 - 50 = 150$$
That gap is the cost of a unilateral nomination clause, and it is `eq:efficiencygap` with numbers in it. Applying the closed form $\Pi^\star = \theta W - (m^S - d^S)$ and $\lambda^\star = \Pi^\star / Q$ with $\theta = 0.5$:

|                          | path | $W$ | each party gains | $\Pi^\star$ | $\lambda^\star$ |
| ------------------------ | ---- | --- | ---------------- | ----------- | --------------- |
| Case 3, seller nominates | A    | 50  | 25               | 200         | **40** EUR/MWh  |
| Case 4, jointly agreed   | B    | 200 | 100              | 300         | **60** EUR/MWh  |

Verification for Case 4: $u^S = \Pi + m^S = 300 + 175 = 475$ against $d^S = 375$, so $+100$. And $u^B = -300 - 225 = -525$ against $d^B = -625$, so $+100$. Correct.

The strike price is higher in Case 4 because the seller now delivers in the expensive hour and must be compensated for the foregone merchant revenue. Both parties are still better off than under Case 3: $100$ each instead of $25$.

---

## Stage 8. Honest information: the foresight trap

Everything above used $q_{t\omega}$, a delivery in hour $t$ allowed to differ across scenarios. Ask what that means operationally. In hour 1 the seller must physically decide how much to deliver. If $q_{1,\omega_1} \ne q_{1,\omega_2}$, the model is saying *"deliver 5 MWh if this turns out to be the low price week, and 0 otherwise"*, which requires knowing the future. An optimiser will exploit this happily, and will  report a flexibility value no trader could ever capture.

**Setup.** Three hours, $Q = 5$ MWh, cap $\bar q = 5$. $\lambda_1 = 50$ is known today. $\lambda_2$ and $\lambda_3$ are independent, each $20$ or $100$ with  probability $0.5$, so $\mathbb{E} = 60$. The seller minimises the cost of delivery $\mathbb{E}[\sum_t \lambda_t q_t]$, that is, the merchant revenue it gives up.

| information assumption                             | best cost | meaning                               |
| -------------------------------------------------- | --------- | ------------------------------------- |
| **Perfect foresight**, $q_{t\omega}$ free          | **137.5** | knows the whole week in advance       |
| **Adaptive**, decide hour by hour as prices arrive | **200**   | realistic                             |
| **Ex ante commitment**, one fixed profile          | **250**   | schedule fixed before the week starts |

*Perfect foresight:* deliver in the cheapest of the three hours. That is $20$ unless both future hours are $100$ (probability $1/4$), so $\mathbb{E}[\min] = 0.75(20) + 0.25(50) = 27.5$, times $5$ MWh gives $137.5$.

*Ex ante commitment:* deliver all in the hour with the lowest expected price, which is hour 1 at $50$, giving $250$. Hours 2 and 3 would give $300$.

*Adaptive:* computed in Stage 10 below, giving $200$.

**The distortion.** Measured against the committed schedule, flexibility is worth $250 - 200 = 50$ if you model information honestly, and $250 - 137.5 = 112.5$ if you do not. That is a **2.25 times overstatement** on a three hour problem, and it grows with the horizon. Over 168 hours it is enormous. Since the entire paper is about quantifying flexibility value, this is not a detail.

---

## Stage 9. Non anticipativity, and why scenario trees will not scale

A **filtration** $(\mathcal{F}_t)$ formalises "what you know at time $t$". It grows, $\mathcal{F}_1 \subseteq \mathcal{F}_2 \subseteq \dots$, because you never forget.  At time $t$, some scenarios are still indistinguishable: nothing observed so far separates them. Group them into **bundles**. A decision is **non anticipative** (equivalently, $\mathcal{F}_t$ measurable, or implementable) if it is constant on each bundle:

$$q_{t\omega} = q_{t\omega'} \quad \text{whenever } \omega, \omega' \text{ share a bundle at } t$$

*Numerical example, using Stage 8.* Four price paths, indexed by $(\lambda_2, \lambda_3)$:

| scenario $(\lambda_2, \lambda_3)$ | bundle at $t=1$ | bundle at $t=2$ | bundle at $t=3$ |
| --------------------------------- | --------------- | --------------- | --------------- |
| (20, 20)                          | I               | I               | I               |
| (20, 100)                         | I               | I               | II              |
| (100, 20)                         | I               | II              | III             |
| (100, 100)                        | I               | II              | IV              |
| **number of free values**         | **1**           | **2**           | **4**           |

At $t = 1$ nothing has been observed, so all four scenarios sit in one bundle and $q_1$ must be a single number. At $t = 2$ the seller has seen $\lambda_2$, which splits the scenarios into two bundles, so $q_2$ may take two values. By $t = 3$ everything is known and $q_3$ may take four. Perfect foresight is the degenerate case where every bundle is a singleton already at $t = 1$, giving four free values of $q_1$ instead of one.

### How this is traditionally modelled

**(a) Scenario fan with explicit constraints.** Keep $q_{t\omega}$ and add the equalities above to the LP. Conceptually clean, and it is what makes scenario decomposition work (progressive hedging relaxes exactly these constraints and prices them). Cost: many redundant variables plus many constraints.

**(b) Scenario tree, node formulation.** Replace the index $(t, \omega)$ by a **node** $n$ of a tree, each node having a unique parent. A scenario is a root to leaf path. One variable per node, and non anticipativity is enforced *structurally*: scenarios sharing a history literally share the variable, so no constraints are needed. This is the standard multistage stochastic programming form.

**(c) Decision rules.** Restrict $q_t$ to a parametric function of observables, for instance $q_t = \theta_0 + \theta_1 \lambda_t + \theta_2 R_t$, and optimise over $\theta$. Cheap, always implementable, generally suboptimal.

**(d) Dynamic programming, the MDP.** Stage 10.

### Why (b) fails for this paper
A weekly problem has $T = 168$. A tree with only **two** branches per hour has $2^{168}$ nodes, which is around $10^{50}$. Even 24 hourly stages with 3 branches is about $10^{11}$ nodes. **The tree grows exponentially in $T$, and that is fatal.**

---
## Stage 10. The MDP
The observation that rescues you: to act well in hour $t$ you do not need the whole history, only a small summary of it. That summary is the **state**.

### The five ingredients
- **Stage** $t$: the hour.
- **State** $S_t = (R_t, \lambda_t, \xi_t)$: volume still to deliver, current price,
and whatever forecast information makes prices Markov. Two histories with the same state are interchangeable.
- **Action** $q_t \in \mathcal{A}(S_t)$, with $0 \le q_t \le \min\{\bar q, R_t\}$ and $R_t - q_t \le (T - t)\bar q$ so the remainder stays deliverable. This is the delivery corridor written recursively.
- **Transition** $R_{t+1} = R_t - q_t$, deterministic and controlled, plus the exogenous price process.
- **Reward** $r(S_t, q_t) = \lambda_t (P_t - q_t)$, the merchant cash flow this hour.

**Markov** means transition and reward depend on the past only through $S_t$. That is what makes the state a sufficient summary, and it is a modelling assumption you have to earn with your price model.

A **policy** $\pi$ maps state to action, $q_t = \pi_t(S_t)$. A policy is **automatically non anticipative**, because it only reads variables observable at time $t$. This is the deep reason the MDP solves the Stage 8 problem: implementability stops being a constraint you impose and becomes a property of the object you optimise over.

### The value function
$$V_t(S_t) = \text{best expected total reward from stage } t \text{ onward, starting in state } S_t$$
It satisfies the **Bellman equation**, which is the slide in your figures folder ("value of being in state $S_t$ = reward from the immediate decision + expected value of being in state $S_{t+1}$"):
$$V_t(S_t) = \max_{q_t \in \mathcal{A}(S_t)} \Big\{ r(S_t, q_t) + \mathbb{E}\big[ V_{t+1}(S_{t+1}) \mid S_t, q_t \big] \Big\}$$

with a terminal condition. You solve it **backwards**: $V_T$ first, then $V_{T-1}$, and so on. The cost is linear in $T$, not exponential.

### Worked backward induction
Take the Stage 8 example in cost minimisation form. Everything is linear in $R$, so write $V_t = c_t \cdot R$ with $c_t$ a cost per MWh.

**$t = 3$, last hour, the obligation is forced.** You must deliver whatever remains, at whatever price appears:
  $$V_3(R, \lambda_3) = \lambda_3 R, \qquad \mathbb{E}[c_3] = 60$$

**$t = 2$.** You observe $\lambda_2$, then choose: deliver now at $\lambda_2$, or carry the MWh to hour 3 at an expected $60$.
$$V_2(R, \lambda_2) = \min\{\lambda_2,\ 60\} \cdot R$$

so $c_2 = 20$ when $\lambda_2 = 20$, and $c_2 = 60$ when $\lambda_2 = 100$. Before observing $\lambda_2$:

$$\mathbb{E}[c_2] = 0.5(20) + 0.5(60) = 40$$

**$t = 1$.** $\lambda_1 = 50$ is known. Deliver now at $50$, or carry at $40$:

$$V_1 = \min\{50,\ 40\} \cdot 5 = 40 \times 5 = 200$$
which is the adaptive number in the Stage 8 table.

### Three things this gives you

1. **The value function is a price.** The number $40$ is the marginal value of carrying one MWh of unmet obligation forward, that is $\partial V / \partial R$, the shadow price of the delivery constraint. Traders call it the option value of the remaining PPA volume.
2. **The optimal policy is a threshold rule.** *Deliver in hour $t$ if and only if $\lambda_t$ is at or below the continuation value.* At $t = 1$, $50 > 40$, so wait. At $t = 2$, deliver if and only if $\lambda_2 \le 60$. This is the same logic as a hydro reservoir's water value or a gas storage spread option, and it is directly interpretable, unlike a wall of LP output.
3. **The continuation value falls as optionality rises:** $60$ with no choices left, $40$ with one hour of choice. The difference is the value of flexibility, computed honestly.
---

## Stage 11. Plugging the MDP into the bilevel

`prop:decoupling` tells you exactly what the lower level owes the upper level: not a

path, but a number. The seller's merchant utility under the optimal policy, as a

function of the contracted volume alone:



$$V(Q) = \max_{\text{policies}} m^S$$



The upper level then runs unchanged: form

$W_3(Q) = V(Q) + m^B - d^S - d^B$, sweep the scalar $Q$, and read the strike price

off the closed form of `prop:transfer`.



Two practical notes:



- $V$ takes $Q$ **only**. Writing $V(\lambda^{PPA}, Q)$, as in the earlier draft, is

redundant: the strike price is a deterministic constant that shifts the objective

without moving its argmax.

- $R_1 = Q$ is the initial state, so sweeping $Q$ is sweeping the initial condition.

A single backward pass over a grid of $R$ gives $V(Q)$ for **all** $Q$ at once,

which is a large saving over re solving an LP for each candidate $Q$.



---



## Stage 12. The catch: CVaR is not time additive



The Bellman recursion needs the objective to be **additive across stages**: total

reward equal to the sum of stage rewards. Expectation is additive. $\mathrm{CVaR}$

is not. The $\mathrm{CVaR}$ of a sum is not the sum of the $\mathrm{CVaR}$s, and a

naive stage wise $\mathrm{CVaR}$ is not the static $\mathrm{CVaR}_\beta$ used in

Stage 4.



Two standard ways out:



**Nested (dynamic) risk measures.** Apply a one step risk measure at each stage.

Time consistent and Bellman compatible, but it encodes a *different* risk preference

from `eq:utility`, so Sections 2 and 3 of the paper would no longer be measuring the

same thing.



**Carry $\zeta$ as a state.** In the Rockafellar and Uryasev form,



$$\mathrm{CVaR}_\beta(\phi) = \max_{\zeta} \Big\{ \zeta - \tfrac{1}{1-\beta} \mathbb{E}\big[(\zeta - \phi)^+\big] \Big\}$$



so if you fix $\zeta$ you are left with a risk neutral MDP on shifted rewards, and

you optimise over the scalar $\zeta$ in an outer loop. This preserves the static

$\mathrm{CVaR}$ exactly, at the cost of one extra loop.



**Recommendation:** the second. It keeps Sections 2 and 3 comparable, which is the

entire reason for having both. This decision should be made before writing any of

Section 3.



---



## Appendix. Checklist for the implementation



1. With $A_S = A_B = 0$, expect $W = 0$ to machine precision and the log

Nash objective to be infeasible. **This is correct behaviour, not a bug.** Use it

as a unit test (Stage 3 and Stage 6(i)).

2. Verify that $\sum_i \phi^i_\omega$ is invariant to $\lambda^{PPA}$, $Q$ and $q$ in

every scenario. If it is not, there is an accounting error: double counted

settlement, or the two parties facing different prices.

3. Compute $W$ **before** solving the Nash problem. If $W \le 0$ there is no

individually rational contract, and the solver failure is informative rather than

a bug.

4. Optimise the log Nash objective, never the raw product. The product is badly

scaled and non concave in the decision variables.

5. $\lambda^\star$ should land inside the individually rational interval. If it lands

outside, the price bound is binding and `rem:zerovolume` applies.

6. Always report the three information brackets from Stage 8 side by side: ex ante

commitment, adaptive, perfect foresight. The spread between them tells the referee

how much of the measured flexibility value is genuine.
