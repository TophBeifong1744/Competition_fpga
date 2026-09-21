"""Bind interval table to original sources and trace selected actual AST nodes."""
import argparse
import ast
import hashlib
import importlib.util
import inspect
from itertools import combinations, product
import json
from pathlib import Path
import sys
import textwrap
import numpy as np
from derive_widths import derive, TABLE


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    derive()
    paths={
        'fixed':a.repo/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py',
        'phat':a.repo/'task-packages/PKG-B-ALG/tasks/phat-fixed-03/phat_model.py',
        'gate':a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/integer_gate.py'}
    fg=load('width_fg',paths['fixed']);ph=load('width_ph',paths['phat'])
    source_hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}
    # Fail if formulas change: reviewed domain derivation needs reinspection.
    assert source_hashes['fixed']=='f6bb2bc41dee3f1e2e6d93176972d92db12d687978fd3a95a47e85b28f88a74a'
    assert source_hashes['gate']=='c2f22ea3f6fb184a38d2f3802d89cd5487e202e44b4226075004460a4c7af1d8'
    assert source_hashes['phat']=='84eaa9691f62aba7164e3172aa94b2e361cb99672647477d98f8b3f3889f3144'
    assert fg._CORDIC_ATAN_Q16[0]==45*65536
    assert sum(fg._CORDIC_ATAN_Q16)<105*65536+24
    observed={};count=0
    names={'sxx':'doa.sxx','syy':'doa.syy','sxy':'doa.sxy','bx':'doa.bx_by','by':'doa.bx_by','determinant':'doa.det','ux':'doa.xy_pre_guard','uy':'doa.xy_pre_guard','predicted':'doa.predicted','residual_sq':'doa.residual_sum_square','norm_sq':'doa.norm_square'}
    def checked(name,value):
        nonlocal count
        if name in names:
            lo,hi=TABLE[names[name]];assert lo<=value<=hi,(name,value,lo,hi)
            old=observed.get(name,(value,value));observed[name]=min(old[0],value),max(old[1],value);count+=1
        return value
    class Trace(ast.NodeTransformer):
        def visit_Assign(self,node):
            self.generic_visit(node)
            if len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                node.value=ast.Call(func=ast.Name(id='checked',ctx=ast.Load()),args=[ast.Constant(node.targets[0].id),node.value],keywords=[])
            return node
        def visit_AugAssign(self,node):
            self.generic_visit(node)
            if isinstance(node.target,ast.Name):
                return [node,ast.Expr(ast.Call(func=ast.Name(id='checked',ctx=ast.Load()),args=[ast.Constant(node.target.id),ast.Name(id=node.target.id,ctx=ast.Load())],keywords=[]))]
            return node
    tree=ast.fix_missing_locations(Trace().visit(ast.parse(textwrap.dedent(inspect.getsource(fg.doa_q20)))))
    (a.out/'doa-traced.py').write_text(ast.unparse(tree),encoding='utf-8')
    env=dict(fg.__dict__);env['checked']=checked;exec(compile(tree,'original-doa-ast','exec'),env)
    cases=0
    for n in range(3,7):
        for ids in combinations(range(6),n):
            for signs in product((-1,1),repeat=n):
                rows=[dict(valid=False,tau_q12=0) for _ in range(6)]
                for i,sign in zip(ids,signs):rows[i]=dict(valid=True,tau_q12=sign*fg.physical_limit_q12(fg.PAIR_LENGTH_SQ[i]))
                assert env['doa_q20'](rows)==fg.doa_q20(rows)
                cases+=1
    # Reciprocal: each mantissa bin endpoints/midpoint across exponents,
    # plus original normalization calls at full-scale quadrant combinations.
    recip_cases=0
    for exponent in (24,30,50,74):
        for k in range(256):
            for m in (2**30+k*2**22,2**30+k*2**22+2**21,2**30+(k+1)*2**22-1):
                magnitude=m<<max(0,exponent-30) if exponent>=30 else ph.rne_shift(m,30-exponent)
                r,e=ph.reciprocal(magnitude)
                lo,hi=TABLE['phat.newton1.reciprocal'];assert lo<=r<=hi
                recip_cases+=1
    cordic_cases=0
    for x,y in product((-2531477,-1048576,-1,0,1,1048576,2531477),repeat=2):
        if not(x or y):continue
        # Trace original CORDIC assignments, not a replacement CORDIC model.
        local=[]
        def capture(frame,event,arg):
            if frame.f_code is fg.atan2_q8.__code__ and event=='line':
                for key in ('x','y'):
                    if key in frame.f_locals:
                        v=frame.f_locals[key];lo,hi=TABLE['cordic.xy_all_iterations'];assert lo<=v<=hi;local.append(v)
            return capture
        sys.settrace(capture)
        try:fg.atan2_q8(y,x)
        finally:sys.settrace(None)
        assert local;cordic_cases+=1
    result=dict(status='AUTHOR_BOUND_TRACE_PASS',source_sha256=source_hashes,doa_corners=cases,checked_assignments=count,observed=observed,reciprocal_cases=recip_cases,cordic_cases=cordic_cases,scope='trace consistency supplements analytic interval inclusion; not exhaustive IP or arithmetic equivalence')
    (a.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print({k:v for k,v in result.items() if k!='observed'})


if __name__=='__main__':main()
