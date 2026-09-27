import unittest
import numpy as np
from tracked_audio import TrackedAudio,FixedDAS,FS

def event(start,u=(1.,0,0),state='LOCKED',expiry=2000):
    return dict(timestamp_ms=start/48,state=state,fresh_valid=state=='LOCKED',stale=state=='HOLD',
                direction=list(u) if state=='LOCKED' else None,display_direction=list(u) if state in ['LOCKED','HOLD'] else None,
                display_expires_at_ms=expiry/48)

class Tests(unittest.TestCase):
    def test_relative_tracker_clock_with_nonzero_sample_origin(self):
        x=np.random.default_rng(7).normal(size=(1400,6))
        a=TrackedAudio('single');expected,v,m=a.process(x,first_sample_id=0,tracking=event(0,expiry=700))
        b=TrackedAudio('single',sample_origin=1536);y,w,n=b.process(x,first_sample_id=1536,tracking=event(0,expiry=700))
        np.testing.assert_array_equal(y,expected);np.testing.assert_array_equal(n,m)
        self.assertEqual(b.events[-1]['sample_id'],2237)
    def test_fallback_is_delayed_single(self):
        x=np.random.default_rng(1).normal(size=(100,6));a=TrackedAudio('single');y,v,m=a.process(x,first_sample_id=0)
        np.testing.assert_array_equal(y[4:],x[:-4,0]);self.assertTrue(np.all(m=='FALLBACK'));self.assertEqual(sum(~v),8)

    def test_settled_beam_matches_fixed_das(self):
        x=np.random.default_rng(2).normal(size=(1500,6));a=TrackedAudio('single');y,_,_=a.process(x,first_sample_id=0,tracking=event(0))
        expected,_=FixedDAS([1,0,0]).process(x,first_sample_id=0)
        np.testing.assert_allclose(y[480:],expected[480:],rtol=0,atol=1e-15)

    def test_fade_matches_independent_blend(self):
        x=np.random.default_rng(3).normal(size=(512,6));y,_,_=TrackedAudio('single').process(x,first_sample_id=0,tracking=event(0))
        b,_=FixedDAS([1,0,0]).process(x,first_sample_id=0);single=np.zeros(len(x));single[4:]=x[:-4,0]
        alpha=np.minimum(np.arange(1,len(x)+1)/480,1)
        np.testing.assert_allclose(y,(1-alpha)*single+alpha*b,rtol=0,atol=1e-15)

    def test_expiry_inside_block_and_hold(self):
        x=np.ones((1600,6));a=TrackedAudio('single');a.process(x[:512],first_sample_id=0,tracking=event(0,expiry=700))
        y,_,mode=a.process(x[512:],first_sample_id=512,tracking=event(512,state='HOLD',expiry=700))
        self.assertTrue(np.all(mode[:189]=='HOLD'));self.assertTrue(np.all(mode[189:]=='FALLBACK'))
        self.assertEqual(a.events[-1]['sample_id'],701)
        np.testing.assert_allclose(y,1.,rtol=0,atol=1e-15)

    def test_split_blocks_preserve_fade_and_expiry(self):
        x=np.random.default_rng(6).normal(size=(1400,6));a=TrackedAudio('single');expected,v,m=a.process(x,first_sample_id=0,tracking=event(0,expiry=700))
        a=TrackedAudio('single');parts=[];masks=[];modes=[];start=0
        for size in [1,3,127,382,300,587]:
            y,b,c=a.process(x[start:start+size],first_sample_id=start,tracking=event(0,expiry=700) if start==0 else None)
            parts.append(y);masks.append(b);modes.append(c);start+=size
        np.testing.assert_array_equal(np.concatenate(parts),expected);np.testing.assert_array_equal(np.concatenate(masks),v);np.testing.assert_array_equal(np.concatenate(modes),m)

    def test_future_event_and_gap_leave_state_unchanged(self):
        a=TrackedAudio('single');x=np.ones((20,6));a.process(x,first_sample_id=0)
        with self.assertRaises(ValueError):a.process(x,first_sample_id=20,tracking=event(21))
        with self.assertRaises(ValueError):a.process(x,first_sample_id=21)
        self.assertEqual(a.next_id,20);self.assertEqual(a.events,[])
        with self.assertRaises(ValueError):a.process(x,first_sample_id=20,tracking=event(float('nan')))

    def test_reset_releases_beam(self):
        a=TrackedAudio('single');a.process(np.ones((512,6)),first_sample_id=0,tracking=event(0));a.reset()
        y,v,m=a.process(np.zeros((20,6)),first_sample_id=5000)
        self.assertFalse(np.any(y));self.assertEqual(sum(~v),8);self.assertTrue(np.all(m=='FALLBACK'))

    def test_new_event_never_changes_past_output(self):
        x=np.random.default_rng(3).normal(size=(1024,6));a=TrackedAudio('single');prefix,_,_=a.process(x[:512],first_sample_id=0);saved=prefix.copy()
        a.process(x[512:],first_sample_id=512,tracking=event(512))
        np.testing.assert_array_equal(prefix,saved)

    def test_direction_update_during_fade_starts_at_current_mix(self):
        x=np.random.default_rng(33).normal(size=(900,6));a=TrackedAudio('single')
        first,_,_=a.process(x[:200],first_sample_id=0,tracking=event(0))
        u=[np.cos(np.deg2rad(20)),np.sin(np.deg2rad(20)),0.]
        second,_,_=a.process(x[200:],first_sample_id=200,tracking=event(200,u=u))
        old,_=FixedDAS([1,0,0]).process(x,first_sample_id=0);new,_=FixedDAS(u).process(x,first_sample_id=0)
        single=np.zeros(len(x));single[4:]=x[:-4,0]
        current_mix=(1-200/480)*single+(200/480)*old
        alpha=np.minimum(np.arange(1,701)/480,1)
        expected=(1-alpha)*current_mix[200:]+alpha*new[200:]
        np.testing.assert_allclose(second,expected,rtol=0,atol=1e-15)

if __name__=='__main__':unittest.main(verbosity=2)
