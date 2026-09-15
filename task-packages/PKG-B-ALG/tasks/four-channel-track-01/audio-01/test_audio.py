"""Numerical/control tests; algebraic test signals are not acoustic performance data."""
import copy
from fractions import Fraction
import math
from pathlib import Path
import sys
import tempfile
import unittest
import wave

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from mixer import Crossfade, mix_timeline
from render_three import (HERE,PARENT,ROOT,load,verify_inputs,ReaderSession,adapt_h1,
                          prepare_events,render_clean,write_wav)


def event(ready,target=1,expiry=1000,fresh=True):
    return dict(ready=ready,target=target,valid_through=expiry if target else None,fresh=fresh)


def decode(path):
    with wave.open(str(path),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,3,48000)
        data=w.readframes(w.getnframes())
    return np.array([int.from_bytes(data[i:i+3],'little',signed=True) for i in range(0,len(data),3)],dtype=np.int64)


class FadeContract(unittest.TestCase):
    def test_no_event_is_exact_single(self):
        bank=np.array([np.arange(20),np.arange(20)+10.])
        y,w,_=mix_timeline(bank,0,20,[],4)
        np.testing.assert_array_equal(y,bank[0])
        np.testing.assert_array_equal(w[:,0],1)

    def test_no_retroactive_direction(self):
        bank=np.array([np.zeros(20),np.ones(20)])
        y,_,_=mix_timeline(bank,0,20,[event(10)],4)
        np.testing.assert_array_equal(y[:11],0)
        np.testing.assert_array_equal(y[10:15],[0,.25,.5,.75,1])

    def test_interrupted_crossfade_continuity(self):
        f=Crossfade(3,4)
        f.select(1,0,100)
        before=f.weights(2)
        f.select(2,2,100)
        np.testing.assert_array_equal(f.weights(2),before)
        np.testing.assert_array_equal(f.weights(6),[0,0,1])

    def test_expiry_without_any_new_event(self):
        f=Crossfade(2,4)
        f.select(1,0,10)
        np.testing.assert_array_equal([f.weights(n)[1] for n in range(7,12)],[1,.75,.5,.25,0])
        np.testing.assert_array_equal(f.weights(100),[1,0])

    def test_new_direction_does_not_extend_old_expiry(self):
        f=Crossfade(3,4)
        f.select(1,0,10)
        f.select(2,9,100)
        self.assertEqual(f.weights(11)[1],0)
        self.assertGreater(f.weights(11)[2],0)

    def test_change_direction_during_expiry_fade_is_continuous(self):
        f=Crossfade(3,4)
        f.select(1,0,10)
        before=f.weights(9)
        f.select(2,9,100)
        np.testing.assert_array_equal(f.weights(9),before)

    def test_release_during_expiry_fade_is_continuous(self):
        f=Crossfade(2,4)
        f.select(1,0,10)
        before=f.weights(9)
        f.select(0,9)
        np.testing.assert_array_equal(f.weights(9),before)

    def test_renewal_during_expiry_fade_has_no_jump(self):
        f=Crossfade(2,4)
        f.select(1,0,10)
        before=f.weights(9)
        f.select(1,9,100)
        np.testing.assert_array_equal(f.weights(9),before)
        np.testing.assert_array_equal(f.weights(13),[0,1])

    def test_hold_event_does_not_refresh_ttl(self):
        bank=np.array([np.zeros(30),np.ones(30)])
        _,w,_=mix_timeline(bank,0,30,[event(0,expiry=10),event(8,expiry=10,fresh=False)],4)
        self.assertEqual(w[11,1],0)

    def test_new_interval_cannot_retain_previous_mix(self):
        bank=np.array([np.zeros(20),np.ones(20)])
        mix_timeline(bank,0,20,[event(0)],4)
        y,_,_=mix_timeline(bank,0,20,[],4)
        np.testing.assert_array_equal(y,0)

    def test_convex_bound_under_rapid_switches(self):
        bank=np.array([np.full(40,-.5),np.full(40,.8),np.full(40,.2)])
        y,w,_=mix_timeline(bank,0,40,[event(0,1,14),event(2,2,20),event(5,0),event(9,1,17)],8)
        self.assertTrue(np.all(w>=0))
        np.testing.assert_allclose(w.sum(axis=1),1,atol=1e-15)
        self.assertTrue(np.all((y>=-.5)&(y<=.8)))

    def test_unordered_or_expired_events_fail(self):
        for events in ([event(2),event(1)],[event(3,expiry=1)]):
            with self.assertRaises(ValueError): mix_timeline(np.ones((2,10)),0,10,events,4)

    def test_integer_endpoint_rounding_and_saturation(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'codes.wav'
            values=np.array([-2.,-1.,-2.5/2**23,-1.5/2**23,.5/2**23,1.5/2**23,1.,2.])
            info=write_wav(p,values,48000)
            np.testing.assert_array_equal(decode(p),[-2**23,-2**23,-2,-2,0,2,2**23-1,2**23-1])
            self.assertEqual(info['saturation_samples'],3)


class RealAudioContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_inputs()
        cls.cfg=load(PARENT/'config.json');cls.audio=load(HERE/'config.json')
        cls.rec=ReaderSession().load(ROOT/cls.cfg['recordings'][0]['directory'])
        cls.x=adapt_h1(cls.rec).samples
        cls.frames=load(PARENT/'evidence/run01/replay/center-frames.json')
        cls.vectors,cls.events=prepare_events(cls.frames,cls.rec.sample_ids,0,len(cls.x),0,cls.cfg)
        cls.render=render_clean(cls.x,cls.vectors,cls.events,cls.cfg,cls.audio)

    def test_common_crop_and_availability(self):
        r=self.render
        self.assertEqual((r['start'],r['stop'],r['radius']),(8,31992,8))
        self.assertEqual(len(r['single']),31984)
        self.assertEqual(len(r['single']),len(r['manual']))
        self.assertEqual(len(r['single']),len(r['automatic']))
        for delay in r['delays'][1:]:
            # n-delay <= n+L and >= n-L for every interpolation tap.
            self.assertTrue(np.all(np.abs(delay)<=r['radius']))

    def test_original_single_and_approved_manual_crop(self):
        r=self.render
        np.testing.assert_array_equal(np.rint(r['single']*2**23),self.rec.samples[8:31992,0])
        old=ROOT/'task-packages/PKG-B-ALG/tasks/real-audio-compare-01/center-target-01/evidence/audio-run01/interval00-manual-raw.wav'
        np.testing.assert_array_equal(np.rint(r['manual']*2**23).astype(np.int64),decode(old)[2:31986])

    def test_frozen_tracker_sequence_replayed(self):
        self.assertEqual(len(self.events),61)
        self.assertEqual(sum(e['fresh'] for e in self.events),21)
        for frame,e in zip(self.frames,self.events):
            self.assertEqual(e['ready'],frame['row_stop'])
        lock=next(e for e in self.events if e['fresh'])
        self.assertEqual(lock['ready'],12288)
        np.testing.assert_array_equal(self.render['automatic'][:12288-8+1],self.render['single'][:12288-8+1])

    def test_future_audio_cannot_affect_emitted_prefix(self):
        changed=self.x.copy();changed[20000:]=0
        r=render_clean(changed,self.vectors,self.events,self.cfg,self.audio)
        # For reference n<19992, n+8<20000: no changed input tap is available.
        for label in ('single','manual','automatic'):
            np.testing.assert_array_equal(r[label][:19992-8],self.render[label][:19992-8])

    def test_gap_frame_crossing_rejected(self):
        with self.assertRaisesRegex(ValueError,'FRAME_CROSSES_INTERVAL'):
            prepare_events(self.frames,self.rec.sample_ids,0,1000,0,self.cfg)

    def test_frame_id_and_ready_binding(self):
        for key,value in [('last_sample_id','999'),('frame_ready_ms',0)]:
            f=copy.deepcopy(self.frames);f[0][key]=value
            with self.assertRaises(ValueError): prepare_events(f,self.rec.sample_ids,0,len(self.x),0,self.cfg)

    def test_rational_sample_golden(self):
        r=self.render
        # Exact rational summation of original integer PCM, binary64 delays and
        # mixer weights. Includes first acquisition, transitions and record tail.
        indices=sorted(set([8,100,12287,12288,12289,12528,12768,16000,20000,30000,31991]+
                          [e['ready']+17 for e in self.events if 8<=e['ready']+17<31992]))
        for n in indices:
            total=Fraction(0)
            for beam,weight in enumerate(r['weights'][n-8]):
                if weight==0: continue
                if beam==0: code=Fraction(int(self.rec.samples[n,0]))
                else:
                    code=Fraction(0)
                    for ch,d in enumerate(r['delays'][beam]):
                        source=Fraction(n)-Fraction.from_float(d)
                        left=source.numerator//source.denominator
                        w=source-left
                        code+=(1-w)*int(self.rec.samples[left,ch])+w*int(self.rec.samples[left+1,ch])
                    code/=4
                total+=Fraction.from_float(float(weight))*code
            self.assertEqual(int(np.rint(r['automatic'][n-8]*2**23)),round(total),n)

    def test_quiet_automatic_remains_bit_exact_single(self):
        rec=ReaderSession().load(ROOT/self.cfg['recordings'][1]['directory'])
        frames=load(PARENT/'evidence/run01/replay/quiet-frames.json')
        v,e=prepare_events(frames,rec.sample_ids,0,len(rec.samples),0,self.cfg)
        r=render_clean(adapt_h1(rec).samples,v,e,self.cfg,self.audio)
        np.testing.assert_array_equal(r['automatic'],r['single'])


if __name__=='__main__': unittest.main()
