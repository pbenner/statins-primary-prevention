"""Trial-level log risk-ratio meta-analysis of binomial event counts.

This reproduces aggregate results; it does not fit patient-level survival models.
"""
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd
from scipy import stats

@dataclass
class MetaResult:
    method: str
    trials: int
    log_rr: float
    se: float
    rr: float
    ci_low: float
    ci_high: float
    p_value: float
    q: float
    q_p_value: float
    i2_percent: float
    tau2: float

    def as_dict(self):
        return asdict(self)

def trial_effects(frame,continuity=0.5):
    """Katz log RR and variance; omit double-zero studies.

    Add continuity to all four cells of a study only when either arm has zero
    events. It is not added to every study. Denominators then increase by 2c.
    """
    needed=["statin_events","statin_n","control_events","control_n"]
    d=frame.copy()
    values=d[needed].to_numpy(dtype=float)
    if not np.isfinite(values).all():raise ValueError("Counts must be finite")
    a,n,c,m=values.T
    if np.any(n<=0) or np.any(m<=0) or np.any(a<0) or np.any(c<0) or np.any(a>=n) or np.any(c>=m):
        raise ValueError("Require positive arm totals and 0 <= events < total")
    d=d.loc[(a+c)>0].copy()
    a,n,c,m=d[needed].to_numpy(dtype=float).T
    cc=((a==0)|(c==0))*float(continuity)
    ac,nc,ccount,mc=a+cc,n+2*cc,c+cc,m+2*cc
    if np.any(ac==0) or np.any(ccount==0):raise ValueError("Zero arm requires a positive correction")
    d["continuity_added"]=cc
    d["log_rr"]=np.log(ac/nc)-np.log(ccount/mc)
    d["variance"]=1/ac-1/nc+1/ccount-1/mc
    d["rr_recalculated"]=np.exp(d.log_rr)
    se=np.sqrt(d.variance.to_numpy())
    d["ci_low_recalculated"]=np.exp(d.log_rr-stats.norm.ppf(.975)*se)
    d["ci_high_recalculated"]=np.exp(d.log_rr+stats.norm.ppf(.975)*se)
    return d

def pool_effects(effects,method="DL"):
    """Inverse-variance pooling with normal 95% confidence intervals.

    DL = nonnegative DerSimonian–Laird between-trial variance.
    FE = common-effect inverse variance. Intervals use the normal critical value
    to match the review's conventional analysis, not a small-sample t adjustment.
    """
    if method not in ["DL","FE"]:raise ValueError("Unknown pooling method")
    y=effects.log_rr.to_numpy(dtype=float);v=effects.variance.to_numpy(dtype=float)
    if len(y)<2 or np.any(v<=0) or not np.isfinite(y).all() or not np.isfinite(v).all():raise ValueError("Need >=2 finite estimates with positive variance")
    weights=1/v;mean=np.sum(weights*y)/weights.sum()
    q=float(np.sum(weights*(y-mean)**2));df=len(y)-1
    denominator=float(weights.sum()-np.sum(weights**2)/weights.sum())
    tau2=max(0.,(q-df)/denominator) if method=="DL" else 0.
    w=1/(v+tau2);mean=float(np.sum(w*y)/w.sum());se=float(np.sqrt(1/w.sum()))
    lo,hi=np.exp(mean+np.array([-1,1])*stats.norm.ppf(.975)*se)
    return MetaResult(method,len(y),mean,se,float(np.exp(mean)),float(lo),float(hi),float(2*stats.norm.sf(abs(mean/se))),q,float(stats.chi2.sf(q,df)),float(max(0.,(q-df)/q)*100) if q>0 else 0.,float(tau2))

def analyze_counts(frame,method="DL",continuity=.5):
    return pool_effects(trial_effects(frame,continuity),method)

def leave_one_out(frame):
    effects=trial_effects(frame)
    rows=[]
    for index,row in effects.iterrows():
        r=pool_effects(effects.drop(index)).as_dict()
        rows.append({"omitted_trial":row.trial,**r})
    return pd.DataFrame(rows)

def sensitivity(frame):
    selections={
        "All eligible trials":frame,
        "Exclude ALLHAT-LLT":frame.loc[frame.trial!="ALLHAT-LLT"],
        "Exclude JUPITER":frame.loc[frame.trial!="JUPITER"],
        "Exclude three trials stopped early":frame.loc[~frame.trial.isin(["ASCOT-LLA","CARDS","JUPITER"])],
        "Exclude ALLHAT-LLT and PROSPER":frame.loc[~frame.trial.isin(["ALLHAT-LLT","PROSPER"])],
    }
    return pd.DataFrame([{"analysis":name,**analyze_counts(d).as_dict()} for name,d in selections.items()])
