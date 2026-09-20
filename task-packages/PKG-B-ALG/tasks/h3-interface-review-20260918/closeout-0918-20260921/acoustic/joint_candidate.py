"""Fixed joint correlation grid, with residual checked against measured pair peaks."""
import numpy as np

class JointCandidate:
    def __init__(self, positions, pairs, fs=48000, c=343):
        self.matrix=np.array([(positions[j]-positions[i])[:2]*fs/c for i,j in pairs])
        self.angles=np.arange(-180,180,dtype=float)
        self.radii=np.arange(2,27,dtype=float)/20  # [0.1,1.3], fixed before evaluation
        theta=np.deg2rad(self.angles)
        self.vectors=(self.radii[:,None,None]*np.stack([np.cos(theta),np.sin(theta)],axis=1)[None,:,:]).reshape(-1,2)
        self.delays=self.vectors@self.matrix.T

    def estimate(self, rows, corr):
        supported=[k for k,r in enumerate(rows) if r['bins']>=12]
        measured=[k for k,r in enumerate(rows) if r['valid']]
        if len(supported)<3 or len(measured)<3:
            return dict(valid=False,reason='INSUFFICIENT_MEASURED_PAIRS',angle=None)
        if np.linalg.matrix_rank(self.matrix[measured])<2:
            return dict(valid=False,reason='RANK_DEFICIENT',angle=None)
        score=np.zeros(len(self.vectors))
        for k in supported:
            lags=np.arange(-12,13)  # covers largest tested projection delay: 1.3 * 7.916
            score+=np.interp(self.delays[:,k],lags,corr[k,lags%1024])
        score/=len(supported)
        if not np.all(np.isfinite(score)):
            return dict(valid=False,reason='NONFINITE_SCORE',angle=None)
        winner=int(np.argmax(score));peak=float(score[winner])
        ties=int(np.count_nonzero(score==score[winner]))
        u=self.vectors[winner];angle=float(self.angles[winner%len(self.angles)])
        tau=np.array([rows[k]['tau_samples'] for k in measured])
        residual=float(np.sqrt(np.mean((self.matrix[measured]@u-tau)**2)))
        # This is NOT residual against grid-generated delays (which would be tautologically zero).
        valid=ties==1 and residual<=.5
        return dict(valid=bool(valid),reason='MEASURED_RESIDUAL_PASS' if valid else 'TIED_SCORE' if ties>1 else 'MEASURED_RESIDUAL_REJECT',
                    angle=angle if valid else None,research_angle=angle,radius=float(np.linalg.norm(u)),
                    measured_residual_samples=residual,joint_score=peak,exact_ties=ties,
                    scoring_pairs=supported,measured_pairs=measured)
