# Club_Quant_CUNEF

Quantitative Finance Club at CUNEF Universidad (Madrid).

We learn quantitative research by doing it: replicating empirical asset pricing papers
with real data, validating every result against an independent benchmark, and then
building our own research on top of what we have replicated.

## How the club works

1. **Reading group.** Members read and replicate published papers (starting with AQR's
   research) in Python, using CRSP and Compustat data through WRDS.
2. **Research projects.** Members propose their own questions, building on the
   replications, and work on them in small teams.

Every result is checked by someone other than its author before it is accepted.

## Replications

| Paper | Folder | Result |
|---|---|---|
| Asness, Frazzini, Israel & Moskowitz (2014), *Fact, Fiction and Momentum Investing* | [`aqr_momentum/`](aqr_momentum/) | UMD momentum factor rebuilt from raw CRSP data, 1927–2013. Monthly correlation with Kenneth French's official series: **0.993** |

## Workflow

- Each paper or project lives in its own folder, with its code and a README covering
  the question, data, method and results.
- `main` is protected: every change goes through a pull request and needs one approval
  from another member.
- Raw CRSP/Compustat data are never committed (WRDS licensing). Derived series and
  charts may be.

## Founders

Juan Villar Movilla and Pedro Gil Anaut, students of Mathematical Engineering and Economics at CUNEF Universidad.
