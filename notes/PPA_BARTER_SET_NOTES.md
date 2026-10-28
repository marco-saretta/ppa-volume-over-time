# PPA Nash Bargaining Paper — Barter Set / CVaR Appendix Thread

Context handoff for continuing this work in Claude Code. This file summarises a long
conversation covering three linked appendix sections of the PPA Nash bargaining paper
(baseload vs. pay-as-produced, CVaR risk aversion, barter set convexity), plus the
Python code for the resulting figure.

## Paper context

- Extending Yu, Tesfatsion & Liu (2012), "Financial Bilateral Contract Negotiation in
  Wholesale Electricity Markets Using Nash Bargaining Theory," *IEEE Trans. Power Syst.*
  27(1), to stochastic (pay-as-produced, PAP) contracts and CVaR risk aversion.
- Also cross-referencing Anders Dan Hansen's thesis, "Nash Bargaining for Power Purchase
  Agreements" (2025), which independently extends the same Yu et al. framework and is
  a useful second source for the barter-set convexity proof technique.
- Notation: seller/generator $G$ (or $S$ in earlier sections), buyer/load $L$ (or $B$).
  Utility $u_i = (1-A_i)\mathbb E[\pi_i] + A_i\,\mathrm{CVaR}_\alpha(\pi_i)$,
  $A_i\in[0,1]$ risk aversion, normalised (see Lemma "utility normalisation" below —
  this normalisation is what collapses the baseload frontier slope to exactly $-1$,
  simpler than Yu et al.'s unnormalised $-(1+A_L)/(1+A_G)$).

## What's been derived, in order

### 1. Asymmetric price beliefs, risk neutral (`app:price_bias`)

Baseload contract, both parties risk neutral but with private price beliefs $K^i\lambda$.
- $W = M\lambda(K^B-K^S)$: non-zero surplus from belief asymmetry alone, no risk aversion
  needed. Contract exists iff $K^B>K^S$ strictly.
- NBS strike: $S^\star = \tfrac{K^S+K^B}{2}\lambda$ (midpoint of beliefs).
- **Key result:** the Nash product is a saddle in $(S,M)$ jointly — concave in $S$,
  convex in $M$ — so there is no unconstrained interior optimum in $M$; it is pushed to
  an exogenous capacity bound $M^\star=\bar M$. Verified via Hessian
  ($\det H = -4M^2 g(S^\star) < 0$) and confirmed numerically in Gurobi (see below).
  This is the formal argument for why a CVaR term can't be dropped even when belief
  bias, not risk aversion, is the phenomenon of interest.

### 2. CVaR risk aversion, symmetric beliefs (`app:cvar_nonzero`)

Same contract, both risk neutral→risk averse via CVaR, no belief bias.
- General mechanism: CVaR is *superadditive*, not additive, across parties
  ($\mathrm{CVaR}_\alpha(\phi^S)+\mathrm{CVaR}_\alpha(\phi^B) \le \mathrm{CVaR}_\alpha(\phi^S+\phi^B)$),
  which is what breaks the zero-sum result of the deterministic/risk-neutral case.
- Closed form (two-scenario, $\beta=0.5$, $P=D=Q$):
  $W(M) = \tfrac{s}{2}(A_S+A_B)\min\{M,\,2Q-M\}$ — a **tent shape**, peaking at the
  physical full hedge $M=Q$, falling to zero at $M=0$ and $M=2Q$ (over-hedging
  destroys surplus). $\min$ of two affine functions ⇒ concave ⇒ genuine **interior**
  optimum at $M^\star=Q$, no external cap needed. This is the structural contrast with
  case 1: risk aversion self-bounds the volume; belief bias does not.
- General (non-symmetric distribution) version: define
  $\underline\rho_\alpha := \mathbb E[\Lambda]-\mathrm{CVaR}_\alpha(\Lambda)$,
  $\overline\rho_\alpha := -\mathrm{CVaR}_\alpha(-\Lambda)-\mathbb E[\Lambda]$
  (lower/upper tail risk premia). For $\pi=c+m\Lambda$:
  $\mathrm{CVaR}_\alpha(\pi) = c+m\mathbb E[\Lambda]-\underline\rho_\alpha m$ if $m\ge0$,
  else $c+m\mathbb E[\Lambda]+\overline\rho_\alpha m$. Verified numerically against a
  brute-force scenario scan (sign flip lands exactly at the predicted threshold).

### 3. Rockafellar–Uryasev LP formulation of CVaR

Standard reminder, kept for the methodology section (near the MDP/$\zeta$-as-state
discussion): $\mathrm{CVaR}_\beta(\phi) = \max_\zeta\{\zeta - \tfrac1{1-\beta}\mathbb
E[(\zeta-\phi)^+]\}$, LP form with $z_\omega\ge0,\ z_\omega\ge\zeta-\phi_\omega$. Cite
Rockafellar & Uryasev (2000), don't re-derive the theorem in the paper itself.

### 4. Gurobi verification models

Three toy models (deterministic, stochastic risk-neutral, CVaR) confirming $W=0$ in the
first two, $W>0$ in the third, matching the closed forms by hand. **Critical lesson**:
`M`, `S` must have **finite bounds** (`lb`, `ub`) whenever they appear in a bilinear
term (e.g. `M*S`). With Gurobi's default `ub=inf`, the McCormick envelope used in
spatial branch-and-bound is numerically vacuous, and Gurobi can report a "0% gap,
optimal" result that is *actually wrong* (confirmed by reproducing this exact failure:
`M*, S*` drifted to nonsensical values while a provably-better objective of 0 was
available). Fixing the bounds fixes the certificate. `NonConvex=2` is unnecessary —
recent Gurobi auto-detects and handles the bilinear structure by default.

A related non-bug: at the symmetric-belief boundary ($K^S=K^B$), the optimal objective
is correctly $\approx 0$ for *every* $M$ along the ridge $S=\lambda$ — Gurobi will
report an arbitrary $M^\star$ on that ridge, which is correct (the whole ridge is
equally optimal, not a solver artefact).

### 5. Barter set convexity — baseload (COMPLETE)

Full theorem + proof written up, following Yu et al.'s technique (their Appendix B)
but simplified using our normalised utility (slope exactly $-1$, so the closing
argument uses the linear functional $f = u_G+u_L = W$, not Yu's party-dependent
$f=[1+A_L]u_G+[1+A_G]u_L$).

**Why Yu et al.'s theorem doesn't extend to PAP automatically:** their whole proof
rests on the $S$-sweep at fixed $M$ tracing a *straight* line (true only because
production/demand are deterministic constants). Under stochastic production the
$S$-sweep is *curved*, so no linear functional stays constant along it — PAP needs a
different closing argument, not a generalisation of theirs. (See open item below.)

Key closed forms (baseload, general — see conversation for full derivation):
- $\underline\rho_\alpha,\overline\rho_\alpha$ as above.
- $S^{R*} = \dfrac{\mathbb E[\Lambda]-\max\{A_G,A_L\}\underline\rho_\alpha}{T}$,
  $S^{U*} = \dfrac{\mathbb E[\Lambda]+\max\{A_G,A_L\}\overline\rho_\alpha}{T}$
  (viable strike bounds — numerically verified the sign-flip location).
- C1/C2 (existence / interior-vs-boundary conditions): ratio of $du_L/dM$ over
  $du_G/dM$ evaluated at $(M^R,S^R)$ (C1, $<-1$) and $(M^U,S^R)$ (C2, $>-1$).
- Main theorem: $W(M):=u_G+u_L$ constant along every $S$-sweep (slope $-1$) ⇒ bounded
  above by $C^1:=W(M^\star)$ where $V_1$'s tangent hits slope $-1$ ⇒
  $\mathbf B\subseteq\{u_G\ge\zeta_1\}\cap\{u_L\ge\zeta_2\}\cap\{u_G+u_L\le C^1\}$, three
  half-planes, convex by construction. Cases 1/2/3 (interior / no-agreement /
  boundary-pinned) fall out of whether/where $V_1$'s slope crosses $-1$ within
  $[M^R,M^U]$.

### 6. Barter set convexity — PAP (OPEN)

Placeholder theorem only. The bilinear $xSB_\omega$ revenue term makes $u_G$ **not**
jointly concave in $(x,S)$ (Hessian of the expectation term alone is
$\begin{pmatrix}0&\mathbb E[B_\omega]\\\mathbb E[B_\omega]&0\end{pmatrix}$, a pure
saddle). Neither the baseload closing trick nor a naive joint-concavity argument
applies. Most promising open route: Jacobian sign-structure / monotone-map argument on
$\Phi(x,S)=(u_G,u_L)$ over the box, using the existing Lemmas (monotonicity,
concavity_x) as building blocks — not yet written down.

### 7. Anders's thesis cross-check

His Lemma 1–4 (Ch. 4) match this framework closely and independently confirm the
$-1$-slope normalisation. His Appendix E.2/E.3 give the full baseload C1/C2 derivation
in his own notation — worth citing directly. **Possible errata to flag with him:** his
eq. (4.27)/(E.19) for $S_{G1}^{R*}$ conditions the CVaR tail on
$\pi_G(M,S^U)$ while evaluating VaR at $\pi_G(M,S^R)$ — looks like a copy/transcription
slip (every other instance keeps the strike consistent).

## Figure + plotting instructions

`barter_set_figure.py` (already generated, saved alongside this file) produces a
two-panel figure:
- **Left panel:** the decision-space box $(M,S)\in[0,M^U]\times[S^R,S^U]$, with each
  edge colour-coded to the utility-space curve it maps to.
- **Right panel:** the resulting utility possibility set $U$ (grey wedge, pinched at
  the disagreement point $\zeta$ because $M=0$ kills all $S$-dependence) with the
  barter set $B$ (small red triangle, vertices $\zeta, I, J$) nested inside it.

This is a **real closed-form example** (two-scenario CVaR, $P=D=Q=10$, $A_G=0.4$,
$A_L=0.6$, $S^R=20$, $S^U=80$), not a schematic — every curve is computed from the
actual $w_G(M,S), w_L(M,S)$ formulas. The kink in $V_1,V_2$ and the crossing point
$M^\star$ both land exactly at $M=Q$ for this simple two-scenario case (a genuine
model property, not a plotting artefact — for more scenarios/asymmetric distributions
the kink and crossing point need not coincide; would need re-deriving via the general
$\underline\rho_\alpha,\overline\rho_\alpha$ formulas above rather than the
symmetric two-point shortcut used in the script).

**To regenerate or adapt:** edit the parameter block at the top of the script (`Q`,
`lam_bar`, `rho`, `A_G`, `A_L`, `S_R`, `S_U`, `M_U`) and rerun. Colour scheme is
consistent across both panels by design (teal = $S^R$/$V_1$, coral = $S^U$/$V_2$,
amber = $M^U$ connector, purple dotted = $M^\star$ connector, grey dashed = collapsed
$M=0$ edge) — keep this mapping if extending the figure so it stays legible.

**Still to do, if picking this up in Code:**
1. Adapt the figure to the paper's *actual* numerical parameters (currently the toy
   $Q=10$ example, not a real case-study number).
2. Attempt the PAP convexity proof via the Jacobian/monotone-map route (item 6).
3. Transcribe the completed baseload appendix (theorem + all lemmas, already written
   out in full in this conversation) into the paper's Overleaf source.
4. Flag the possible Anders thesis errata (item 7) directly with him.
