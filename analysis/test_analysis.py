"""Numerical checks against printed totals and an independent implementation."""
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from statsmodels.stats.meta_analysis import combine_effects,effectsize_2proportions
from meta_analysis import analyze_counts,pool_effects,trial_effects

BASE=Path(__file__).resolve().parent

class AnalysisChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=pd.read_csv(BASE/"data/uspstf_2022_trial_counts.csv")

    def test_counts_match_published_totals(self):
        expected={"All-cause mortality":(18,85186,1774,1924),"Cardiovascular mortality":(12,75138,586,645),"Incident diabetes":(6,59083,1004,941)}
        for name,(k,n,a,c) in expected.items():
            d=self.data.loc[self.data.outcome==name]
            self.assertEqual((len(d),int((d.statin_n+d.control_n).sum()),int(d.statin_events.sum()),int(d.control_events.sum())),(k,n,a,c))

    def test_ctt_totals_and_ci_levels(self):
        d=pd.read_csv(BASE/"data/ctt_2012_risk_effects.csv")
        for _,g in d.groupby('population'):
            summary=g.loc[g.is_summary].iloc[0];strata=g.loc[~g.is_summary]
            for column in ['statin_or_more_events','control_or_less_events']:
                self.assertEqual(strata[column].sum(),summary[column])
            self.assertTrue((strata.ci_level==.99).all());self.assertEqual(summary.ci_level,.95)
        for rank in range(6):
            g=d.loc[d.risk_order==rank]
            combined=g.loc[g.population=='All participants'].iloc[0]
            separate=g.loc[g.population!='All participants']
            self.assertEqual(separate.statin_or_more_events.sum(),combined.statin_or_more_events)
            self.assertEqual(separate.control_or_less_events.sum(),combined.control_or_less_events)

    def test_trial_effects_against_statsmodels(self):
        d=self.data.loc[(self.data.statin_events>0)&(self.data.control_events>0)].copy()
        own=trial_effects(d)
        y,v=effectsize_2proportions(d.statin_events.to_numpy(),d.statin_n.to_numpy(),d.control_events.to_numpy(),d.control_n.to_numpy(),statistic='risk-ratio')
        np.testing.assert_allclose(own.log_rr,y,atol=1e-13)
        np.testing.assert_allclose(own.variance,v,atol=1e-13)

    def test_pool_against_statsmodels(self):
        for _,d in self.data.groupby('outcome'):
            e=trial_effects(d);own=pool_effects(e)
            # The helper computes unused random-effect square roots even when
            # its untruncated tau² is negative. We validate its FE branch then.
            with np.errstate(invalid='ignore'):
                other=combine_effects(e.log_rr.to_numpy(),e.variance.to_numpy(),method_re='dl')
            # Statsmodels' DL estimator is untruncated; use its FE result
            # when Q < k−1. The conventional DL tau² is bounded at zero.
            mean=other.mean_effect_re if other.tau2>=0 else other.mean_effect_fe
            se=other.sd_eff_w_re if other.tau2>=0 else other.sd_eff_w_fe
            self.assertAlmostEqual(own.log_rr,float(mean),places=12)
            self.assertAlmostEqual(own.se,float(se),places=12)

    def test_arm_swap_reciprocity(self):
        d=self.data.loc[self.data.outcome=='All-cause mortality'].copy()
        swapped=d.rename(columns={'statin_events':'control_events','control_events':'statin_events','statin_n':'control_n','control_n':'statin_n'})
        first,second=analyze_counts(d),analyze_counts(swapped)
        self.assertAlmostEqual(first.rr*second.rr,1.,places=12)
        self.assertAlmostEqual(first.ci_low*second.ci_high,1.,places=12)

    def test_zero_handling(self):
        d=self.data.loc[self.data.outcome=='All-cause mortality']
        e=trial_effects(d)
        self.assertEqual(len(e),17);self.assertNotIn('Bone et al',e.trial.to_list())
        corrected=e.loc[e.continuity_added>0]
        self.assertEqual(corrected.trial.to_list(),['METEOR'])
        self.assertAlmostEqual(corrected.iloc[0].rr_recalculated,(1.5/701)/(.5/282))

    def test_published_rounding(self):
        expected={'All-cause mortality':(.92,.87,.98),'Cardiovascular mortality':(.91,.81,1.02),'Incident diabetes':(1.04,.92,1.19)}
        for name,rounded in expected.items():
            r=analyze_counts(self.data.loc[self.data.outcome==name])
            self.assertEqual(tuple(round(x,2) for x in [r.rr,r.ci_low,r.ci_high]),rounded)

if __name__=='__main__':unittest.main()
